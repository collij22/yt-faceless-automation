from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(slots=True)
class VideoChapters:
    """Chapter markers for YouTube video description."""

    items: list[tuple[int, str]]  # (seconds, title)

    def to_description_block(self) -> str:
        lines = ["Chapters:"]
        for seconds, title in self.items:
            mm = seconds // 60
            ss = seconds % 60
            lines.append(f"{mm:02d}:{ss:02d} - {title}")
        return "\n".join(lines)


@dataclass(slots=True)
class VideoMetadata:
    """SEO-focused video metadata container."""

    title: str
    description: str
    tags: list[str]
    chapters: VideoChapters | None = None

    def full_description(self) -> str:
        parts: list[str] = [self.description.strip()]
        if self.chapters and self.chapters.items:
            parts.append("\n" + self.chapters.to_description_block())
        return "\n".join(parts)


def choose_best_title(candidates: Sequence[str]) -> str:
    """Choose the strongest title candidate with simple heuristics.

    Prefers: brevity (<= 60 chars), power words, and clarity.
    """
    def score(title: str) -> int:
        s = 0
        if len(title) <= 60:
            s += 2
        power = ["secret", "ultimate", "new", "2025", "ai", "earn", "fast"]
        s += sum(1 for w in power if w in title.lower())
        if ":" in title or "-" in title:
            s += 1
        return s

    return max(candidates, key=score)
