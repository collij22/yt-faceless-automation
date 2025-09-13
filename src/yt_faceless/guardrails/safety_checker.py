"""Brand safety and content moderation system."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..core.config import AppConfig
from ..core.schemas import BrandSafetyCheck
from ..integrations.n8n_client import N8NClient
from ..logging_setup import get_logger

logger = get_logger(__name__)


class BrandSafetyChecker:
    """Checks content for brand safety and compliance."""

    def __init__(self, config: AppConfig):
        """Initialize brand safety checker.

        Args:
            config: Application configuration
        """
        self.config = config
        self.n8n_client = N8NClient(config)
        self.data_dir = config.directories.data_dir / "guardrails"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.rules_file = self.data_dir / "safety_rules.json"
        self.violations_file = self.data_dir / "violations.json"

        self.rules = self._load_safety_rules()
        self.violations_history = self._load_violations_history()

    def _load_safety_rules(self) -> Dict[str, Any]:
        """Load brand safety rules."""
        if not self.rules_file.exists():
            # Create default rules
            default_rules = {
                "prohibited_terms": {
                    "violence": ["kill", "murder", "assault", "weapon", "gun", "bomb"],
                    "adult": ["explicit", "nsfw", "adult", "nude"],
                    "hate": ["racist", "sexist", "discriminate", "hate"],
                    "medical": ["cure", "treatment", "diagnosis", "covid", "vaccine"],
                    "financial": ["guaranteed return", "get rich quick", "mlm", "pyramid"],
                    "copyright": ["copyrighted", "dmca", "trademark", "®", "™"]
                },
                "sensitive_topics": [
                    "politics",
                    "religion",
                    "controversial",
                    "tragedy",
                    "disaster",
                    "death"
                ],
                "required_disclosures": {
                    "affiliate": ["affiliate", "commission", "partner"],
                    "sponsored": ["sponsored", "paid", "promotion", "ad"],
                    "medical": ["not medical advice", "consult doctor", "educational"],
                    "financial": ["not financial advice", "do your research", "risk"]
                },
                "platform_policies": {
                    "youtube": {
                        "max_title_length": 100,
                        "max_description_length": 5000,
                        "max_tags": 500,
                        "prohibited_in_title": ["click here", "subscribe", "like"],
                        "requires_age_gate": ["alcohol", "tobacco", "gambling"]
                    },
                    "tiktok": {
                        "max_caption_length": 2200,
                        "max_hashtags": 100,
                        "prohibited_hashtags": ["follow4follow", "like4like"],
                        "music_copyright_check": True
                    },
                    "instagram": {
                        "max_caption_length": 2200,
                        "max_hashtags": 30,
                        "prohibited_hashtags": ["tag4tag", "instatag"],
                        "requires_branded_content_tag": ["ad", "sponsored"]
                    }
                },
                "advertiser_friendly": {
                    "avoid_terms": ["controversial", "shocking", "disturbing"],
                    "avoid_topics": ["tragedy", "natural disaster", "sensitive events"],
                    "requires_context": ["news", "documentary", "educational"]
                },
                "legal_compliance": {
                    "ftc_disclosure_required": ["affiliate", "sponsored", "gifted"],
                    "coppa_compliance": ["kids", "children", "toys"],
                    "gdpr_compliance": ["data", "personal information", "tracking"]
                }
            }
            self.rules_file.write_text(json.dumps(default_rules, indent=2))
            logger.info(f"Created default safety rules at {self.rules_file}")

        with open(self.rules_file, 'r') as f:
            return json.load(f)

    def _load_violations_history(self) -> List[Dict[str, Any]]:
        """Load violations history."""
        if not self.violations_file.exists():
            return []

        with open(self.violations_file, 'r') as f:
            return json.load(f)

    def _save_violations_history(self) -> None:
        """Save violations history."""
        with open(self.violations_file, 'w') as f:
            json.dump(self.violations_history, f, indent=2)

    def check_prohibited_terms(
        self,
        text: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Check text for prohibited terms.

        Args:
            text: Text to check
            category: Optional specific category to check

        Returns:
            List of violations found
        """
        violations = []
        text_lower = text.lower()

        categories = [category] if category else self.rules.get("prohibited_terms", {}).keys()

        for cat in categories:
            terms = self.rules.get("prohibited_terms", {}).get(cat, [])
            for term in terms:
                if term.lower() in text_lower:
                    violations.append({
                        "type": "prohibited_term",
                        "category": cat,
                        "term": term,
                        "severity": "high"
                    })

        return violations

    def check_sensitive_topics(self, text: str) -> List[Dict[str, Any]]:
        """Check for sensitive topics.

        Args:
            text: Text to check

        Returns:
            List of sensitive topics found
        """
        violations = []
        text_lower = text.lower()

        for topic in self.rules.get("sensitive_topics", []):
            if topic.lower() in text_lower:
                violations.append({
                    "type": "sensitive_topic",
                    "topic": topic,
                    "severity": "medium"
                })

        return violations

    def check_required_disclosures(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for required disclosures.

        Args:
            text: Text to check
            context: Context information (e.g., has_affiliates, is_sponsored)

        Returns:
            List of missing disclosures
        """
        violations = []
        text_lower = text.lower()

        disclosures = self.rules.get("required_disclosures", {})

        # Check affiliate disclosure
        if context.get("has_affiliates") and not any(
            term in text_lower for term in disclosures.get("affiliate", [])
        ):
            violations.append({
                "type": "missing_disclosure",
                "category": "affiliate",
                "severity": "high",
                "required_terms": disclosures.get("affiliate", [])
            })

        # Check sponsorship disclosure
        if context.get("is_sponsored") and not any(
            term in text_lower for term in disclosures.get("sponsored", [])
        ):
            violations.append({
                "type": "missing_disclosure",
                "category": "sponsored",
                "severity": "high",
                "required_terms": disclosures.get("sponsored", [])
            })

        # Check medical disclaimer
        medical_triggers = ["health", "medical", "treatment", "cure", "symptom"]
        if any(trigger in text_lower for trigger in medical_triggers):
            if not any(term in text_lower for term in disclosures.get("medical", [])):
                violations.append({
                    "type": "missing_disclosure",
                    "category": "medical",
                    "severity": "medium",
                    "required_terms": disclosures.get("medical", [])
                })

        # Check financial disclaimer
        financial_triggers = ["invest", "trading", "stock", "crypto", "profit"]
        if any(trigger in text_lower for trigger in financial_triggers):
            if not any(term in text_lower for term in disclosures.get("financial", [])):
                violations.append({
                    "type": "missing_disclosure",
                    "category": "financial",
                    "severity": "medium",
                    "required_terms": disclosures.get("financial", [])
                })

        return violations

    def check_platform_compliance(
        self,
        metadata: Dict[str, Any],
        platform: str
    ) -> List[Dict[str, Any]]:
        """Check platform-specific compliance.

        Args:
            metadata: Video metadata
            platform: Platform name

        Returns:
            List of platform violations
        """
        violations = []
        platform_rules = self.rules.get("platform_policies", {}).get(platform, {})

        if not platform_rules:
            return violations

        # Check title
        title = metadata.get("title", "")
        if len(title) > platform_rules.get("max_title_length", 1000):
            violations.append({
                "type": "platform_violation",
                "platform": platform,
                "field": "title",
                "issue": "exceeds_length",
                "severity": "high"
            })

        # Check for prohibited terms in title
        for term in platform_rules.get("prohibited_in_title", []):
            if term.lower() in title.lower():
                violations.append({
                    "type": "platform_violation",
                    "platform": platform,
                    "field": "title",
                    "issue": f"prohibited_term: {term}",
                    "severity": "medium"
                })

        # Check description
        desc = metadata.get("description", "")
        if isinstance(desc, dict):
            desc = desc.get("text", "")
        if len(desc) > platform_rules.get("max_description_length", 10000):
            violations.append({
                "type": "platform_violation",
                "platform": platform,
                "field": "description",
                "issue": "exceeds_length",
                "severity": "medium"
            })

        # Check tags
        tags = metadata.get("tags", [])
        if isinstance(tags, dict):
            tags = tags.get("primary", []) + tags.get("competitive", [])

        total_tag_chars = sum(len(tag) for tag in tags)
        if total_tag_chars > platform_rules.get("max_tags", 500):
            violations.append({
                "type": "platform_violation",
                "platform": platform,
                "field": "tags",
                "issue": "exceeds_character_limit",
                "severity": "low"
            })

        # Check for age-gated content
        for term in platform_rules.get("requires_age_gate", []):
            if term.lower() in title.lower() or term.lower() in desc.lower():
                violations.append({
                    "type": "platform_violation",
                    "platform": platform,
                    "issue": f"requires_age_gate: {term}",
                    "severity": "medium"
                })

        return violations

    def check_advertiser_friendly(
        self,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if content is advertiser-friendly.

        Args:
            metadata: Video metadata

        Returns:
            Advertiser-friendliness assessment
        """
        score = 100  # Start with perfect score
        issues = []

        title = metadata.get("title", "")
        desc = metadata.get("description", "")
        if isinstance(desc, dict):
            desc = desc.get("text", "")

        full_text = f"{title} {desc}".lower()

        # Check for terms to avoid
        for term in self.rules.get("advertiser_friendly", {}).get("avoid_terms", []):
            if term.lower() in full_text:
                score -= 20
                issues.append(f"Contains term: {term}")

        # Check for topics to avoid
        for topic in self.rules.get("advertiser_friendly", {}).get("avoid_topics", []):
            if topic.lower() in full_text:
                score -= 25
                issues.append(f"Contains topic: {topic}")

        # Check if context is provided for sensitive content
        requires_context = self.rules.get("advertiser_friendly", {}).get("requires_context", [])
        for term in requires_context:
            if term.lower() in full_text:
                # Check if educational/documentary context is provided
                context_terms = ["educational", "documentary", "explained", "history", "science"]
                if not any(ctx in full_text for ctx in context_terms):
                    score -= 15
                    issues.append(f"Lacks context for: {term}")

        return {
            "score": max(0, score),
            "rating": "green" if score >= 80 else "yellow" if score >= 50 else "limited",
            "issues": issues,
            "advertiser_friendly": score >= 50
        }

    def validate_legal_compliance(
        self,
        metadata: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate legal compliance requirements.

        Args:
            metadata: Video metadata
            context: Context information

        Returns:
            List of compliance violations
        """
        violations = []
        legal_rules = self.rules.get("legal_compliance", {})

        desc = metadata.get("description", "")
        if isinstance(desc, dict):
            desc = desc.get("text", "")

        # FTC disclosure check
        ftc_triggers = legal_rules.get("ftc_disclosure_required", [])
        for trigger in ftc_triggers:
            if trigger in desc.lower() or context.get(f"has_{trigger}"):
                # Check for proper disclosure
                if not any(word in desc.lower() for word in ["disclosure", "sponsored", "ad", "paid"]):
                    violations.append({
                        "type": "legal_compliance",
                        "law": "FTC",
                        "issue": f"Missing disclosure for {trigger}",
                        "severity": "high"
                    })

        # COPPA compliance check
        coppa_triggers = legal_rules.get("coppa_compliance", [])
        for trigger in coppa_triggers:
            if trigger in metadata.get("title", "").lower() or trigger in desc.lower():
                violations.append({
                    "type": "legal_compliance",
                    "law": "COPPA",
                    "issue": f"Content targets children: {trigger}",
                    "severity": "high",
                    "recommendation": "Mark as 'Made for Kids' on YouTube"
                })

        # GDPR compliance check
        gdpr_triggers = legal_rules.get("gdpr_compliance", [])
        for trigger in gdpr_triggers:
            if trigger in desc.lower():
                if "privacy policy" not in desc.lower():
                    violations.append({
                        "type": "legal_compliance",
                        "law": "GDPR",
                        "issue": f"Mentions {trigger} without privacy policy",
                        "severity": "medium"
                    })

        return violations

    async def run_ai_moderation(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run AI-powered content moderation.

        Args:
            content: Content to moderate

        Returns:
            Moderation results
        """
        if not getattr(self.config.webhooks, "moderation_url", None):
            logger.warning("Moderation webhook not configured")
            return {"status": "skipped", "reason": "no_webhook"}

        try:
            response = await self.n8n_client.execute_webhook(
                self.config.webhooks.moderation_url,
                content,
                timeout=30
            )

            return response

        except Exception as e:
            logger.error(f"AI moderation failed: {e}")
            return {"status": "failed", "error": str(e)}

    def generate_safety_report(
        self,
        check_result: BrandSafetyCheck
    ) -> Dict[str, Any]:
        """Generate comprehensive safety report.

        Args:
            check_result: Brand safety check result

        Returns:
            Safety report
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "slug": check_result.slug,
            "overall_status": "pass" if check_result.passed else "fail",
            "checks_performed": check_result.checks_performed,
            "violations": check_result.violations,
            "warnings": check_result.warnings,
            "score": check_result.score,
            "recommendations": []
        }

        # Add recommendations based on violations
        for violation in check_result.violations:
            if violation["type"] == "prohibited_term":
                report["recommendations"].append(
                    f"Remove or replace the term '{violation.get('term', 'unknown')}'"
                )
            elif violation["type"] == "missing_disclosure":
                report["recommendations"].append(
                    f"Add {violation['category']} disclosure using terms like: {', '.join(violation.get('required_terms', []))}"
                )
            elif violation["type"] == "platform_violation":
                report["recommendations"].append(
                    f"Fix {violation['platform']} issue in {violation.get('field', 'content')}: {violation.get('issue', 'unknown')}"
                )

        # Log to history
        self.violations_history.append(report)
        self._save_violations_history()

        return report


async def check_content_safety(
    config: AppConfig,
    slug: str,
    platforms: Optional[List[str]] = None,
    run_ai_check: bool = False,
    dry_run: bool = False
) -> BrandSafetyCheck:
    """Check content for brand safety and compliance.

    Args:
        config: Application configuration
        slug: Video slug
        platforms: Platforms to check compliance for
        run_ai_check: Whether to run AI moderation
        dry_run: Simulate without checking

    Returns:
        Brand safety check result
    """
    enabled = config.features.get("brand_safety") if "brand_safety" in config.features else True
    if not enabled:
        logger.info("Brand safety feature is disabled")
        return BrandSafetyCheck(
            slug=slug,
            passed=True,
            checks_performed=[],
            violations=[],
            warnings=[],
            score=100
        )

    checker = BrandSafetyChecker(config)

    # Load content
    content_dir = config.directories.content_dir / slug
    metadata_path = content_dir / "metadata.json"

    if not metadata_path.exists():
        logger.error(f"Metadata not found: {metadata_path}")
        return BrandSafetyCheck(
            slug=slug,
            passed=False,
            checks_performed=["metadata_exists"],
            violations=[{"type": "missing_metadata", "severity": "high"}],
            warnings=[],
            score=0
        )

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    # Extract text content
    title = metadata.get("title", "")
    desc = metadata.get("description", "")
    if isinstance(desc, dict):
        desc = desc.get("text", "")

    full_text = f"{title} {desc}"

    # Build context
    context = {
        "has_affiliates": bool(metadata.get("monetization_settings", {}).get("affiliate_links")),
        "is_sponsored": bool(metadata.get("monetization_settings", {}).get("sponsorship_disclosure")),
        "niche": metadata.get("niche")
    }

    violations = []
    warnings = []
    checks_performed = []

    if not dry_run:
        # Check prohibited terms
        checks_performed.append("prohibited_terms")
        term_violations = checker.check_prohibited_terms(full_text)
        violations.extend(term_violations)

        # Check sensitive topics
        checks_performed.append("sensitive_topics")
        topic_warnings = checker.check_sensitive_topics(full_text)
        warnings.extend(topic_warnings)

        # Check required disclosures
        checks_performed.append("required_disclosures")
        disclosure_violations = checker.check_required_disclosures(desc, context)
        violations.extend(disclosure_violations)

        # Check platform compliance
        if platforms:
            for platform in platforms:
                checks_performed.append(f"platform_{platform}")
                platform_violations = checker.check_platform_compliance(metadata, platform)
                violations.extend(platform_violations)

        # Check advertiser friendliness
        checks_performed.append("advertiser_friendly")
        ad_friendly = checker.check_advertiser_friendly(metadata)
        if not ad_friendly["advertiser_friendly"]:
            warnings.append({
                "type": "advertiser_unfriendly",
                "score": ad_friendly["score"],
                "issues": ad_friendly["issues"]
            })

        # Check legal compliance
        checks_performed.append("legal_compliance")
        legal_violations = checker.validate_legal_compliance(metadata, context)
        violations.extend(legal_violations)

        # Run AI moderation if requested
        if run_ai_check:
            checks_performed.append("ai_moderation")
            ai_result = await checker.run_ai_moderation({
                "title": title,
                "description": desc,
                "tags": metadata.get("tags", [])
            })
            if ai_result.get("violations"):
                violations.extend(ai_result["violations"])

    # Calculate score
    score = 100
    for violation in violations:
        if violation.get("severity") == "high":
            score -= 20
        elif violation.get("severity") == "medium":
            score -= 10
        else:
            score -= 5

    for warning in warnings:
        score -= 5

    score = max(0, score)

    result = BrandSafetyCheck(
        slug=slug,
        passed=score >= 70 and not any(v.get("severity") == "high" for v in violations),
        checks_performed=checks_performed,
        violations=violations,
        warnings=warnings,
        score=score
    )

    # Generate report
    if not dry_run:
        report = checker.generate_safety_report(result)
        logger.info(f"Safety check for {slug}: {'PASS' if result.passed else 'FAIL'} (score: {score})")

    return result


async def validate_compliance(
    config: AppConfig,
    slug: str,
    fix_issues: bool = False
) -> Dict[str, Any]:
    """Validate and optionally fix compliance issues.

    Args:
        config: Application configuration
        slug: Video slug
        fix_issues: Whether to attempt fixing issues

    Returns:
        Validation results
    """
    # Run safety check
    check_result = await check_content_safety(
        config,
        slug,
        platforms=["youtube", "tiktok", "instagram"]
    )

    if not check_result.passed and fix_issues:
        # Attempt to fix issues
        content_dir = config.directories.content_dir / slug
        metadata_path = content_dir / "metadata.json"

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        fixed_count = 0

        for violation in check_result.violations:
            if violation["type"] == "missing_disclosure":
                # Add required disclosure
                desc = metadata.get("description", "")
                if isinstance(desc, dict):
                    desc_text = desc.get("text", "")
                else:
                    desc_text = str(desc)

                # Add disclosure based on category
                if violation["category"] == "affiliate":
                    desc_text = "This video contains affiliate links; we may earn a commission.\n\n" + desc_text
                elif violation["category"] == "sponsored":
                    desc_text = "This video contains paid promotion.\n\n" + desc_text

                if isinstance(metadata.get("description"), dict):
                    metadata["description"]["text"] = desc_text
                else:
                    metadata["description"] = desc_text

                fixed_count += 1

        if fixed_count > 0:
            # Save fixed metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Fixed {fixed_count} compliance issues for {slug}")

            # Re-run check
            check_result = await check_content_safety(config, slug)

    return {
        "passed": check_result.passed,
        "score": check_result.score,
        "violations": check_result.violations,
        "warnings": check_result.warnings,
        "fixed": fix_issues and fixed_count > 0
    }