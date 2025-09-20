"""Fallback mechanisms for visual content generation."""

from __future__ import annotations

import hashlib
import logging
import random
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class VisualFallbackGenerator:
    """Generates fallback visuals when assets are unavailable."""

    # Predefined color gradients
    GRADIENTS = [
        # Warm gradients
        [(255, 94, 77), (255, 154, 0)],    # Sunset
        [(255, 0, 132), (252, 176, 69)],   # Tropical
        [(248, 87, 195), (224, 109, 235)], # Pink Purple

        # Cool gradients
        [(0, 176, 255), (0, 82, 212)],     # Ocean
        [(67, 198, 172), (25, 22, 84)],    # Teal Night
        [(142, 158, 255), (235, 142, 255)], # Pastel Purple

        # Dark gradients
        [(29, 43, 100), (248, 205, 218)],  # Night Sky
        [(67, 67, 67), (0, 0, 0)],         # Grayscale
        [(44, 62, 80), (189, 195, 199)],   # Storm

        # Nature gradients
        [(134, 194, 50), (49, 126, 51)],   # Forest
        [(255, 175, 189), (255, 195, 160)], # Peach
        [(255, 236, 210), (252, 182, 159)], # Warm Sand
    ]

    # Fallback patterns based on content type
    CONTENT_PATTERNS = {
        "hook": [(255, 94, 77), (255, 154, 0)],      # Attention-grabbing
        "explanation": [(0, 176, 255), (0, 82, 212)], # Clear, professional
        "proof": [(67, 198, 172), (25, 22, 84)],     # Trustworthy
        "cta": [(255, 0, 132), (252, 176, 69)],      # Energetic
        "default": [(142, 158, 255), (235, 142, 255)] # Neutral
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize fallback generator.

        Args:
            cache_dir: Directory to cache generated fallbacks
        """
        self.cache_dir = cache_dir or Path(".cache/fallbacks")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate_gradient_card(
        self,
        text: str,
        width: int = 1920,
        height: int = 1080,
        scene_type: Optional[str] = None,
        seed: Optional[int] = None
    ) -> Path:
        """Generate a gradient card with text overlay.

        Args:
            text: Text to display on the card
            width: Card width in pixels
            height: Card height in pixels
            scene_type: Type of scene (hook, explanation, etc.)
            seed: Random seed for reproducible gradients

        Returns:
            Path to generated image
        """
        # Generate cache key
        cache_key = self._get_cache_key(text, width, height, scene_type, seed)
        cache_path = self.cache_dir / f"{cache_key}.png"

        if cache_path.exists():
            logger.debug(f"Using cached gradient card: {cache_path}")
            return cache_path

        # Create new gradient card
        try:
            import PIL
        except ImportError:
            logger.error("PIL not installed. Install with: pip install pillow")
            return self._create_solid_fallback(text, width, height)

        # Select gradient colors
        if scene_type and scene_type.lower() in self.CONTENT_PATTERNS:
            colors = self.CONTENT_PATTERNS[scene_type.lower()]
        else:
            random.seed(seed)
            colors = random.choice(self.GRADIENTS)

        # Create gradient image
        image = self._create_gradient(width, height, colors[0], colors[1])

        # Add text overlay
        if text:
            self._add_text_overlay(image, text)

        # Add subtle texture
        self._add_texture(image)

        # Save to cache
        image.save(cache_path, "PNG", optimize=True)
        logger.info(f"Generated gradient fallback: {cache_path}")

        return cache_path

    def generate_icon_card(
        self,
        icon_name: str,
        text: Optional[str] = None,
        width: int = 1920,
        height: int = 1080,
        color_scheme: Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = None
    ) -> Path:
        """Generate a card with an icon and optional text.

        Args:
            icon_name: Name of icon to use
            text: Optional text below icon
            width: Card width
            height: Card height
            color_scheme: Background gradient colors

        Returns:
            Path to generated image
        """
        # For now, fall back to gradient card
        # In future, could integrate with icon libraries
        return self.generate_gradient_card(
            text or icon_name,
            width,
            height,
            scene_type="default"
        )

    def generate_pattern_background(
        self,
        pattern_type: str = "dots",
        width: int = 1920,
        height: int = 1080,
        primary_color: Tuple[int, int, int] = (50, 50, 50),
        secondary_color: Tuple[int, int, int] = (30, 30, 30)
    ) -> Path:
        """Generate a patterned background.

        Args:
            pattern_type: Type of pattern (dots, lines, grid)
            width: Image width
            height: Image height
            primary_color: Main color
            secondary_color: Pattern color

        Returns:
            Path to generated image
        """
        cache_key = f"pattern_{pattern_type}_{width}x{height}_{self._color_to_hex(primary_color)}"
        cache_path = self.cache_dir / f"{cache_key}.png"

        if cache_path.exists():
            return cache_path

        try:
            image = Image.new("RGB", (width, height), primary_color)
            draw = ImageDraw.Draw(image)

            if pattern_type == "dots":
                self._draw_dot_pattern(draw, width, height, secondary_color)
            elif pattern_type == "lines":
                self._draw_line_pattern(draw, width, height, secondary_color)
            elif pattern_type == "grid":
                self._draw_grid_pattern(draw, width, height, secondary_color)

            image.save(cache_path, "PNG", optimize=True)
            return cache_path

        except Exception as e:
            logger.error(f"Failed to generate pattern: {e}")
            return self._create_solid_fallback("", width, height)

    def _create_gradient(
        self,
        width: int,
        height: int,
        color1: Tuple[int, int, int],
        color2: Tuple[int, int, int],
        direction: str = "diagonal"
    ) -> Image.Image:
        """Create a gradient image."""
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)

        if direction == "horizontal":
            for x in range(width):
                ratio = x / width
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                draw.line([(x, 0), (x, height)], fill=(r, g, b))

        elif direction == "vertical":
            for y in range(height):
                ratio = y / height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

        else:  # diagonal
            for y in range(height):
                for x in range(width):
                    ratio = (x + y) / (width + height)
                    r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                    g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                    b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                    draw.point((x, y), fill=(r, g, b))

        return image

    def _add_text_overlay(
        self,
        image: Image.Image,
        text: str,
        max_width_ratio: float = 0.8,
        max_height_ratio: float = 0.3
    ) -> None:
        """Add text overlay to image."""
        draw = ImageDraw.Draw(image, "RGBA")
        width, height = image.size

        # Try to load a nice font, fall back to default
        font_size = int(height * 0.06)  # 6% of height
        try:
            # Try common font locations
            font_paths = [
                "C:/Windows/Fonts/Arial.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ]

            font = None
            for font_path in font_paths:
                if Path(font_path).exists():
                    font = ImageFont.truetype(font_path, font_size)
                    break

            if not font:
                font = ImageFont.load_default()

        except Exception:
            font = ImageFont.load_default()

        # Word wrap text
        wrapped_text = self._wrap_text(text, font, int(width * max_width_ratio))

        # Calculate text position
        text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # Draw semi-transparent background
        padding = 30
        bg_rect = [
            x - padding,
            y - padding,
            x + text_width + padding,
            y + text_height + padding
        ]
        draw.rounded_rectangle(bg_rect, radius=15, fill=(0, 0, 0, 180))

        # Draw text
        draw.multiline_text(
            (x, y),
            wrapped_text,
            fill=(255, 255, 255, 255),
            font=font,
            align="center"
        )

    def _add_texture(self, image: Image.Image, opacity: int = 30) -> None:
        """Add subtle texture overlay to image."""
        width, height = image.size
        texture = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(texture)

        # Add noise texture
        import random
        for _ in range(width * height // 100):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            brightness = random.randint(200, 255)
            draw.point((x, y), fill=(brightness, brightness, brightness, opacity))

        # Composite texture onto image
        image.paste(texture, (0, 0), texture)

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
        """Wrap text to fit within max width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    def _draw_dot_pattern(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
        color: Tuple[int, int, int]
    ) -> None:
        """Draw dot pattern on image."""
        spacing = 50
        radius = 3

        for y in range(0, height, spacing):
            for x in range(0, width, spacing):
                draw.ellipse(
                    [x - radius, y - radius, x + radius, y + radius],
                    fill=color
                )

    def _draw_line_pattern(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
        color: Tuple[int, int, int]
    ) -> None:
        """Draw diagonal line pattern."""
        spacing = 20

        for offset in range(-height, width, spacing):
            draw.line(
                [(offset, 0), (offset + height, height)],
                fill=color,
                width=1
            )

    def _draw_grid_pattern(
        self,
        draw: ImageDraw.Draw,
        width: int,
        height: int,
        color: Tuple[int, int, int]
    ) -> None:
        """Draw grid pattern."""
        spacing = 40

        for x in range(0, width, spacing):
            draw.line([(x, 0), (x, height)], fill=color, width=1)

        for y in range(0, height, spacing):
            draw.line([(0, y), (width, y)], fill=color, width=1)

    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments."""
        key_str = "_".join(str(arg) for arg in args if arg is not None)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def _color_to_hex(self, color: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string."""
        return f"{color[0]:02x}{color[1]:02x}{color[2]:02x}"

    def _create_solid_fallback(
        self,
        text: str,
        width: int,
        height: int
    ) -> Path:
        """Create a simple solid color fallback."""
        cache_key = f"solid_{width}x{height}_{hashlib.md5(text.encode()).hexdigest()[:8]}"
        cache_path = self.cache_dir / f"{cache_key}.png"

        if not cache_path.exists():
            # Create solid color image
            try:
                image = Image.new("RGB", (width, height), (50, 50, 50))
                image.save(cache_path, "PNG")
            except Exception as e:
                logger.error(f"Failed to create solid fallback: {e}")
                # Return a placeholder path
                cache_path = self.cache_dir / "error.png"
                if not cache_path.exists():
                    # Create 1x1 pixel as last resort
                    with open(cache_path, "wb") as f:
                        f.write(b"\x89PNG\r\n\x1a\n")  # PNG header

        return cache_path


def generate_fallback_for_missing_asset(
    scene_type: Optional[str] = None,
    text: Optional[str] = None,
    width: int = 1920,
    height: int = 1080
) -> Path:
    """Generate a fallback visual for a missing asset.

    Args:
        scene_type: Type of scene
        text: Text to display
        width: Image width
        height: Image height

    Returns:
        Path to fallback image
    """
    generator = VisualFallbackGenerator()

    if not text:
        text = {
            "hook": "Welcome",
            "explanation": "Let me explain",
            "proof": "Here's the evidence",
            "cta": "Take action now",
        }.get(scene_type, "")

    return generator.generate_gradient_card(
        text,
        width,
        height,
        scene_type
    )


def ensure_minimum_assets(
    available_assets: List,
    required_count: int,
    scene_type: Optional[str] = None
) -> List:
    """Ensure minimum number of assets by generating fallbacks.

    Args:
        available_assets: Currently available assets
        required_count: Number of assets required
        scene_type: Type of scene

    Returns:
        List of assets including fallbacks
    """
    from .timeline import VisualAsset

    assets = list(available_assets)

    if len(assets) >= required_count:
        return assets[:required_count]

    # Generate fallbacks for missing assets
    generator = VisualFallbackGenerator()

    for i in range(len(assets), required_count):
        fallback_path = generator.generate_gradient_card(
            f"Visual {i + 1}",
            scene_type=scene_type,
            seed=i
        )

        fallback_asset = VisualAsset(
            path=fallback_path,
            title=f"Fallback Visual {i + 1}",
            creator="System",
            license="cc0",
            source_url="",
            attribution=None,
            width=1920,
            height=1080,
            asset_type="image"
        )

        assets.append(fallback_asset)

    return assets