"""Multi-language localization and translation system."""

from .translator import (
    LocalizationManager,
    translate_content,
    generate_multilingual_metadata,
)

__all__ = [
    "LocalizationManager",
    "translate_content",
    "generate_multilingual_metadata",
]