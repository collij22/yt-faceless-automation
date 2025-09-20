#!/usr/bin/env python3
"""Quick Google TTS Test"""

from gtts import gTTS

# Test with short text
text = "This is a test of Google Text to Speech. It should work as a fallback when ElevenLabs fails."

print("Generating Google TTS audio...")
tts = gTTS(text=text, lang='en', slow=False)
tts.save("google_tts_test.mp3")
print("Success! Audio saved to google_tts_test.mp3")
print("The Google TTS fallback is working!")