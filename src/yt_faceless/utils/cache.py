"""Caching utilities for API responses and data."""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from ..core.config import AppConfig
from ..core.errors import CacheError

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for various data types."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.cache_dir = config.directories.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite cache for structured data
        self.db_path = self.cache_dir / "cache.db"
        self._init_db()
        
        # Memory cache for frequently accessed items
        self._memory_cache: Dict[str, tuple[Any, float]] = {}
        self._memory_cache_size = 0
        self._max_memory_size = 100 * 1024 * 1024  # 100MB
    
    def _init_db(self) -> None:
        """Initialize SQLite database for caching."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at REAL,
                    expires_at REAL,
                    hit_count INTEGER DEFAULT 0,
                    size_bytes INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires 
                ON cache(expires_at)
            """)
    
    def get(
        self,
        key: str,
        default: Any = None,
        use_memory: bool = True
    ) -> Any:
        """Get cached value by key.
        
        Args:
            key: Cache key
            default: Default value if not found
            use_memory: Whether to check memory cache first
        
        Returns:
            Cached value or default
        """
        # Check memory cache first
        if use_memory and key in self._memory_cache:
            value, expires_at = self._memory_cache[key]
            if expires_at > time.time():
                logger.debug(f"Memory cache hit for {key}")
                return value
            else:
                # Expired, remove from memory
                del self._memory_cache[key]
        
        # Check disk cache
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT value, expires_at FROM cache 
                    WHERE key = ? AND expires_at > ?
                    """,
                    (key, time.time())
                )
                row = cursor.fetchone()
                
                if row:
                    value_blob, expires_at = row
                    value = pickle.loads(value_blob)
                    
                    # Update hit count
                    conn.execute(
                        "UPDATE cache SET hit_count = hit_count + 1 WHERE key = ?",
                        (key,)
                    )
                    
                    # Add to memory cache if small enough
                    if use_memory and len(value_blob) < 1024 * 1024:  # < 1MB
                        self._memory_cache[key] = (value, expires_at)
                    
                    logger.debug(f"Disk cache hit for {key}")
                    return value
        
        except Exception as e:
            logger.error(f"Cache read error for {key}: {e}")
        
        return default
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        use_memory: bool = True
    ) -> None:
        """Set cached value.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (None for config default)
            use_memory: Whether to also cache in memory
        """
        if ttl_seconds is None:
            ttl_seconds = self.config.performance.cache_ttl_hours * 3600
        
        expires_at = time.time() + ttl_seconds
        value_blob = pickle.dumps(value)
        size_bytes = len(value_blob)
        
        # Check size limit
        max_size = self.config.performance.cache_max_size_mb * 1024 * 1024
        if size_bytes > max_size:
            logger.warning(f"Value too large to cache: {size_bytes} bytes")
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache 
                    (key, value, created_at, expires_at, size_bytes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (key, value_blob, time.time(), expires_at, size_bytes)
                )
            
            # Add to memory cache if small enough
            if use_memory and size_bytes < 1024 * 1024:  # < 1MB
                self._memory_cache[key] = (value, expires_at)
                self._memory_cache_size += size_bytes
                self._evict_memory_cache()
            
            logger.debug(f"Cached {key} ({size_bytes} bytes, TTL: {ttl_seconds}s)")
            
        except Exception as e:
            logger.error(f"Cache write error for {key}: {e}")
            raise CacheError(f"Failed to cache value: {e}")
    
    def delete(self, key: str) -> bool:
        """Delete cached value.
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted, False if not found
        """
        # Remove from memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]
        
        # Remove from disk cache
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM cache WHERE key = ?",
                    (key,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    def clear(self, expired_only: bool = False) -> int:
        """Clear cache.
        
        Args:
            expired_only: Only clear expired entries
        
        Returns:
            Number of entries cleared
        """
        # Clear memory cache
        if not expired_only:
            self._memory_cache.clear()
            self._memory_cache_size = 0
        else:
            current_time = time.time()
            expired_keys = [
                k for k, (_, exp) in self._memory_cache.items()
                if exp <= current_time
            ]
            for key in expired_keys:
                del self._memory_cache[key]
        
        # Clear disk cache
        try:
            with sqlite3.connect(self.db_path) as conn:
                if expired_only:
                    cursor = conn.execute(
                        "DELETE FROM cache WHERE expires_at <= ?",
                        (time.time(),)
                    )
                else:
                    cursor = conn.execute("DELETE FROM cache")
                
                count = cursor.rowcount
                logger.info(f"Cleared {count} cache entries")
                return count
        
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        stats = {
            "memory_cache_size": len(self._memory_cache),
            "memory_cache_bytes": self._memory_cache_size,
            "disk_cache_size": 0,
            "disk_cache_bytes": 0,
            "total_hits": 0,
            "expired_count": 0,
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total entries
                cursor = conn.execute("SELECT COUNT(*) FROM cache")
                stats["disk_cache_size"] = cursor.fetchone()[0]
                
                # Total size
                cursor = conn.execute("SELECT SUM(size_bytes) FROM cache")
                stats["disk_cache_bytes"] = cursor.fetchone()[0] or 0
                
                # Total hits
                cursor = conn.execute("SELECT SUM(hit_count) FROM cache")
                stats["total_hits"] = cursor.fetchone()[0] or 0
                
                # Expired entries
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM cache WHERE expires_at <= ?",
                    (time.time(),)
                )
                stats["expired_count"] = cursor.fetchone()[0]
        
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
        
        return stats
    
    def _evict_memory_cache(self) -> None:
        """Evict items from memory cache if size limit exceeded."""
        if self._memory_cache_size <= self._max_memory_size:
            return
        
        # Sort by expiration time and evict oldest
        sorted_items = sorted(
            self._memory_cache.items(),
            key=lambda x: x[1][1]  # Sort by expires_at
        )
        
        while self._memory_cache_size > self._max_memory_size * 0.8:  # Keep 80% full
            if not sorted_items:
                break
            
            key, (value, _) = sorted_items.pop(0)
            del self._memory_cache[key]
            # Estimate size reduction (rough)
            self._memory_cache_size -= len(pickle.dumps(value))
    
    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        key_data = {
            "args": args,
            "kwargs": kwargs,
        }

        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get_cached_audio(self, key: str) -> Optional[Path]:
        """Get cached audio file path.

        Args:
            key: Cache key for audio file

        Returns:
            Path to cached audio file if exists, None otherwise
        """
        audio_cache_dir = self.cache_dir / "tts_audio"
        audio_cache_dir.mkdir(parents=True, exist_ok=True)

        cached_path = audio_cache_dir / f"{key}.wav"
        if cached_path.exists():
            logger.debug(f"Audio cache hit for {key}")
            return cached_path

        return None

    def cache_audio(self, key: str, source_path: Path) -> None:
        """Cache audio file.

        Args:
            key: Cache key for audio file
            source_path: Path to source audio file to cache
        """
        if not source_path.exists():
            logger.error(f"Source audio file does not exist: {source_path}")
            return

        audio_cache_dir = self.cache_dir / "tts_audio"
        audio_cache_dir.mkdir(parents=True, exist_ok=True)

        cached_path = audio_cache_dir / f"{key}.wav"

        try:
            # Copy file to cache
            import shutil
            shutil.copy2(source_path, cached_path)
            logger.debug(f"Cached audio file {key} ({source_path.stat().st_size} bytes)")
        except Exception as e:
            logger.error(f"Failed to cache audio file: {e}")
            raise CacheError(f"Failed to cache audio file: {e}")


def cached(
    ttl_seconds: Optional[int] = 3600,
    key_prefix: Optional[str] = None,
    cache_manager: Optional[CacheManager] = None
) -> Callable:
    """Decorator for caching function results.
    
    Args:
        ttl_seconds: Cache TTL in seconds
        key_prefix: Prefix for cache keys
        cache_manager: CacheManager instance (created if None)
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Get or create cache manager
            nonlocal cache_manager
            if cache_manager is None:
                # This would need to be initialized with config
                logger.warning("No cache manager provided, caching disabled")
                return func(*args, **kwargs)
            
            # Generate cache key
            func_name = func.__name__
            if key_prefix:
                func_name = f"{key_prefix}:{func_name}"
            
            cache_key = f"{func_name}:{cache_manager.cache_key(*args, **kwargs)}"
            
            # Check cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func_name}")
                return cached_result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


class FileCache:
    """Simple file-based cache for large objects."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Use first 2 chars as subdirectory for better file system performance
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        subdir = self.cache_dir / key_hash[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{key_hash}.cache"
    
    def exists(self, key: str) -> bool:
        """Check if cached file exists."""
        return self.get_path(key).exists()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached object from file."""
        path = self.get_path(key)
        
        if not path.exists():
            return None
        
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache file {path}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """Save object to cache file."""
        path = self.get_path(key)
        
        try:
            with open(path, "wb") as f:
                pickle.dump(value, f)
            return True
        except Exception as e:
            logger.error(f"Failed to save cache file {path}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cached file."""
        path = self.get_path(key)
        
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as e:
                logger.error(f"Failed to delete cache file {path}: {e}")
        
        return False
    
    def clear(self) -> int:
        """Clear all cached files."""
        count = 0
        
        for cache_file in self.cache_dir.rglob("*.cache"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.error(f"Failed to delete {cache_file}: {e}")
        
        return count