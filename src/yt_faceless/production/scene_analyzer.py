"""Scene analysis and keyword extraction for visual asset matching."""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SceneSegment:
    """Represents a single scene segment."""

    index: int
    start_time: float
    end_time: float
    duration: float
    text: str
    section_marker: Optional[str]  # e.g., [HOOK], [KEY INSIGHT]
    keywords: List[str]
    search_queries: List[str]
    key_phrase: Optional[str]  # For text overlay
    visual_cues: List[str]
    b_roll_suggestions: List[str]
    scene_type: Optional[str] = None

    def __post_init__(self):
        """Infer scene type from section marker if not provided."""
        if not self.scene_type and self.section_marker:
            marker_upper = self.section_marker.upper()
            if "INTRO" in marker_upper or "HOOK" in marker_upper:
                self.scene_type = "HOOK"
            elif "PROOF" in marker_upper or "FACT" in marker_upper:
                self.scene_type = "PROOF"
            elif "DEMO" in marker_upper or "EXAMPLE" in marker_upper:
                self.scene_type = "DEMONSTRATION"
            elif "CTA" in marker_upper or "OUTRO" in marker_upper:
                self.scene_type = "OUTRO"
            else:
                self.scene_type = "MAIN"


class SceneAnalyzer:
    """Analyzes script content to extract scenes and keywords."""

    # Common stopwords to filter out
    STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "been", "by", "for", "from",
        "has", "have", "he", "in", "is", "it", "its", "of", "on", "that", "the",
        "to", "was", "will", "with", "you", "your", "this", "these", "those",
        "they", "them", "we", "our", "i", "me", "my", "can", "could", "would",
        "should", "just", "like", "get", "got", "make", "made", "let", "lets",
        "but", "or", "if", "then", "so", "because", "when", "where", "what",
        "why", "how", "which", "who", "very", "really", "actually", "basically",
        "literally", "simply", "merely", "quite", "rather", "somewhat", "fairly"
    }

    # Scene duration buckets (in seconds)
    SCENE_DURATIONS = {
        "short": (4, 8),     # Quick facts, transitions
        "medium": (8, 15),   # Explanations, examples
        "long": (15, 25),    # Detailed proofs, demonstrations
    }

    # Section markers and their typical durations
    SECTION_MARKERS = {
        "HOOK": "short",
        "TEASER": "short",
        "INTRO": "medium",
        "KEY INSIGHT": "medium",
        "POINT": "medium",
        "EXAMPLE": "medium",
        "PROOF": "long",
        "DEMONSTRATION": "long",
        "DEEP DIVE": "long",
        "CTA": "short",
        "OUTRO": "short",
        "END": "short",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize scene analyzer.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.min_scene_duration = self.config.get("min_scene_duration", 4)
        self.max_scene_duration = self.config.get("max_scene_duration", 25)
        self.words_per_minute = self.config.get("words_per_minute", 150)

    def analyze_script(
        self,
        script_text: str,
        metadata: Optional[Dict[str, Any]] = None,
        audio_duration: Optional[float] = None
    ) -> List[SceneSegment]:
        """Analyze script and segment into scenes.

        Args:
            script_text: Full script text
            metadata: Optional metadata with sections, visual cues, etc.
            audio_duration: Optional total audio duration in seconds

        Returns:
            List of scene segments
        """
        # Extract structural markers; if none found, synthesize coarse sections from the script
        sections = self._extract_sections(script_text)
        if not sections:
            # Create simple sections by splitting the script into paragraphs
            paras = [p.strip() for p in script_text.split("\n\n") if p.strip()]
            cur_time = 0.0
            est_wpm = self.words_per_minute
            synthesized = []
            for i, para in enumerate(paras[:12]):  # cap to avoid too many
                words = len(para.split())
                dur = max(6.0, min(20.0, (words / est_wpm) * 60))
                synthesized.append({
                    "marker": None,
                    "start_time": cur_time,
                    "end_time": cur_time + dur,
                    "text": para,
                    "visual_cues": [],
                    "b_roll_suggestions": []
                })
                cur_time += dur
            if synthesized:
                sections = synthesized

        # If we have metadata sections, use those
        if metadata and "sections" in metadata:
            sections = self._merge_with_metadata_sections(sections, metadata["sections"])

        # Segment into scenes
        scenes = self._segment_into_scenes(sections, audio_duration)

        # Extract keywords and generate queries for each scene
        for scene in scenes:
            scene.keywords = self._extract_keywords(scene.text)
            scene.search_queries = self._generate_search_queries(
                scene.keywords,
                scene.visual_cues,
                metadata.get("tags", []) if metadata else []
            )
            scene.key_phrase = self._extract_key_phrase(scene.text)

        return scenes

    def _extract_sections(self, script_text: str) -> List[Dict[str, Any]]:
        """Extract sections from script markers.

        Args:
            script_text: Script text with markers

        Returns:
            List of section dictionaries
        """
        sections = []

        # Pattern for markers like [HOOK - 0:00] or [KEY INSIGHT]
        marker_pattern = re.compile(
            r'\[([A-Z\s]+)(?:\s*-\s*(\d+:\d+))?\]',
            re.IGNORECASE
        )

        # Split script by markers
        last_pos = 0
        for match in marker_pattern.finditer(script_text):
            # Add previous text if any
            if match.start() > last_pos:
                prev_text = script_text[last_pos:match.start()].strip()
                if prev_text and sections:
                    sections[-1]["text"] += " " + prev_text

            # Parse marker and time
            marker = match.group(1).strip().upper()
            time_str = match.group(2)

            # Convert time to seconds
            start_time = 0
            if time_str:
                parts = time_str.split(":")
                if len(parts) == 2:
                    start_time = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 1:
                    start_time = int(parts[0])

            # Create new section
            section = {
                "marker": marker,
                "start_time": start_time,
                "text": "",
                "visual_cues": [],
                "b_roll_suggestions": []
            }

            # Extract visual cues from text
            section["visual_cues"] = self._extract_visual_cues(
                script_text[match.end():match.end() + 500]  # Look ahead
            )

            sections.append(section)
            last_pos = match.end()

        # Add remaining text
        if last_pos < len(script_text):
            remaining = script_text[last_pos:].strip()
            if remaining:
                if sections:
                    sections[-1]["text"] += " " + remaining
                else:
                    # No markers found, treat entire script as one section
                    sections.append({
                        "marker": None,
                        "start_time": 0,
                        "text": script_text,
                        "visual_cues": self._extract_visual_cues(script_text),
                        "b_roll_suggestions": []
                    })

        return sections

    def _extract_visual_cues(self, text: str) -> List[str]:
        """Extract visual cues from text.

        Args:
            text: Text to analyze

        Returns:
            List of visual cues
        """
        cues = []

        # Pattern for explicit B-ROLL markers
        b_roll_pattern = re.compile(r'\[B-?ROLL:\s*([^\]]+)\]', re.IGNORECASE)
        for match in b_roll_pattern.finditer(text):
            cues.append(match.group(1).strip())

        # Pattern for visual descriptions in parentheses
        visual_pattern = re.compile(r'\((?:show|display|visualize|image of|video of)\s+([^)]+)\)', re.IGNORECASE)
        for match in visual_pattern.finditer(text):
            cues.append(match.group(1).strip())

        return cues

    def _merge_with_metadata_sections(
        self,
        extracted_sections: List[Dict[str, Any]],
        metadata_sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge extracted sections with metadata sections.

        Args:
            extracted_sections: Sections extracted from script
            metadata_sections: Sections from metadata

        Returns:
            Merged section list
        """
        merged = []

        for meta_section in metadata_sections:
            # Find matching extracted section
            matched = None
            for ext_section in extracted_sections:
                if (abs(ext_section["start_time"] - meta_section.get("start_time", 0)) < 2 or
                    ext_section["marker"] == meta_section.get("type", "").upper()):
                    matched = ext_section
                    break

            if matched:
                # Merge data
                merged_section = {
                    **matched,
                    "visual_cues": list(set(
                        matched.get("visual_cues", []) +
                        meta_section.get("visual_cues", [])
                    )),
                    "b_roll_suggestions": list(set(
                        matched.get("b_roll_suggestions", []) +
                        meta_section.get("b_roll_suggestions", [])
                    )),
                    "end_time": meta_section.get("end_time"),
                }
            else:
                # Use metadata section as-is
                merged_section = {
                    "marker": meta_section.get("type", "").upper(),
                    "start_time": meta_section.get("start_time", 0),
                    "end_time": meta_section.get("end_time"),
                    "text": meta_section.get("text", ""),
                    "visual_cues": meta_section.get("visual_cues", []),
                    "b_roll_suggestions": meta_section.get("b_roll_suggestions", [])
                }

            merged.append(merged_section)

        # Add any unmatched extracted sections
        for ext_section in extracted_sections:
            if not any(self._sections_match(ext_section, m) for m in merged):
                merged.append(ext_section)

        # Sort by start time
        merged.sort(key=lambda s: s.get("start_time", 0))
        return merged

    def _sections_match(self, section1: Dict, section2: Dict) -> bool:
        """Check if two sections match."""
        time_match = abs(section1.get("start_time", 0) - section2.get("start_time", 0)) < 2
        marker_match = section1.get("marker") == section2.get("marker")
        return time_match or marker_match

    def _segment_into_scenes(
        self,
        sections: List[Dict[str, Any]],
        total_duration: Optional[float] = None
    ) -> List[SceneSegment]:
        """Segment sections into appropriately sized scenes.

        Args:
            sections: List of sections
            total_duration: Total duration in seconds

        Returns:
            List of scene segments
        """
        scenes = []
        scene_index = 0
        cursor = 0.0

        for i, section in enumerate(sections):
            # Calculate section duration
            if "end_time" in section and section["end_time"]:
                start_time = float(section.get("start_time", 0) or 0)
                if start_time < cursor:
                    start_time = cursor
                duration = float(section["end_time"]) - start_time
            elif i + 1 < len(sections):
                next_start = float(sections[i + 1].get("start_time", 0) or 0)
                start_time = float(section.get("start_time", 0) or 0)
                if start_time < cursor:
                    start_time = cursor
                duration = next_start - start_time
            elif total_duration:
                start_time = float(section.get("start_time", 0) or 0)
                if start_time < cursor:
                    start_time = cursor
                duration = float(total_duration) - start_time
            else:
                # Estimate from word count
                word_count = len(section["text"].split())
                start_time = float(section.get("start_time", 0) or 0)
                if start_time < cursor:
                    start_time = cursor
                duration = (word_count / self.words_per_minute) * 60

            # Determine target scene duration based on marker
            if section.get("marker") in self.SECTION_MARKERS:
                duration_type = self.SECTION_MARKERS[section["marker"]]
                min_dur, max_dur = self.SCENE_DURATIONS[duration_type]
            else:
                min_dur = self.min_scene_duration
                max_dur = self.max_scene_duration

            # Split into scenes if too long
            if duration > max_dur:
                num_scenes = int(duration / ((min_dur + max_dur) / 2))
                scene_duration = duration / num_scenes

                # Split text proportionally
                words = section["text"].split()
                words_per_scene = len(words) // num_scenes

                for j in range(num_scenes):
                    start_idx = j * words_per_scene
                    end_idx = (j + 1) * words_per_scene if j < num_scenes - 1 else len(words)
                    scene_text = " ".join(words[start_idx:end_idx])

                    scene = SceneSegment(
                        index=scene_index,
                        start_time=start_time + (j * scene_duration),
                        end_time=start_time + ((j + 1) * scene_duration),
                        duration=scene_duration,
                        text=scene_text,
                        section_marker=section.get("marker"),
                        keywords=[],
                        search_queries=[],
                        key_phrase=None,
                        visual_cues=section.get("visual_cues", []) if j == 0 else [],
                        b_roll_suggestions=section.get("b_roll_suggestions", []) if j == 0 else []
                    )
                    scenes.append(scene)
                    scene_index += 1
                cursor = scenes[-1].end_time
            else:
                # Use section as single scene
                end_time = start_time + duration
                # Clamp to bounds
                if duration < min_dur:
                    end_time = start_time + min_dur
                if duration > max_dur:
                    end_time = start_time + max_dur
                scene = SceneSegment(
                    index=scene_index,
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    text=section["text"],
                    section_marker=section.get("marker"),
                    keywords=[],
                    search_queries=[],
                    key_phrase=None,
                    visual_cues=section.get("visual_cues", []),
                    b_roll_suggestions=section.get("b_roll_suggestions", [])
                )
                scenes.append(scene)
                scene_index += 1
                cursor = scene.end_time

        return scenes

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract keywords from text using simple heuristics.

        Args:
            text: Text to analyze
            max_keywords: Maximum keywords to extract

        Returns:
            List of keywords
        """
        # Clean and tokenize
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text_clean.split()

        # Filter stopwords and short words
        words = [w for w in words if w not in self.STOPWORDS and len(w) > 3]

        # Identify potential nouns (simple heuristic)
        nouns = []
        noun_suffixes = ["tion", "ment", "ness", "ity", "ing", "er", "or", "ist"]

        for word in words:
            # Check if word ends with common noun suffixes
            if any(word.endswith(suffix) for suffix in noun_suffixes):
                nouns.append(word)
            # Or if it's capitalized in original (proper noun)
            elif word.title() in text:
                nouns.append(word)
            # Or if it appears multiple times (important term)
            elif words.count(word) > 1:
                nouns.append(word)

        # Count frequencies
        word_freq = Counter(nouns if nouns else words)

        # Get top keywords
        keywords = [word for word, _ in word_freq.most_common(max_keywords)]

        # Add any numbers/statistics mentioned
        numbers = re.findall(r'\b\d+(?:\.\d+)?(?:\s*(?:%|percent|million|billion|thousand))?\b', text, re.IGNORECASE)
        for num in numbers[:2]:  # Add up to 2 numbers
            keywords.append(num.strip())

        return keywords[:max_keywords]

    def _generate_search_queries(
        self,
        keywords: List[str],
        visual_cues: List[str],
        tags: List[str]
    ) -> List[str]:
        """Generate search queries for finding relevant images.

        Args:
            keywords: Extracted keywords
            visual_cues: Visual cues from script
            tags: Video tags/topics

        Returns:
            List of search queries
        """
        queries = []

        # Direct visual cues have highest priority
        queries.extend(visual_cues[:3])

        # Combine keywords for queries
        if len(keywords) >= 2:
            queries.append(" ".join(keywords[:2]))

        # Individual important keywords
        for keyword in keywords[:3]:
            if len(keyword) > 4:  # Skip very short words
                queries.append(keyword)

        # Add topic-based queries if available
        if tags:
            if isinstance(tags, dict):
                primary_tags = tags.get("primary", [])[:2]
            elif isinstance(tags, list):
                primary_tags = tags[:2]
            else:
                primary_tags = []

            for tag in primary_tags:
                if keywords:
                    queries.append(f"{tag} {keywords[0]}")
                else:
                    queries.append(tag)

        # Deduplicate while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q and q.lower() not in seen:
                unique_queries.append(q)
                seen.add(q.lower())

        return unique_queries[:5]  # Limit to 5 queries per scene

    def _extract_key_phrase(self, text: str, max_length: int = 60) -> Optional[str]:
        """Extract a key phrase for text overlay.

        Args:
            text: Scene text
            max_length: Maximum phrase length

        Returns:
            Key phrase or None
        """
        if not text:
            return None

        # Look for quoted text first
        quotes = re.findall(r'"([^"]+)"', text)
        for quote in quotes:
            if 10 < len(quote) < max_length:
                return quote

        # Look for key statements (after "is", "means", etc.)
        key_patterns = [
            r'(?:is|are|means?|shows?|proves?|reveals?)\s+([^.!?]{10,60})',
            r'(?:remember|note|important):\s*([^.!?]{10,60})',
            r'(?:first|second|third|finally),?\s*([^.!?]{10,60})',
        ]

        for pattern in key_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phrase = match.group(1).strip()
                if len(phrase) < max_length:
                    return phrase.capitalize()

        # Fall back to first sentence if short enough
        sentences = re.split(r'[.!?]', text)
        if sentences and len(sentences[0]) < max_length:
            return sentences[0].strip().capitalize()

        # Or first N words
        words = text.split()
        if len(words) > 5:
            phrase = " ".join(words[:8]) + "..."
            if len(phrase) < max_length:
                return phrase

        return None


def analyze_script_for_scenes(
    script_path: Path,
    metadata_path: Optional[Path] = None,
    audio_path: Optional[Path] = None
) -> List[SceneSegment]:
    """Convenience function to analyze a script file.

    Args:
        script_path: Path to script file
        metadata_path: Optional path to metadata JSON
        audio_path: Optional path to audio file for duration

    Returns:
        List of scene segments
    """
    # Load script
    script_text = script_path.read_text(encoding="utf-8")

    # Load metadata if provided
    metadata = None
    if metadata_path and metadata_path.exists():
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

    # Get audio duration if provided
    audio_duration = None
    if audio_path and audio_path.exists():
        # TODO: Use ffprobe to get actual duration
        # For now, estimate from script
        word_count = len(script_text.split())
        audio_duration = (word_count / 150) * 60  # Assume 150 WPM

    # Analyze
    analyzer = SceneAnalyzer()
    scenes = analyzer.analyze_script(script_text, metadata, audio_duration)

    return scenes