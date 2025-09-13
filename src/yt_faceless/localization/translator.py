"""Multi-language translation and localization system."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import AppConfig
from ..core.schemas import LocalizationRequest
from ..integrations.n8n_client import N8NClient
from ..logging_setup import get_logger

logger = get_logger(__name__)


class LocalizationManager:
    """Manages content localization and translation."""

    def __init__(self, config: AppConfig):
        """Initialize localization manager.

        Args:
            config: Application configuration
        """
        self.config = config
        self.n8n_client = N8NClient(config)
        self.data_dir = config.directories.data_dir / "localization"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.translations_dir = self.data_dir / "translations"
        self.translations_dir.mkdir(parents=True, exist_ok=True)

        # Load language configurations
        self.lang_config_file = self.data_dir / "languages.json"
        self.languages = self._load_language_config()

    def _load_language_config(self) -> Dict[str, Any]:
        """Load language configuration."""
        if not self.lang_config_file.exists():
            # Create default configuration
            default_config = {
                "supported_languages": {
                    "es": {
                        "name": "Spanish",
                        "native_name": "Español",
                        "market_size": "large",
                        "regions": ["ES", "MX", "AR", "CO"],
                        "tts_voice": "es-ES-Standard-A",
                        "subtitle_style": {
                            "font": "Arial",
                            "size": 48,
                            "color": "white"
                        }
                    },
                    "pt": {
                        "name": "Portuguese",
                        "native_name": "Português",
                        "market_size": "large",
                        "regions": ["BR", "PT"],
                        "tts_voice": "pt-BR-Standard-A",
                        "subtitle_style": {
                            "font": "Arial",
                            "size": 48,
                            "color": "white"
                        }
                    },
                    "fr": {
                        "name": "French",
                        "native_name": "Français",
                        "market_size": "medium",
                        "regions": ["FR", "CA", "BE"],
                        "tts_voice": "fr-FR-Standard-A",
                        "subtitle_style": {
                            "font": "Arial",
                            "size": 48,
                            "color": "white"
                        }
                    },
                    "de": {
                        "name": "German",
                        "native_name": "Deutsch",
                        "market_size": "medium",
                        "regions": ["DE", "AT", "CH"],
                        "tts_voice": "de-DE-Standard-A",
                        "subtitle_style": {
                            "font": "Arial",
                            "size": 48,
                            "color": "white"
                        }
                    },
                    "hi": {
                        "name": "Hindi",
                        "native_name": "हिन्दी",
                        "market_size": "large",
                        "regions": ["IN"],
                        "tts_voice": "hi-IN-Standard-A",
                        "subtitle_style": {
                            "font": "Noto Sans Devanagari",
                            "size": 48,
                            "color": "yellow"
                        }
                    },
                    "ja": {
                        "name": "Japanese",
                        "native_name": "日本語",
                        "market_size": "medium",
                        "regions": ["JP"],
                        "tts_voice": "ja-JP-Standard-A",
                        "subtitle_style": {
                            "font": "Noto Sans CJK JP",
                            "size": 42,
                            "color": "white"
                        }
                    },
                    "zh": {
                        "name": "Chinese",
                        "native_name": "中文",
                        "market_size": "large",
                        "regions": ["CN", "TW", "HK"],
                        "tts_voice": "zh-CN-Standard-A",
                        "subtitle_style": {
                            "font": "Noto Sans CJK SC",
                            "size": 42,
                            "color": "white"
                        }
                    }
                },
                "translation_providers": {
                    "primary": "deepl",  # or "google", "azure"
                    "fallback": "google",
                    "cache_translations": True
                },
                "localization_strategy": {
                    "adapt_cultural_references": True,
                    "localize_numbers_dates": True,
                    "preserve_brand_names": True,
                    "seo_optimization": True
                }
            }
            self.lang_config_file.write_text(json.dumps(default_config, indent=2))
            logger.info(f"Created default language config at {self.lang_config_file}")

        with open(self.lang_config_file, 'r') as f:
            return json.load(f)

    async def translate_text(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
        context: Optional[str] = None
    ) -> str:
        """Translate text to target language.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code
            context: Optional context for better translation

        Returns:
            Translated text
        """
        # Check cache first
        cache_key = f"{source_lang}_{target_lang}_{hash(text)}"
        cache_file = self.translations_dir / f"{cache_key}.txt"

        if cache_file.exists() and self.languages.get("translation_providers", {}).get("cache_translations", True):
            return cache_file.read_text(encoding='utf-8')

        # Use translation webhook
        if not getattr(self.config.webhooks, "translation_url", None):
            logger.warning("Translation webhook not configured")
            return text

        try:
            payload = {
                "text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "context": context,
                "provider": self.languages.get("translation_providers", {}).get("primary", "google")
            }

            response = await self.n8n_client.execute_webhook(
                self.config.webhooks.translation_url,
                payload,
                timeout=30
            )

            translated = response.get("translated_text", text)

            # Cache translation
            if self.languages.get("translation_providers", {}).get("cache_translations", True):
                cache_file.write_text(translated, encoding='utf-8')

            return translated

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text

    async def translate_metadata(
        self,
        metadata: Dict[str, Any],
        target_lang: str,
        source_lang: str = "en"
    ) -> Dict[str, Any]:
        """Translate video metadata.

        Args:
            metadata: Original metadata
            target_lang: Target language code
            source_lang: Source language code

        Returns:
            Translated metadata
        """
        translated = metadata.copy()

        # Translate title
        if "title" in metadata:
            translated["title"] = await self.translate_text(
                metadata["title"],
                target_lang,
                source_lang,
                context="youtube_video_title"
            )

        # Translate description
        if "description" in metadata:
            desc_text = metadata["description"]
            if isinstance(desc_text, dict):
                desc_text = desc_text.get("text", "")

            translated_desc = await self.translate_text(
                desc_text,
                target_lang,
                source_lang,
                context="youtube_video_description"
            )

            if isinstance(metadata["description"], dict):
                translated["description"] = metadata["description"].copy()
                translated["description"]["text"] = translated_desc
            else:
                translated["description"] = translated_desc

        # Translate tags with SEO optimization
        if "tags" in metadata:
            # Handle both dict and list tag formats
            tags_to_translate = []
            if isinstance(metadata["tags"], dict):
                # Flatten dict tags (primary + competitive)
                tags_to_translate = metadata["tags"].get("primary", []) + metadata["tags"].get("competitive", [])
            else:
                tags_to_translate = metadata.get("tags", [])

            translated_tags = []
            for tag in tags_to_translate:
                translated_tag = await self.translate_text(
                    tag,
                    target_lang,
                    source_lang,
                    context="youtube_tag"
                )
                translated_tags.append(translated_tag)

            # Add language-specific SEO tags
            lang_info = self.languages.get("supported_languages", {}).get(target_lang, {})
            if lang_info:
                translated_tags.append(lang_info.get("native_name", target_lang))
                for region in lang_info.get("regions", [])[:2]:
                    translated_tags.append(region.lower())

            translated["tags"] = translated_tags

        # Add localization metadata
        translated["localization"] = {
            "source_language": source_lang,
            "target_language": target_lang,
            "language_name": self.languages.get("supported_languages", {}).get(target_lang, {}).get("name", target_lang),
            "translated_at": datetime.now().isoformat()
        }

        return translated

    async def generate_multilingual_subtitles(
        self,
        script_path: Path,
        target_langs: List[str],
        source_lang: str = "en"
    ) -> Dict[str, Path]:
        """Generate subtitles in multiple languages.

        Args:
            script_path: Path to original script/subtitles
            target_langs: List of target language codes
            source_lang: Source language code

        Returns:
            Dictionary of language -> subtitle file path
        """
        subtitle_files = {}

        # Load original script
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return subtitle_files

        with open(script_path, 'r', encoding='utf-8') as f:
            original_text = f.read()

        # Parse SRT if it's a subtitle file
        if script_path.suffix == ".srt":
            segments = self._parse_srt(original_text)
        else:
            # Treat as plain text script
            segments = [{"text": original_text, "start": 0, "end": 0}]

        for lang in target_langs:
            try:
                # Translate each segment
                translated_segments = []
                for segment in segments:
                    translated_text = await self.translate_text(
                        segment["text"],
                        lang,
                        source_lang
                    )
                    translated_segments.append({
                        **segment,
                        "text": translated_text
                    })

                # Generate SRT file
                output_path = script_path.parent / f"subtitles_{lang}.srt"
                srt_content = self._generate_srt(translated_segments)
                output_path.write_text(srt_content, encoding='utf-8')

                subtitle_files[lang] = output_path
                logger.info(f"Generated {lang} subtitles: {output_path}")

            except Exception as e:
                logger.error(f"Failed to generate {lang} subtitles: {e}")

        return subtitle_files

    def _parse_srt(self, srt_content: str) -> List[Dict[str, Any]]:
        """Parse SRT subtitle content.

        Args:
            srt_content: SRT file content

        Returns:
            List of subtitle segments
        """
        segments = []
        blocks = srt_content.strip().split('\n\n')

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # Parse timing
                timing_line = lines[1]
                start_str, end_str = timing_line.split(' --> ')

                # Parse text (may be multiple lines)
                text = '\n'.join(lines[2:])

                segments.append({
                    "index": int(lines[0]),
                    "start_str": start_str,
                    "end_str": end_str,
                    "text": text
                })

        return segments

    def _generate_srt(self, segments: List[Dict[str, Any]]) -> str:
        """Generate SRT subtitle content.

        Args:
            segments: List of subtitle segments

        Returns:
            SRT formatted string
        """
        srt_lines = []

        for i, segment in enumerate(segments, 1):
            srt_lines.append(str(i))
            srt_lines.append(f"{segment.get('start_str', '00:00:00,000')} --> {segment.get('end_str', '00:00:05,000')}")
            srt_lines.append(segment["text"])
            srt_lines.append("")

        return '\n'.join(srt_lines)

    async def generate_voice_over(
        self,
        script: str,
        target_lang: str,
        voice_id: Optional[str] = None
    ) -> Optional[Path]:
        """Generate voice-over in target language.

        Args:
            script: Script text
            target_lang: Target language code
            voice_id: Optional specific voice ID

        Returns:
            Path to generated audio file
        """
        if not getattr(self.config.webhooks, "tts_url", None):
            logger.warning("TTS webhook not configured")
            return None

        # Get language-specific voice
        lang_info = self.languages.get("supported_languages", {}).get(target_lang, {})
        if not voice_id:
            voice_id = lang_info.get("tts_voice", f"{target_lang}-Standard-A")

        try:
            payload = {
                "text": script,
                "voice_id": voice_id,
                "language": target_lang,
                "speed": 1.0,
                "pitch": 0
            }

            response = await self.n8n_client.execute_webhook(
                self.config.webhooks.tts_url,
                payload,
                timeout=60
            )

            audio_path = Path(response.get("audio_path", ""))
            if audio_path.exists():
                return audio_path

            logger.error(f"Generated audio not found: {audio_path}")
            return None

        except Exception as e:
            logger.error(f"Voice-over generation failed: {e}")
            return None

    def get_market_priority(self, lang: str) -> int:
        """Get market priority for a language.

        Args:
            lang: Language code

        Returns:
            Priority score (higher is better)
        """
        lang_info = self.languages.get("supported_languages", {}).get(lang, {})
        market_size = lang_info.get("market_size", "small")

        priorities = {
            "large": 3,
            "medium": 2,
            "small": 1
        }

        return priorities.get(market_size, 0)


async def translate_content(
    config: AppConfig,
    slug: str,
    target_languages: List[str],
    generate_audio: bool = False,
    generate_subtitles: bool = True,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Translate content to multiple languages.

    Args:
        config: Application configuration
        slug: Video slug
        target_languages: List of target language codes
        generate_audio: Whether to generate voice-overs
        generate_subtitles: Whether to generate subtitles
        dry_run: Simulate without translating

    Returns:
        Translation results
    """
    if not (config.features.get("multi_language") or config.features.get("localization")):
        logger.info("Localization feature is disabled")
        return {"status": "disabled"}

    manager = LocalizationManager(config)

    # Load content
    content_dir = config.directories.content_dir / slug
    metadata_path = content_dir / "metadata.json"
    script_path = content_dir / "script.md"
    subtitles_path = content_dir / "subtitles.srt"

    if not metadata_path.exists():
        logger.error(f"Metadata not found: {metadata_path}")
        return {"status": "error", "reason": "metadata_not_found"}

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    results = {
        "slug": slug,
        "languages": {}
    }

    # Sort languages by market priority
    target_languages.sort(key=lambda l: manager.get_market_priority(l), reverse=True)

    for lang in target_languages:
        if dry_run:
            results["languages"][lang] = {
                "status": "dry_run",
                "would_translate": ["metadata", "subtitles"],
                "market_priority": manager.get_market_priority(lang)
            }
            continue

        lang_results = {}

        try:
            # Translate metadata
            translated_metadata = await manager.translate_metadata(metadata, lang)

            # Save translated metadata
            lang_dir = content_dir / "localized" / lang
            lang_dir.mkdir(parents=True, exist_ok=True)

            metadata_file = lang_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(translated_metadata, f, indent=2, ensure_ascii=False)

            lang_results["metadata"] = str(metadata_file)

            # Generate subtitles
            if generate_subtitles:
                subtitle_source = subtitles_path if subtitles_path.exists() else script_path
                if subtitle_source.exists():
                    subtitle_files = await manager.generate_multilingual_subtitles(
                        subtitle_source,
                        [lang]
                    )
                    if lang in subtitle_files:
                        lang_results["subtitles"] = str(subtitle_files[lang])

            # Generate voice-over
            if generate_audio and script_path.exists():
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_text = f.read()

                translated_script = await manager.translate_text(script_text, lang)
                audio_path = await manager.generate_voice_over(translated_script, lang)

                if audio_path:
                    lang_results["audio"] = str(audio_path)

            lang_results["status"] = "success"
            results["languages"][lang] = lang_results
            logger.info(f"Translated content to {lang}")

        except Exception as e:
            logger.error(f"Failed to translate to {lang}: {e}")
            results["languages"][lang] = {
                "status": "failed",
                "error": str(e)
            }

    return results


async def generate_multilingual_metadata(
    config: AppConfig,
    slug: str,
    languages: List[str]
) -> Dict[str, Dict[str, Any]]:
    """Generate metadata in multiple languages.

    Args:
        config: Application configuration
        slug: Video slug
        languages: Target language codes

    Returns:
        Dictionary of language -> metadata
    """
    result = await translate_content(
        config,
        slug,
        languages,
        generate_audio=False,
        generate_subtitles=False
    )

    metadata_by_lang = {}
    for lang, lang_result in result.get("languages", {}).items():
        if lang_result.get("status") == "success" and "metadata" in lang_result:
            metadata_path = Path(lang_result["metadata"])
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata_by_lang[lang] = json.load(f)

    return metadata_by_lang