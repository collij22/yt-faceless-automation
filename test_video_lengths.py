#!/usr/bin/env python
"""Test video generation with different target lengths"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from run_full_production_pipeline import YouTubeProductionSystem

def test_video_lengths():
    """Test script generation and video creation with different target lengths"""

    pipeline = YouTubeProductionSystem()

    # Test idea
    test_idea = {
        'title': '5 Mind-Blowing Facts About Space',
        'hook': 'What NASA doesn\'t want you to know',
        'keywords': ['space', 'nasa', 'astronomy', 'facts', 'science']
    }

    # Test different video lengths
    length_configs = [
        {"minutes": 1, "name": "short", "words": 150},
        {"minutes": 5, "name": "medium", "words": 750},
        {"minutes": 10, "name": "long", "words": 1500},
    ]

    print("\n" + "="*60)
    print("TESTING VIDEO LENGTH GENERATION")
    print("="*60)

    for config in length_configs:
        print(f"\n{'='*60}")
        print(f"Testing {config['minutes']} minute video")
        print("="*60)

        # Add target length to idea
        test_idea['target_length'] = config

        # Get time reference
        time_ref = pipeline.get_time_reference(config['minutes'])
        print(f"Time reference: '{time_ref}'")

        # Generate script
        script = pipeline.generate_high_retention_script(test_idea)

        # Count words in script
        word_count = len(script.split())
        print(f"Script word count: {word_count} (target: {config['words']})")

        # Check if time reference is correctly used
        if time_ref in script:
            print(f"[OK] Time reference '{time_ref}' found in script")
        else:
            print(f"[FAIL] Time reference '{time_ref}' NOT found in script")

        # Show script preview
        print("\nScript preview (first 300 chars):")
        print("-"*40)
        print(script[:300] + "...")

        # Test TTS generation for 1 minute version
        if config['minutes'] == 1:
            print("\nGenerating TTS for 1-minute script...")
            try:
                from gtts import gTTS
                # Clean script for TTS
                clean_script = pipeline.clean_script_for_tts(script)
                tts = gTTS(text=clean_script[:500], lang='en', slow=False)
                test_audio = f"test_{config['name']}_audio.mp3"
                tts.save(test_audio)

                # Get duration
                probe_cmd = [
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    test_audio
                ]
                result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
                duration = float(result.stdout.strip())
                print(f"Audio duration: {duration:.1f} seconds (target: {config['minutes']*60})")

                # Generate accurate timestamps
                timestamps = pipeline.generate_accurate_timestamps(duration)
                print(f"\nGenerated timestamps:")
                print(timestamps)

            except Exception as e:
                print(f"TTS test failed: {e}")

    print("\n" + "="*60)
    print("VIDEO LENGTH TESTING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_video_lengths()