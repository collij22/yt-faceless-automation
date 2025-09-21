"""n8n webhook and API client for workflow automation."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

try:
    import aiohttp
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from ..core.config import AppConfig
from ..core.errors import ConfigurationError, N8NWebhookError, RateLimitError, RetryableError
from ..core.schemas import (
    YouTubeUploadPayload,
    YouTubeUploadResponse,
    QualityScores,
    VerificationStatus,
    MetricsBaseline,
    AnalyticsRequest,
    EnhancedAnalyticsSnapshot,
    TimeWindow,
    KPIMetrics,
    RetentionPoint,
    TrafficSource,
    Geography,
    Anomaly,
    PerformancePredictions,
    EngagementAnalysis,
    MonetizationMetrics,
)

logger = logging.getLogger(__name__)


class N8NClient:
    """Client for interacting with n8n webhooks and API."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.webhooks = config.webhooks
        self.session = None
        self._rate_limiter = RateLimiter(
            requests_per_minute=config.performance.rate_limit_requests_per_minute,
            burst_size=config.performance.rate_limit_burst_size
        )
    
    def trigger_tts_webhook(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: Optional[str] = None,
        chunk_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Trigger TTS generation webhook.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID for TTS provider
            model: TTS model to use
            chunk_id: Unique ID for this chunk (for caching)
            **kwargs: Additional parameters for the webhook
        
        Returns:
            Webhook response with audio URL/path
        """
        payload = {
            "text": text,
            "voice_id": voice_id or self._get_default_voice_id(),
            "model": model or self._get_default_tts_model(),
            "chunk_id": chunk_id,
            "provider": self.config.tts.provider,
            **kwargs
        }
        
        # Add provider-specific parameters
        if self.config.tts.provider == "elevenlabs":
            payload.update({
                "api_key": self.config.tts.elevenlabs_api_key,
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.75,
                }
            })
        
        response = self._post_webhook(
            self.webhooks.tts_url,
            payload,
            timeout=60  # TTS can take time
        )
        
        # Validate response
        if not response.get("success"):
            raise N8NWebhookError(
                f"TTS webhook failed: {response.get('error', 'Unknown error')}"
            )
        
        return response
    
    def trigger_upload_webhook(
        self,
        video_path: str,
        metadata: Dict[str, Any],
        schedule_time: Optional[str] = None,
        privacy: str = "private",
        **kwargs
    ) -> Dict[str, Any]:
        """Trigger YouTube upload webhook.
        
        Args:
            video_path: Path to video file
            metadata: Video metadata (title, description, tags, etc.)
            schedule_time: ISO timestamp for scheduled publishing
            privacy: Privacy setting (private, unlisted, public)
            **kwargs: Additional upload parameters
        
        Returns:
            Webhook response with YouTube video ID
        """
        payload = {
            "video_path": video_path,
            "metadata": metadata,
            "schedule_time": schedule_time,
            "privacy": privacy,
            "notify_subscribers": kwargs.get("notify_subscribers", True),
            "auto_chapters": self.config.features.get("auto_chapters", True),
            "auto_captions": self.config.features.get("auto_subtitles", True),
            **kwargs
        }
        
        response = self._post_webhook(
            self.webhooks.upload_url,
            payload,
            timeout=300  # Upload can take several minutes
        )
        
        if not response.get("success"):
            raise N8NWebhookError(
                f"Upload webhook failed: {response.get('error', 'Unknown error')}"
            )
        
        return response
    
    def trigger_asset_webhook(
        self,
        asset_urls: List[str],
        destination_dir: str,
        parallel: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Trigger asset download webhook.
        
        Args:
            asset_urls: List of URLs to download
            destination_dir: Directory to save assets
            parallel: Whether to download in parallel
            **kwargs: Additional download parameters
        
        Returns:
            Webhook response with download results
        """
        if not self.webhooks.asset_url:
            raise ConfigurationError("Asset webhook URL not configured")
        
        payload = {
            "urls": asset_urls,
            "destination": destination_dir,
            "parallel": parallel,
            "max_concurrent": self.config.performance.max_concurrent_downloads,
            **kwargs
        }
        
        response = self._post_webhook(
            self.webhooks.asset_url,
            payload,
            timeout=120
        )
        
        return response
    
    def trigger_error_webhook(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        severity: str = "error",
        **kwargs
    ) -> None:
        """Trigger error notification webhook.

        Args:
            error_type: Type of error
            error_message: Error message
            context: Error context and details
            severity: Error severity (info, warning, error, critical)
            **kwargs: Additional error details
        """
        if not self.webhooks.error_url:
            logger.warning("Error webhook not configured, skipping notification")
            return

        payload = {
            "error_type": error_type,
            "message": error_message,
            "context": context,
            "severity": severity,
            "timestamp": time.time(),
            **kwargs
        }

        try:
            self._post_webhook(
                self.webhooks.error_url,
                payload,
                timeout=10,
                raise_on_error=False
            )
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")

    async def execute_webhook(self, url: str, payload: dict, timeout: int = 30) -> dict:
        """Execute a generic webhook asynchronously.

        Args:
            url: Webhook URL
            payload: Request payload
            timeout: Request timeout in seconds

        Returns:
            Response data from webhook
        """
        import aiohttp

        if not hasattr(self, 'session') or self.session is None:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(url, json=payload, timeout=timeout) as resp:
                resp.raise_for_status()
                return await resp.json()
        except Exception as e:
            logger.error(f"Webhook execution failed: {e}")
            raise

    # Phase 6: Typed Upload Methods

    def upload_video(self, payload: YouTubeUploadPayload) -> YouTubeUploadResponse:
        """Upload video with typed payload and response.

        Args:
            payload: Typed upload payload with all metadata

        Returns:
            Typed upload response with verification status
        """
        # Convert payload to dict for webhook
        upload_data = {
            "video_path": payload.video_path,
            "thumbnail_path": payload.thumbnail_path,
            "title": payload.title,
            "description": payload.description,
            "tags": payload.tags,
            "category_id": payload.category_id,
            "privacy_status": payload.privacy_status,
            "publish_at_iso": payload.publish_at_iso,
            "made_for_kids": payload.made_for_kids,
            "language": payload.language,
            "chapters": [{"start": c.start, "title": c.title} for c in (payload.chapters or [])],
            "slug": payload.slug,
            "checksum_sha256": payload.checksum_sha256,
            "transaction_id": payload.transaction_id,
        }

        # Add optional enhanced fields
        if payload.quality_gates:
            upload_data["quality_gates"] = payload.quality_gates.model_dump()
        if payload.monetization_settings:
            upload_data["monetization_settings"] = payload.monetization_settings.model_dump()
        if payload.audience_retention_hooks:
            upload_data["retention_hooks"] = [h.model_dump() for h in payload.audience_retention_hooks]

        upload_data["platform_targets"] = payload.platform_targets
        upload_data["upload_priority"] = payload.upload_priority
        upload_data["parent_video_id"] = payload.parent_video_id
        upload_data["experiment_id"] = payload.experiment_id

        # Log with masked secrets
        logger.info(f"Uploading video for slug: {payload.slug}, transaction: {payload.transaction_id}")

        # Call webhook with retries
        start_time = time.time()
        response = self._post_webhook(
            self.webhooks.upload_url,
            upload_data,
            timeout=300  # 5 minutes for upload
        )

        upload_duration_ms = int((time.time() - start_time) * 1000)

        # Parse response into typed object
        return YouTubeUploadResponse(
            execution_id=response.get("execution_id", ""),
            video_id=response.get("video_id", ""),
            status=response.get("status", "failed"),
            publish_at_iso=response.get("publish_at_iso"),
            errors=response.get("errors"),
            transaction_id=payload.transaction_id,
            upload_duration_ms=upload_duration_ms,
            quality_scores=QualityScores(**response["quality_scores"]) if "quality_scores" in response else None,
            platform_ids=response.get("platform_ids", {}),
            verification_status=VerificationStatus(**response["verification_status"]) if "verification_status" in response else None,
            rollback_available_until_iso=response.get("rollback_available_until_iso"),
            metrics_baseline=MetricsBaseline(**response["metrics_baseline"]) if "metrics_baseline" in response else None,
        )

    def check_video_status(self, video_id: str) -> Dict[str, Any]:
        """Check video processing status.

        Args:
            video_id: YouTube video ID

        Returns:
            Status information
        """
        if not self.config.apis.n8n_api_url:
            # Fallback to webhook if API not configured
            payload = {"video_id": video_id, "action": "check_status"}
            return self._post_webhook(self.webhooks.upload_url, payload, timeout=30)

        return self.call_n8n_api(f"/youtube/video/{video_id}/status")

    def update_video_metadata(
        self,
        video_id: str,
        metadata: Dict[str, Any],
        variant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update video metadata (for experiments).

        Args:
            video_id: YouTube video ID
            metadata: Metadata to update
            variant_id: Experiment variant ID

        Returns:
            Update response
        """
        payload = {
            "video_id": video_id,
            "metadata": metadata,
            "variant_id": variant_id,
            "action": "update_metadata"
        }

        return self._post_webhook(self.webhooks.upload_url, payload, timeout=60)

    def clear_experiment(self, video_id: str) -> Dict[str, Any]:
        """Clear experiment flags from video.

        Args:
            video_id: YouTube video ID

        Returns:
            Clear response
        """
        return self.update_video_metadata(video_id, {"experiment_active": False})

    # Phase 7: Analytics Methods

    def fetch_analytics(self, request: AnalyticsRequest) -> EnhancedAnalyticsSnapshot:
        """Fetch analytics with typed request and response.

        Args:
            request: Typed analytics request

        Returns:
            Enhanced analytics snapshot with predictions
        """
        # Check for analytics webhook URL
        analytics_url = self.webhooks.analytics_url
        if not analytics_url:
            raise ConfigurationError("Analytics webhook URL not configured")

        # Build request payload
        analytics_data = {
            "video_id": request.video_id,
            "lookback_days": request.lookback_days,
            "granularity": request.granularity,
            "metrics": request.metrics or ["views", "ctr", "retention", "revenue"],
            "dimensions": request.dimensions,
            "filters": request.filters,
            "compare_to": request.compare_to,
            "include_predictions": request.include_predictions,
            "include_anomalies": request.include_anomalies,
        }

        logger.info(f"Fetching analytics for video: {request.video_id}, lookback: {request.lookback_days} days")

        # Call webhook
        response = self._post_webhook(analytics_url, analytics_data, timeout=120)

        # Parse into typed response
        snapshot = EnhancedAnalyticsSnapshot(
            video_id=response["video_id"],
            time_window=TimeWindow(**response["time_window"]),
            kpis=KPIMetrics(**response["kpis"]),
            retention_curve=[RetentionPoint(**p) for p in response["retention_curve"]],
            traffic_sources=[TrafficSource(**s) for s in response["traffic_sources"]],
            top_geographies=[Geography(**g) for g in response["top_geographies"]],
            performance_score=response.get("performance_score", 50.0),
        )

        # Add optional enhanced fields
        if "anomalies" in response and response["anomalies"]:
            snapshot.anomalies = [Anomaly(**a) for a in response["anomalies"]]

        if "predictions" in response and response["predictions"]:
            snapshot.predictions = PerformancePredictions(**response["predictions"])

        if "engagement_patterns" in response:
            snapshot.engagement_patterns = EngagementAnalysis(**response["engagement_patterns"])

        if "monetization_metrics" in response:
            snapshot.monetization_metrics = MonetizationMetrics(**response["monetization_metrics"])

        if "comparative_analysis" in response:
            snapshot.comparative_analysis = response["comparative_analysis"]

        # Persist raw analytics
        self._save_analytics_snapshot(request.video_id, response)

        return snapshot

    def fetch_variant_metrics(
        self,
        video_id: str,
        variant_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch metrics for experiment variants.

        Args:
            video_id: YouTube video ID
            variant_ids: List of variant IDs

        Returns:
            Metrics by variant ID
        """
        analytics_url = self.webhooks.analytics_url
        if not analytics_url:
            raise ConfigurationError("Analytics webhook URL not configured")

        payload = {
            "video_id": video_id,
            "variant_ids": variant_ids,
            "action": "fetch_variant_metrics"
        }

        return self._post_webhook(analytics_url, payload, timeout=60)

    def apply_metadata_update(
        self,
        video_id: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply metadata update (for optimization).

        Args:
            video_id: YouTube video ID
            fields: Fields to update

        Returns:
            Update response
        """
        return self.update_video_metadata(video_id, fields)

    def _save_analytics_snapshot(
        self,
        video_id: str,
        snapshot_data: Dict[str, Any]
    ) -> None:
        """Save raw analytics snapshot to disk.

        Args:
            video_id: Video ID
            snapshot_data: Raw analytics data
        """
        analytics_dir = self.config.directories.data_dir / "analytics" / video_id
        analytics_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        snapshot_file = analytics_dir / f"{timestamp}.json"

        with open(snapshot_file, "w") as f:
            json.dump(snapshot_data, f, indent=2, default=str)

        logger.debug(f"Saved analytics snapshot to {snapshot_file}")

    def send_error_notification(self, alert: Any) -> None:
        """Send error notification for alerts.

        Args:
            alert: Alert object
        """
        self.trigger_error_webhook(
            error_type=getattr(alert, "type", "unknown"),
            error_message=getattr(alert, "message", "Unknown alert"),
            context=getattr(alert, "data", {}),
            severity=getattr(alert, "severity", "error")
        )
    
    async def trigger_tts_webhook_async(
        self,
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Async version of TTS webhook trigger with robust success mapping.

        Accepts either {"success": true, "audio_path": ...} or
        {"status": "success", "output": {"files": [path, ...]}} structures.
        """
        import aiohttp
        import os
        from pathlib import Path as _P

        payload = {
            "text": text,
            "voice_id": kwargs.get("voice_id") or self._get_default_voice_id(),
            "model": kwargs.get("model") or self._get_default_tts_model(),
            **kwargs
        }

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhooks.tts_url, json=payload, timeout=timeout) as resp:
                resp.raise_for_status()
                data = await resp.json()

        # Normalize success detection
        ok = bool(data.get("success")) or str(data.get("status", "")).lower() in ("ok", "success")

        # Normalize audio path/url extraction
        def _first_nonempty(value):
            if isinstance(value, list):
                for v in value:
                    if v:
                        return v
            return value if value else None

        audio_path = data.get("audio_path")
        if not audio_path:
            # Look for common keys in nested output
            output = data.get("output") or {}
            files = output.get("files") or []
            file_single = output.get("file")
            url_candidates = [
                data.get("audio_url"),
                data.get("url"),
                output.get("audio_url"),
                output.get("url"),
            ]
            candidate = _first_nonempty(files) or file_single or _first_nonempty(url_candidates)
            if candidate:
                audio_path = str(candidate)
                data["audio_path"] = audio_path

        # If we got a URL (http/https), download it to cache and return a local path
        if audio_path and isinstance(audio_path, str) and audio_path.lower().startswith(("http://", "https://")):
            cache_dir = self.config.directories.cache_dir / "tts_webhook"
            cache_dir.mkdir(parents=True, exist_ok=True)
            # Derive filename from chunk_id or hash of URL
            chunk_id = payload.get("chunk_id") or str(int(time.time()*1000))
            # Try to preserve extension from URL
            ext = os.path.splitext(audio_path.split("?")[0])[1] or ".wav"
            dl_path = cache_dir / f"{chunk_id}{ext}"
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_path, timeout=timeout) as r2:
                    r2.raise_for_status()
                    with open(dl_path, "wb") as f:
                        f.write(await r2.read())
            data["audio_path"] = str(dl_path)
            audio_path = str(dl_path)

        if not ok or not audio_path:
            # Provide clearer error for upstream fallback
            err_msg = data.get("error") or "No audio_path returned by webhook"
            raise N8NWebhookError(f"Async TTS failed: {err_msg}")

        return data
    
    async def batch_tts_generation(
        self,
        text_chunks: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Generate TTS for multiple text chunks in parallel.
        
        Args:
            text_chunks: List of text chunks to process
            **kwargs: Parameters for TTS generation
        
        Returns:
            List of TTS responses
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Limit concurrent requests
        semaphore = asyncio.Semaphore(self.config.performance.max_concurrent_tts_chunks)
        
        async def process_chunk(chunk: str, index: int) -> Dict[str, Any]:
            async with semaphore:
                result = await self.trigger_tts_webhook_async(
                    chunk,
                    chunk_id=f"chunk_{index}",
                    **kwargs
                )
                result["chunk_index"] = index
                return result
        
        tasks = [
            process_chunk(chunk, i)
            for i, chunk in enumerate(text_chunks)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to process chunk {i}: {result}")
                # Retry logic could go here
                processed_results.append({
                    "success": False,
                    "chunk_index": i,
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def call_n8n_api(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call n8n API directly (not webhook).
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            data: Request data
            **kwargs: Additional request parameters
        
        Returns:
            API response
        """
        if not self.config.apis.n8n_api_url or not self.config.apis.n8n_api_key:
            raise ConfigurationError("n8n API URL and key required for API calls")
        
        url = urljoin(self.config.apis.n8n_api_url, endpoint)
        headers = {
            "X-N8N-API-KEY": self.config.apis.n8n_api_key,
            "Content-Type": "application/json",
        }
        
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required for n8n API calls")
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            timeout=kwargs.get("timeout", 30),
        )
        
        if response.status_code == 429:
            raise RateLimitError(
                "n8n API rate limit exceeded",
                retry_after=int(response.headers.get("Retry-After", 60))
            )
        
        response.raise_for_status()
        return response.json()
    
    def _post_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        timeout: int = 30,
        raise_on_error: bool = True
    ) -> Dict[str, Any]:
        """Post data to webhook with retry logic.
        
        Args:
            url: Webhook URL
            payload: Data to send
            timeout: Request timeout in seconds
            raise_on_error: Whether to raise exceptions
        
        Returns:
            Webhook response
        """
        # Apply rate limiting
        self._rate_limiter.acquire()
        
        if not REQUESTS_AVAILABLE:
            # Fallback to urllib if requests not available
            import urllib.request
            import urllib.error
            
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            
            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if raise_on_error:
                    raise N8NWebhookError(f"Webhook failed: {e.code} {e.reason}")
                return {"success": False, "error": str(e)}
        
        # Use requests with retry logic
        max_attempts = self.config.performance.max_retry_attempts
        backoff_base = self.config.performance.retry_backoff_base
        
        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=timeout
                )
                
                if response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < max_attempts - 1:
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        time.sleep(retry_after)
                        continue
                    raise RateLimitError("Webhook rate limit exceeded", retry_after)
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt < max_attempts - 1:
                    wait_time = backoff_base ** attempt
                    logger.warning(f"Webhook timeout, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                if raise_on_error:
                    raise N8NWebhookError(f"Webhook timeout after {max_attempts} attempts")
                return {"success": False, "error": "Timeout"}
                
            except requests.exceptions.RequestException as e:
                if attempt < max_attempts - 1 and self._is_retryable(e):
                    wait_time = backoff_base ** attempt
                    logger.warning(f"Webhook error: {e}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                if raise_on_error:
                    raise N8NWebhookError(f"Webhook failed: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}
    
    def _is_retryable(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        retryable_errors = [
            "ConnectionError",
            "Timeout",
            "ProxyError",
            "SSLError",
        ]
        
        error_type = type(error).__name__
        return any(err in error_type for err in retryable_errors)
    
    def _get_default_voice_id(self) -> str:
        """Get default voice ID based on TTS provider."""
        if self.config.tts.provider == "elevenlabs":
            return self.config.tts.elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"
        elif self.config.tts.provider == "playht":
            return self.config.tts.playht_voice_id or "larry"
        else:
            return "default"
    
    def _get_default_tts_model(self) -> str:
        """Get default TTS model based on provider."""
        if self.config.tts.provider == "elevenlabs":
            return self.config.tts.elevenlabs_model
        elif self.config.tts.provider == "playht":
            return "PlayHT2.0"
        else:
            return "standard"
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, requests_per_minute: int, burst_size: int):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.interval = 60.0 / requests_per_minute
    
    def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, blocking if necessary."""
        while tokens > self.tokens:
            self._refill()
            if tokens > self.tokens:
                sleep_time = (tokens - self.tokens) * self.interval
                time.sleep(sleep_time)
                self._refill()
        
        self.tokens -= tokens
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        
        tokens_to_add = elapsed / self.interval
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_update = now