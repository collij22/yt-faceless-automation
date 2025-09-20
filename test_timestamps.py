#!/usr/bin/env python
"""Test timestamp generation with different video durations"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from run_full_production_pipeline import YouTubeProductionSystem

def test_timestamp_generation():
    """Test timestamp generation for various durations"""

    pipeline = YouTubeProductionSystem()

    test_durations = [
        25,    # Very short
        39,    # Your actual video
        60,    # 1 minute
        120,   # 2 minutes
        180,   # 3 minutes
        240,   # 4 minutes
    ]

    print("TIMESTAMP GENERATION TEST")
    print("="*60)

    for duration in test_durations:
        print(f"\nDuration: {duration} seconds ({duration//60}:{duration%60:02d})")
        print("-"*40)
        timestamps = pipeline.generate_accurate_timestamps(duration)
        print(timestamps)

    # Test with actual audio file if it exists
    test_audio = "content/20250920_101134/narration.mp3"
    if os.path.exists(test_audio):
        print("\n" + "="*60)
        print("ACTUAL AUDIO FILE TEST")
        print("="*60)

        import subprocess
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            test_audio
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        actual_duration = float(result.stdout.strip())

        print(f"\nActual audio duration: {actual_duration:.1f} seconds")
        print("-"*40)
        timestamps = pipeline.generate_accurate_timestamps(actual_duration)
        print(timestamps)

        # Generate full description
        idea = {
            'title': 'Test Video Title',
            'hook': 'This is a test hook',
            'keywords': ['test', 'video', 'timestamps', 'youtube', 'automation']
        }

        print("\n" + "="*60)
        print("FULL DESCRIPTION WITH TIMESTAMPS")
        print("="*60)
        description = pipeline.generate_seo_description(idea, actual_duration)
        print(description)

if __name__ == "__main__":
    test_timestamp_generation()