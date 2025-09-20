#!/usr/bin/env python3
"""
Google TTS Alternative (Free)
Uses gTTS (Google Text-to-Speech) which is free
"""

from gtts import gTTS
import os

def generate_google_tts(text, output_file="google_tts_audio.mp3"):
    """Generate TTS using free Google TTS"""
    
    print("Generating audio with Google TTS (free)...")
    
    try:
        # Create TTS object
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to file
        tts.save(output_file)
        
        print(f"[SUCCESS] Audio saved to {output_file}")
        print(f"File size: {os.path.getsize(output_file) / 1024:.1f} KB")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to generate audio: {e}")
        return False

def install_gtts():
    """Install gTTS if not available"""
    try:
        import gtts
        return True
    except ImportError:
        print("Installing gTTS...")
        os.system("pip install gtts")
        return True

if __name__ == "__main__":
    # Install if needed
    if not install_gtts():
        print("Failed to install gTTS")
        exit(1)
    
    # Test with sample text
    test_text = """
    Welcome to this video about passive income ideas that actually work in 2025.
    In the next few minutes, I'll show you proven methods to generate income while you sleep.
    """
    
    if generate_google_tts(test_text, "test_google_tts.mp3"):
        print("\nGoogle TTS is working!")
        print("You can use this as an alternative to ElevenLabs")