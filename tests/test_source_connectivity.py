import os
from pathlib import Path

from yt_faceless.production.asset_sources.openverse import OpenverseSource
from yt_faceless.production.asset_sources.wikimedia import WikimediaSource


def test_openverse_minimal_query():
    src = OpenverseSource(cache_dir=Path('.cache/test'))
    results = src.search('mediterranean longevity', limit=5)
    assert isinstance(results, list)
    # Should not raise and should return 0..5 results
    assert len(results) >= 0


def test_wikimedia_minimal_query():
    src = WikimediaSource(cache_dir=Path('.cache/test'))
    results = src.search('mediterranean diet', limit=5)
    assert isinstance(results, list)
    assert len(results) >= 0

