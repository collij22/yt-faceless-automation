"""License validation and attribution utilities."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class LicenseValidator:
    """Validates and manages content licenses."""

    # Licenses safe for commercial use
    COMMERCIAL_SAFE = {
        "cc0", "cc-0", "cc0-1.0",  # Creative Commons Zero
        "pd", "pdm", "publicdomain", "public-domain",  # Public Domain
        "cc-by", "cc-by-1.0", "cc-by-2.0", "cc-by-2.5", "cc-by-3.0", "cc-by-4.0",  # Attribution
        "cc-by-sa", "cc-by-sa-1.0", "cc-by-sa-2.0", "cc-by-sa-2.5", "cc-by-sa-3.0", "cc-by-sa-4.0",  # ShareAlike
    }

    # Licenses that require attribution
    ATTRIBUTION_REQUIRED = {
        "cc-by", "cc-by-1.0", "cc-by-2.0", "cc-by-2.5", "cc-by-3.0", "cc-by-4.0",
        "cc-by-sa", "cc-by-sa-1.0", "cc-by-sa-2.0", "cc-by-sa-2.5", "cc-by-sa-3.0", "cc-by-sa-4.0",
    }

    # ShareAlike licenses (viral - output must use same license)
    SHAREALIKE = {
        "cc-by-sa", "cc-by-sa-1.0", "cc-by-sa-2.0", "cc-by-sa-2.5", "cc-by-sa-3.0", "cc-by-sa-4.0",
    }

    # Non-commercial licenses (NOT safe for monetized content)
    NON_COMMERCIAL = {
        "cc-by-nc", "cc-by-nc-2.0", "cc-by-nc-3.0", "cc-by-nc-4.0",
        "cc-by-nc-sa", "cc-by-nc-sa-2.0", "cc-by-nc-sa-3.0", "cc-by-nc-sa-4.0",
        "cc-by-nc-nd", "cc-by-nc-nd-2.0", "cc-by-nc-nd-3.0", "cc-by-nc-nd-4.0",
    }

    # No derivatives licenses (cannot modify)
    NO_DERIVATIVES = {
        "cc-by-nd", "cc-by-nd-2.0", "cc-by-nd-3.0", "cc-by-nd-4.0",
        "cc-by-nc-nd", "cc-by-nc-nd-2.0", "cc-by-nc-nd-3.0", "cc-by-nc-nd-4.0",
    }

    @classmethod
    def normalize_license(cls, license_str: str) -> str:
        """Normalize license string to standard format.

        Args:
            license_str: Raw license string

        Returns:
            Normalized license identifier
        """
        if not license_str:
            return "unknown"

        # Convert to lowercase and clean
        normalized = license_str.lower().strip()
        normalized = normalized.replace("_", "-")
        normalized = normalized.replace(" ", "-")
        normalized = normalized.replace("creative-commons", "cc")
        normalized = normalized.replace("creativecommons", "cc")

        # Handle version numbers
        import re
        # Match patterns like "cc by 4.0" or "cc-by 4.0"
        pattern = re.compile(r"(cc-?(?:by|sa|nc|nd)(?:-(?:by|sa|nc|nd))*)\s*(\d+(?:\.\d+)?)?")
        match = pattern.search(normalized)

        if match:
            base = match.group(1).replace(" ", "-")
            version = match.group(2)
            if version:
                return f"{base}-{version}"
            return base

        # Check for public domain variations
        if any(pd in normalized for pd in ["public domain", "publicdomain", "pd mark", "pdm", "no copyright"]):
            return "pd"

        if "cc0" in normalized or "zero" in normalized:
            return "cc0"

        return normalized[:50]  # Limit length

    @classmethod
    def is_commercial_safe(cls, license_str: str) -> bool:
        """Check if license allows commercial use.

        Args:
            license_str: License identifier

        Returns:
            True if commercial use is allowed
        """
        normalized = cls.normalize_license(license_str)

        # Check if explicitly non-commercial
        if any(nc in normalized for nc in ["nc", "non-commercial", "noncommercial"]):
            return False

        # Check if in commercial safe list
        for safe in cls.COMMERCIAL_SAFE:
            if safe in normalized or normalized in safe:
                return True

        # Unknown licenses are not safe
        logger.warning(f"Unknown license for commercial use: {normalized}")
        return False

    @classmethod
    def requires_attribution(cls, license_str: str) -> bool:
        """Check if license requires attribution.

        Args:
            license_str: License identifier

        Returns:
            True if attribution is required
        """
        normalized = cls.normalize_license(license_str)

        for attr_license in cls.ATTRIBUTION_REQUIRED:
            if attr_license in normalized or normalized in attr_license:
                return True

        return False

    @classmethod
    def is_sharealike(cls, license_str: str) -> bool:
        """Check if license has ShareAlike requirement.

        Args:
            license_str: License identifier

        Returns:
            True if ShareAlike is required
        """
        normalized = cls.normalize_license(license_str)

        return any(sa in normalized for sa in ["sa", "share-alike", "sharealike"])

    @classmethod
    def allows_modification(cls, license_str: str) -> bool:
        """Check if license allows modifications.

        Args:
            license_str: License identifier

        Returns:
            True if modifications are allowed
        """
        normalized = cls.normalize_license(license_str)

        # Check if explicitly no-derivatives
        if any(nd in normalized for nd in ["nd", "no-deriv", "noderivs", "no-derivatives"]):
            return False

        # Most CC licenses allow modification
        if normalized.startswith("cc"):
            return True

        # Public domain allows everything
        if normalized in ["pd", "cc0", "publicdomain"]:
            return True

        # Unknown licenses - be conservative
        return False

    @classmethod
    def get_license_url(cls, license_str: str) -> Optional[str]:
        """Get the official license URL.

        Args:
            license_str: License identifier

        Returns:
            License URL or None
        """
        normalized = cls.normalize_license(license_str)

        # Extract version
        import re
        version_match = re.search(r"(\d+\.\d+)", normalized)
        version = version_match.group(1) if version_match else "4.0"

        # Map to URLs
        if normalized == "cc0" or "cc0" in normalized:
            return "https://creativecommons.org/publicdomain/zero/1.0/"
        elif normalized == "pd" or "public" in normalized:
            return "https://creativecommons.org/publicdomain/mark/1.0/"
        elif "cc-by-sa" in normalized:
            return f"https://creativecommons.org/licenses/by-sa/{version}/"
        elif "cc-by-nc-sa" in normalized:
            return f"https://creativecommons.org/licenses/by-nc-sa/{version}/"
        elif "cc-by-nc-nd" in normalized:
            return f"https://creativecommons.org/licenses/by-nc-nd/{version}/"
        elif "cc-by-nc" in normalized:
            return f"https://creativecommons.org/licenses/by-nc/{version}/"
        elif "cc-by-nd" in normalized:
            return f"https://creativecommons.org/licenses/by-nd/{version}/"
        elif "cc-by" in normalized:
            return f"https://creativecommons.org/licenses/by/{version}/"

        return None


def format_attribution(
    title: str,
    creator: Optional[str],
    license: str,
    source: str,
    url: Optional[str] = None
) -> str:
    """Format an attribution string according to best practices.

    Args:
        title: Work title
        creator: Creator name
        license: License identifier
        source: Source platform
        url: Source URL

    Returns:
        Formatted attribution string
    """
    parts = []

    # Title
    if title:
        parts.append(f'"{title}"')

    # Creator
    if creator and creator.lower() not in ["unknown", "anonymous"]:
        parts.append(f"by {creator}")

    # Source
    if source:
        parts.append(f"from {source}")

    # License
    normalized_license = LicenseValidator.normalize_license(license)
    license_url = LicenseValidator.get_license_url(normalized_license)

    if normalized_license in ["pd", "cc0"]:
        parts.append("(Public Domain)")
    elif normalized_license != "unknown":
        parts.append(f"licensed under {normalized_license.upper()}")

    # URL
    if url:
        parts.append(f"({url})")
    elif license_url:
        parts.append(f"({license_url})")

    return " ".join(parts)


def generate_attribution_block(
    assets: List[Dict],
    format: str = "markdown"
) -> str:
    """Generate attribution block for multiple assets.

    Args:
        assets: List of asset dictionaries with attribution info
        format: Output format (markdown or plain)

    Returns:
        Formatted attribution block
    """
    if not assets:
        return ""

    # Filter assets that need attribution
    attributed_assets = []
    has_sharealike = False

    for asset in assets:
        license = asset.get("license", "")
        if LicenseValidator.requires_attribution(license):
            attributed_assets.append(asset)
        if LicenseValidator.is_sharealike(license):
            has_sharealike = True

    if not attributed_assets and not has_sharealike:
        return ""

    lines = []

    if format == "markdown":
        lines.append("## Media Attribution")
        lines.append("")

        if has_sharealike:
            lines.append("*This video contains Creative Commons ShareAlike content.*")
            lines.append("")

        lines.append("The following media assets are used under Creative Commons licenses:")
        lines.append("")

        for i, asset in enumerate(attributed_assets, 1):
            attribution = format_attribution(
                asset.get("title", "Untitled"),
                asset.get("creator"),
                asset.get("license", ""),
                asset.get("source", ""),
                asset.get("source_url")
            )
            lines.append(f"{i}. {attribution}")

    else:  # plain text
        lines.append("MEDIA ATTRIBUTION")
        lines.append("=" * 50)

        if has_sharealike:
            lines.append("This video contains Creative Commons ShareAlike content.")
            lines.append("")

        for asset in attributed_assets:
            attribution = format_attribution(
                asset.get("title", "Untitled"),
                asset.get("creator"),
                asset.get("license", ""),
                asset.get("source", ""),
                asset.get("source_url")
            )
            lines.append(f"• {attribution}")

    return "\n".join(lines)


def check_license_compatibility(licenses: List[str]) -> Dict[str, any]:
    """Check if a set of licenses are compatible for use together.

    Args:
        licenses: List of license identifiers

    Returns:
        Dict with compatibility info and recommendations
    """
    result = {
        "compatible": True,
        "commercial_safe": True,
        "requires_attribution": False,
        "requires_sharealike": False,
        "allows_modification": True,
        "warnings": [],
        "recommendations": []
    }

    normalized_licenses = [LicenseValidator.normalize_license(l) for l in licenses]

    # Check each license
    for license in normalized_licenses:
        if not LicenseValidator.is_commercial_safe(license):
            result["commercial_safe"] = False
            result["warnings"].append(f"License '{license}' does not allow commercial use")

        if LicenseValidator.requires_attribution(license):
            result["requires_attribution"] = True

        if LicenseValidator.is_sharealike(license):
            result["requires_sharealike"] = True
            result["recommendations"].append("Output must be licensed under same ShareAlike terms")

        if not LicenseValidator.allows_modification(license):
            result["allows_modification"] = False
            result["warnings"].append(f"License '{license}' does not allow modifications")

    # Check overall compatibility
    if not result["commercial_safe"]:
        result["compatible"] = False
        result["recommendations"].append("Remove non-commercial assets for monetized content")

    if not result["allows_modification"]:
        result["compatible"] = False
        result["recommendations"].append("Cannot use No-Derivatives content in edited videos")

    return result