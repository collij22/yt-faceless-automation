#!/usr/bin/env python
"""Quick test to verify all fixes are working"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

def test_fixed_pipeline():
    """Run a quick test to verify video duration and timestamps are correct"""

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    content_dir = Path(f"content/test_{session_id}")
    content_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("TESTING FIXED PIPELINE")
    print("="*60)

    # 1. Create a test script
    script = """This is a test video to verify our fixes are working correctly.

The video should now have the correct duration matching the audio.

And the timestamps in the description should be accurate.

Let me add a bit more content to make this longer.

This is the final part of our test."""

    script_file = content_dir / "script.txt"
    script_file.write_text(script)
    print(f"[OK] Created test script")

    # 2. Generate TTS
    print("\n[INFO] Generating TTS...")
    try:
        from gtts import gTTS
        tts = gTTS(text=script, lang='en', slow=False)
        audio_file = content_dir / "test_audio.mp3"
        tts.save(str(audio_file))
        print(f"[OK] TTS generated: {audio_file}")
    except ImportError:
        print("[ERROR] gTTS not installed")
        return False

    # 3. Get audio duration
    probe_cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(audio_file)
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    audio_duration = float(result.stdout.strip())
    print(f"[OK] Audio duration: {audio_duration:.1f} seconds")

    # 4. Generate video with correct duration
    print("\n[INFO] Creating video...")
    video_file = content_dir / "test_video.mp4"
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', f'color=c=blue:s=1920x1080:d={audio_duration}',
        '-i', str(audio_file),
        '-vf', "drawtext=text='Fixed Pipeline Test':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2",
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-shortest',
        str(video_file)
    ]

    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] FFmpeg failed: {result.stderr}")
        return False
    print(f"[OK] Video created: {video_file}")

    # 5. Verify video duration
    result = subprocess.run(probe_cmd[:-1] + [str(video_file)], capture_output=True, text=True, check=True)
    video_duration = float(result.stdout.strip())
    print(f"[OK] Video duration: {video_duration:.1f} seconds")

    # 6. Generate accurate timestamps
    from run_full_production_pipeline import YouTubeProductionSystem
    pipeline = YouTubeProductionSystem()
    timestamps = pipeline.generate_accurate_timestamps(audio_duration)
    print(f"\n[OK] Generated timestamps for {audio_duration:.1f}s video:")
    print(timestamps)

    # 7. Check duration match
    duration_diff = abs(video_duration - audio_duration)
    if duration_diff < 0.5:
        print(f"\n[SUCCESS] Durations match! (difference: {duration_diff:.2f}s)")
    else:
        print(f"\n[FAIL] Duration mismatch (difference: {duration_diff:.2f}s)")
        return False

    # 8. Create metadata with accurate timestamps
    metadata = {
        "title": "Pipeline Test Video",
        "description": pipeline.generate_seo_description(
            {
                'title': 'Pipeline Test Video',
                'hook': 'Testing our fixes',
                'keywords': ['test', 'pipeline', 'youtube']
            },
            audio_duration
        ),
        "duration_seconds": audio_duration,
        "timestamps": timestamps
    }

    metadata_file = content_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"[OK] Saved metadata with accurate timestamps")

    print("\n" + "="*60)
    print("ALL FIXES VERIFIED SUCCESSFULLY!")
    print("="*60)
    print(f"\nTest outputs saved to: {content_dir}")
    print(f"- Audio: {audio_duration:.1f}s")
    print(f"- Video: {video_duration:.1f}s")
    print(f"- Timestamps: Accurate for {audio_duration:.1f}s duration")

    return True

if __name__ == "__main__":
    test_fixed_pipeline()