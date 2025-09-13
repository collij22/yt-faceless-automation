"""Monetization module for affiliate links, sponsorships, and revenue tracking."""

from .affiliates import AffiliateManager, inject_affiliate_links
from .sponsorships import SponsorshipManager, apply_sponsorship_disclosure
from .revenue import RevenueTracker, generate_revenue_report

__all__ = [
    'AffiliateManager',
    'inject_affiliate_links',
    'SponsorshipManager',
    'apply_sponsorship_disclosure',
    'RevenueTracker',
    'generate_revenue_report',
]