#!/usr/bin/env python
"""Test script to verify video duration fix"""

import subprocess
from pathlib import Path
import sys

def test_video_assembly():
    """Test that video matches audio duration"""

    # Use existing audio file
    test_audio = Path("content/20250920_101134/narration.mp3")
    if not test_audio.exists():
        print(f"[ERROR] Test audio not found: {test_audio}")
        return False

    # Get audio duration
    probe_cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(test_audio)
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    audio_duration = float(result.stdout.strip())
    print(f"[INFO] Audio duration: {audio_duration:.2f} seconds")

    # Create test video with fixed duration
    test_output = Path("test_fixed_duration.mp4")

    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', f'color=c=blue:s=1920x1080:d={audio_duration}',
        '-i', str(test_audio),
        '-vf', "drawtext=text='Duration Test Video':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2",
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-shortest',
        str(test_output)
    ]

    print(f"[INFO] Creating video with duration: {audio_duration:.2f}s")
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] FFmpeg failed: {result.stderr}")
        return False

    # Verify output video duration
    result = subprocess.run(probe_cmd[:-1] + [str(test_output)], capture_output=True, text=True, check=True)
    video_duration = float(result.stdout.strip())
    print(f"[INFO] Output video duration: {video_duration:.2f} seconds")

    # Check if durations match (within 0.5 seconds tolerance)
    duration_diff = abs(video_duration - audio_duration)
    if duration_diff < 0.5:
        print(f"[SUCCESS] Video duration matches audio! (difference: {duration_diff:.2f}s)")
        return True
    else:
        print(f"[ERROR] Duration mismatch! Audio: {audio_duration:.2f}s, Video: {video_duration:.2f}s")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("VIDEO DURATION FIX TEST")
    print("="*60)

    if test_video_assembly():
        print("\n[SUCCESS] Fix verified successfully!")
        print("\nNow you can run the full pipeline:")
        print("  python run_full_production_pipeline.py")
        print("\nOr the automated version:")
        print("  python run_automated_pipeline.py")
    else:
        print("\n[FAILED] Fix verification failed")
        sys.exit(1)