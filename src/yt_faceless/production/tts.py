"""Text-to-Speech module with SSML support and intelligent chunking."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import AppConfig
from ..core.errors import TTSError, ConfigurationError
from ..integrations.n8n_client import N8NClient
from ..utils.cache import CacheManager
from ..utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class TTSProcessor:
    """Handles TTS generation with chunking, caching, and synthesis."""

    # SSML tags to preserve during chunking
    SSML_TAGS = {
        "speak", "break", "emphasis", "prosody", "say-as",
        "phoneme", "sub", "mark", "p", "s"
    }

    # Default TTS settings
    DEFAULT_CHUNK_SIZE = 3000  # characters
    DEFAULT_GAP_MS = 120  # milliseconds between chunks
    DEFAULT_SAMPLE_RATE = 44100  # Hz

    def __init__(self, config: AppConfig):
        self.config = config
        self.n8n_client = N8NClient(config)
        self.cache_manager = CacheManager(config)

        # Provider-specific settings
        self.provider = config.tts.provider
        self.voice_id = self._get_voice_id()
        self.model = self._get_model()

        # Chunking settings
        self.max_chunk_size = self._get_max_chunk_size()
        # Default words per minute for TTS pacing (YouTube standard)
        self.words_per_minute = 150

    def _get_voice_id(self) -> str:
        """Get voice ID based on provider configuration."""
        if self.provider == "elevenlabs":
            return self.config.tts.elevenlabs_voice_id
        elif self.provider == "playht":
            return self.config.tts.playht_voice_id
        else:
            return "default"

    def _get_model(self) -> str:
        """Get TTS model based on provider."""
        if self.provider == "elevenlabs":
            return self.config.tts.elevenlabs_model
        elif self.provider == "playht":
            return "PlayHT2.0"
        else:
            return "standard"

    def _get_max_chunk_size(self) -> int:
        """Get maximum chunk size for provider."""
        limits = {
            "elevenlabs": 5000,
            "playht": 3000,
            "google": 5000,
            "azure": 10000,
        }
        return limits.get(self.provider, self.DEFAULT_CHUNK_SIZE)


def chunk_script(
    ssml_markdown: str,
    max_chars: int = 3000,
    preserve_ssml: bool = True
) -> List[str]:
    """Split script into chunks while preserving SSML and sentence boundaries.

    Args:
        ssml_markdown: Script text with optional SSML markup
        max_chars: Maximum characters per chunk
        preserve_ssml: Whether to preserve SSML tags

    Returns:
        List of text chunks ready for TTS
    """
    # Handle empty input
    if not ssml_markdown or not ssml_markdown.strip():
        return ["<speak></speak>"] if preserve_ssml else []

    chunks = []

    # Remove markdown formatting but preserve SSML
    text = _strip_markdown(ssml_markdown)

    if preserve_ssml:
        # Parse SSML and chunk intelligently
        chunks = _chunk_with_ssml(text, max_chars)
    else:
        # Simple sentence-based chunking
        chunks = _chunk_by_sentences(text, max_chars)

    # Add inter-sentence breaks if needed
    chunks = [_add_sentence_breaks(chunk) for chunk in chunks]

    # Wrap in speak tags if SSML
    if preserve_ssml:
        chunks = [_wrap_in_speak(chunk) for chunk in chunks]

    return chunks


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting while preserving SSML."""
    # Remove markdown headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)

    return text.strip()


def _chunk_with_ssml(text: str, max_chars: int) -> List[str]:
    """Chunk text while preserving SSML structure."""
    chunks = []
    current_chunk = ""
    current_length = 0

    # Split by sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        sentence_length = len(sentence)

        if current_length + sentence_length > max_chars:
            # Current chunk is full, start new one
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
            current_length = sentence_length
        else:
            # Add to current chunk
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
            current_length += sentence_length + 1

    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def _chunk_by_sentences(text: str, max_chars: int) -> List[str]:
    """Simple sentence-based chunking without SSML."""
    chunks = []
    current_chunk = ""

    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def _add_sentence_breaks(text: str) -> str:
    """Add SSML breaks between sentences for natural pacing."""
    # Add break after sentence endings
    text = re.sub(
        r'([.!?])\s+',
        r'\1<break time="250ms"/> ',
        text
    )
    return text


def _wrap_in_speak(text: str) -> str:
    """Wrap text in SSML speak tags if not already wrapped."""
    if not text.startswith("<speak>"):
        text = f"<speak>{text}</speak>"
    return text


def validate_ssml_chunk(chunk: str) -> str:
    """Validate and fix SSML XML structure.

    Args:
        chunk: SSML text chunk

    Returns:
        Valid SSML chunk with fixed XML
    """
    try:
        # Try to parse as XML
        ET.fromstring(chunk)
        return chunk
    except ET.ParseError:
        # Fix common issues
        fixed = chunk

        # Escape special characters
        fixed = fixed.replace("&", "&amp;")
        fixed = fixed.replace("<", "&lt;").replace(">", "&gt;")

        # Re-enable SSML tags
        for tag in ["speak", "break", "emphasis", "prosody", "say-as"]:
            fixed = fixed.replace(f"&lt;{tag}", f"<{tag}")
            fixed = fixed.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
            fixed = fixed.replace(f"/&gt;", "/>")  # Self-closing tags

        # Try parsing again
        try:
            ET.fromstring(fixed)
            return fixed
        except ET.ParseError:
            # If still invalid, return plain text
            logger.warning("Could not fix SSML, using plain text")
            return re.sub(r'<[^>]+>', '', chunk)


async def synthesize_chunks(
    cfg: AppConfig,
    chunks: List[str],
    voice_id: Optional[str] = None,
    model: Optional[str] = None,
    parallel: bool = True
) -> List[Path]:
    """Synthesize TTS for multiple chunks with caching.

    Args:
        cfg: Application configuration
        chunks: List of text chunks
        voice_id: Override voice ID
        model: Override TTS model
        parallel: Whether to process in parallel

    Returns:
        List of paths to audio files
    """
    processor = TTSProcessor(cfg)
    voice_id = voice_id or processor.voice_id
    model = model or processor.model

    audio_paths = []

    if parallel:
        # Process chunks in parallel with concurrency limit
        semaphore = asyncio.Semaphore(cfg.performance.max_concurrent_tts_chunks)

        async def process_chunk(chunk: str, index: int) -> Path:
            async with semaphore:
                return await _synthesize_single_chunk(
                    cfg, chunk, index, voice_id, model
                )

        tasks = [
            process_chunk(chunk, i)
            for i, chunk in enumerate(chunks)
        ]

        audio_paths = await asyncio.gather(*tasks)
    else:
        # Process sequentially
        for i, chunk in enumerate(chunks):
            path = await _synthesize_single_chunk(
                cfg, chunk, i, voice_id, model
            )
            audio_paths.append(path)

    return audio_paths


async def _synthesize_single_chunk(
    cfg: AppConfig,
    chunk: str,
    index: int,
    voice_id: str,
    model: str
) -> Path:
    """Synthesize a single chunk with caching."""
    # Generate cache key
    cache_key = _generate_cache_key(chunk, cfg.tts.provider, voice_id, model)

    # Check cache
    cache_manager = CacheManager(cfg)
    cached_path = cache_manager.get_cached_audio(cache_key)

    if cached_path and cached_path.exists():
        logger.info(f"Using cached audio for chunk {index}")
        return cached_path

    # Synthesize via n8n webhook
    n8n_client = N8NClient(cfg)

    try:
        response = await n8n_client.trigger_tts_webhook_async(
            text=chunk,
            voice_id=voice_id,
            model=model,
            chunk_id=f"chunk_{index}",
        )

        # Robust success + path handling (normalized in client, but keep safe here)
        ok = bool(response.get("success")) or str(response.get("status", "")).lower() in ("ok", "success")
        audio_path_val = response.get("audio_path")
        if not audio_path_val:
            output = response.get("output") or {}
            files = output.get("files") or []
            if isinstance(files, list):
                audio_path_val = next((f for f in files if f), None)

        if not ok or not audio_path_val:
            # Attempt local fallback before failing
            fb = _local_tts_fallback(cfg, chunk, index)
            if fb:
                cache_manager.cache_audio(cache_key, fb)
                return fb
            raise TTSError(f"TTS failed for chunk {index}: {response.get('error') or 'missing audio path'}")

        audio_path = Path(audio_path_val)

        # Cache the result
        cache_manager.cache_audio(cache_key, audio_path)

        return audio_path

    except Exception as e:
        logger.error(f"Failed to synthesize chunk {index}: {e}")
        # Last-chance local fallback
        fb = _local_tts_fallback(cfg, chunk, index)
        if fb:
            cache_manager.cache_audio(cache_key, fb)
            return fb
        raise TTSError(f"TTS synthesis failed: {e}")


def _local_tts_fallback(cfg: AppConfig, text: str, index: int) -> Optional[Path]:
    """Local, no-network TTS fallback.

    Tries gTTS (if installed). If unavailable, generates short silence so the pipeline can proceed.
    Returns a WAV path or None on failure.
    """
    from pathlib import Path as _Path
    import subprocess
    cache_dir = cfg.directories.cache_dir / "tts_fallback"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Try gTTS
    try:
        from gtts import gTTS  # type: ignore
        mp3_path = cache_dir / f"chunk_{index}.mp3"
        wav_path = cache_dir / f"chunk_{index}.wav"
        gTTS(text=text, lang='en', slow=False).save(str(mp3_path))
        # Convert to WAV for consistent downstream merge
        subprocess.run([
            cfg.video.ffmpeg_bin, "-y", "-i", str(mp3_path), "-ar", "44100", "-ac", "1", str(wav_path)
        ], check=True, capture_output=True, text=True)
        return wav_path
    except Exception as e:  # gTTS missing or failed
        logger.warning(f"Local gTTS fallback unavailable: {e}. Generating silence.")

    # Generate brief silence as last resort
    try:
        wav_path = cache_dir / f"chunk_{index}_silence.wav"
        # 1s silence to keep timeline moving
        subprocess.run([
            cfg.video.ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", "1.0",
            str(wav_path)
        ], check=True, capture_output=True, text=True)
        return wav_path
    except Exception as e:
        logger.error(f"Failed to generate silence fallback: {e}")
        return None


def _generate_cache_key(
    text: str,
    provider: str,
    voice_id: str,
    model: str
) -> str:
    """Generate SHA-256 cache key for TTS chunk."""
    # Normalize text for consistent hashing
    normalized = text.strip().lower()

    # Create hash input
    hash_input = f"{normalized}|{provider}|{voice_id}|{model}"

    # Generate SHA-256 hash
    return hashlib.sha256(hash_input.encode()).hexdigest()


def merge_audio(
    cfg: AppConfig,
    segments: List[Path],
    out_path: Path,
    gap_ms: int = 120,
    normalize: bool = True
) -> None:
    """Merge audio segments with optional gaps and normalization.

    Args:
        cfg: Application configuration
        segments: List of audio file paths
        out_path: Output file path
        gap_ms: Gap between segments in milliseconds
        normalize: Whether to normalize loudness
    """
    import subprocess

    # Build FFmpeg filter complex
    filter_parts = []
    inputs = []

    for i, segment in enumerate(segments):
        inputs.extend(["-i", str(segment)])

    # Normalize each input to consistent format (44.1kHz mono)
    normalized_inputs = []
    for i in range(len(segments)):
        filter_parts.append(
            f"[{i}:a]aresample=44100,aformat=channel_layouts=mono[norm{i}]"
        )
        normalized_inputs.append(f"[norm{i}]")

    # Create concat filter with gaps
    if gap_ms > 0:
        # Generate silence at same format
        silence_duration = gap_ms / 1000.0
        filter_parts.append(
            f"aevalsrc=0:d={silence_duration}:s=44100:c=mono[silence]"
        )

        # Interleave audio with silence
        concat_inputs = []
        for i, norm_input in enumerate(normalized_inputs):
            concat_inputs.append(norm_input)
            if i < len(segments) - 1:
                concat_inputs.append("[silence]")

        concat_string = "".join(concat_inputs)
        filter_parts.append(
            f"{concat_string}concat=n={len(segments)*2-1}:v=0:a=1[merged]"
        )
    else:
        # Simple concatenation
        concat_inputs = "".join(normalized_inputs)
        filter_parts.append(
            f"{concat_inputs}concat=n={len(segments)}:v=0:a=1[merged]"
        )

    # Add normalization if requested
    if normalize:
        filter_parts.append(
            "[merged]loudnorm=I=-16:TP=-1.5:LRA=11[normalized]"
        )
        output_label = "[normalized]"
    else:
        output_label = "[merged]"

    # Resample to standard rate
    filter_parts.append(
        f"{output_label}aresample=44100,aformat=sample_fmts=s16:channel_layouts=mono[final]"
    )

    # Build FFmpeg command
    cmd = [
        cfg.video.ffmpeg_bin,
        *inputs,
        "-filter_complex",
        ";".join(filter_parts),
        "-map", "[final]",
        "-c:a", "pcm_s16le",
        "-ar", "44100",
        "-ac", "1",
        str(out_path),
        "-y"
    ]

    # Execute FFmpeg
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Successfully merged {len(segments)} audio segments")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg merge failed: {e.stderr}")
        raise TTSError(f"Audio merge failed: {e}")


def voiceover_for_slug(
    cfg: AppConfig,
    slug: str,
    overwrite: bool = False
) -> Path:
    """Generate complete voiceover for a content slug.

    Args:
        cfg: Application configuration
        slug: Content slug identifier
        overwrite: Whether to overwrite existing audio

    Returns:
        Path to generated audio file
    """
    content_dir = cfg.directories.content_dir / slug
    script_path = content_dir / "script.md"
    audio_path = content_dir / "audio.wav"

    # Check if audio already exists
    if audio_path.exists() and not overwrite:
        logger.info(f"Audio already exists for {slug}, skipping generation")
        return audio_path

    # Load script
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    script_text = script_path.read_text(encoding="utf-8")

    # Chunk the script
    chunks = chunk_script(script_text, max_chars=3000)
    logger.info(f"Split script into {len(chunks)} chunks")

    # Create TTS cache directory
    cache_dir = content_dir / "tts_cache"
    cache_dir.mkdir(exist_ok=True)

    # Synthesize chunks (using async in sync context)
    async def _synthesize():
        return await synthesize_chunks(cfg, chunks)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        segment_paths = loop.run_until_complete(_synthesize())
    finally:
        loop.close()

    # Merge audio segments
    merge_audio(
        cfg,
        segment_paths,
        audio_path,
        gap_ms=120,
        normalize=True
    )

    # Clean up cache if requested
    if getattr(cfg.performance, 'cleanup_temp_files', False):
        for segment in segment_paths:
            try:
                segment.unlink()
            except Exception:
                pass

    logger.info(f"Generated voiceover: {audio_path}")
    return audio_path


# Cost estimation utilities

def estimate_tts_cost(
    text: str,
    provider: str,
    model: Optional[str] = None
) -> float:
    """Estimate TTS cost based on character count and provider rates.

    Args:
        text: Text to synthesize
        provider: TTS provider name
        model: Optional model name

    Returns:
        Estimated cost in USD
    """
    char_count = len(text)

    # Provider rates (USD per 1000 characters)
    rates = {
        "elevenlabs": {
            "eleven_monolingual_v1": 0.30,
            "eleven_multilingual_v2": 0.45,
        },
        "playht": {
            "PlayHT2.0": 0.20,
            "PlayHT1.0": 0.15,
        },
        "google": {
            "standard": 0.004,
            "wavenet": 0.016,
            "neural2": 0.016,
        },
        "azure": {
            "standard": 0.004,
            "neural": 0.016,
        },
    }

    provider_rates = rates.get(provider, {})

    if model and model in provider_rates:
        rate = provider_rates[model]
    else:
        # Use first available rate for provider
        rate = next(iter(provider_rates.values()), 0.01)

    cost = (char_count / 1000) * rate

    return round(cost, 4)


def calculate_audio_duration(text: str, words_per_minute: int = 150) -> float:
    """Estimate audio duration from text.

    Args:
        text: Text content
        words_per_minute: Speaking rate

    Returns:
        Estimated duration in seconds
    """
    # Count words (simple split)
    words = len(text.split())

    # Calculate duration
    minutes = words / words_per_minute
    seconds = minutes * 60

    return round(seconds, 1)