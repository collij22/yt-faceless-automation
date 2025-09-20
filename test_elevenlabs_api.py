#!/usr/bin/env python3
"""
Test ElevenLabs API Configuration
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_elevenlabs():
    """Test ElevenLabs API key and configuration"""
    
    api_key = os.getenv('ELEVENLABS_API_KEY', '')
    voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')
    
    print("="*60)
    print("ELEVENLABS API TEST")
    print("="*60)
    
    if not api_key:
        print("[ERROR] ELEVENLABS_API_KEY not found in .env file")
        return False
    
    # Mask the API key for display
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
    print(f"API Key: {masked_key}")
    print(f"Voice ID: {voice_id}")
    
    # Test 1: Check API key validity
    print("\n[1/3] Testing API key validity...")
    headers = {
        "xi-api-key": api_key
    }
    
    try:
        # Get user info
        response = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers=headers
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"[SUCCESS] API key is valid")
            print(f"Subscription: {user_data.get('subscription', {}).get('tier', 'Unknown')}")
            
            # Check character limit
            char_count = user_data.get('subscription', {}).get('character_count', 0)
            char_limit = user_data.get('subscription', {}).get('character_limit', 0)
            print(f"Characters used: {char_count:,} / {char_limit:,}")
            
            if char_count >= char_limit:
                print("[WARNING] Character limit reached! TTS will fail.")
                return False
                
        elif response.status_code == 401:
            print("[ERROR] Invalid API key (401 Unauthorized)")
            print("\nTo fix this:")
            print("1. Go to https://elevenlabs.io/")
            print("2. Sign in to your account")
            print("3. Click your profile → Profile + API Key")
            print("4. Copy your API key")
            print("5. Update ELEVENLABS_API_KEY in .env file")
            return False
        else:
            print(f"[ERROR] API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False
    
    # Test 2: Check available voices
    print("\n[2/3] Checking available voices...")
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers=headers
        )
        
        if response.status_code == 200:
            voices = response.json().get('voices', [])
            print(f"[SUCCESS] Found {len(voices)} voices")
            
            # Check if specified voice exists
            voice_found = False
            for voice in voices[:5]:  # Show first 5
                print(f"  - {voice['name']} (ID: {voice['voice_id'][:20]}...)")
                if voice['voice_id'] == voice_id:
                    voice_found = True
            
            if not voice_found and voice_id != 'EXAVITQu4vr4xnSDxMaL':
                print(f"\n[WARNING] Voice ID {voice_id} not found in your voices")
                print("Using default voice instead")
        else:
            print(f"[ERROR] Could not fetch voices: {response.status_code}")
            
    except Exception as e:
        print(f"[ERROR] Failed to fetch voices: {e}")
    
    # Test 3: Generate sample audio
    print("\n[3/3] Testing audio generation...")
    test_text = "Test."  # Very short text to minimize credit usage
    
    # Use a premade voice if custom voice not found
    test_voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel (premade voice)
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{test_voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": test_text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Save test audio
            with open("test_audio.mp3", "wb") as f:
                f.write(response.content)
            print("[SUCCESS] Test audio generated: test_audio.mp3")
            print("\n✅ ElevenLabs API is working correctly!")
            return True
            
        elif response.status_code == 401:
            print("[ERROR] Authentication failed during audio generation")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Raw response: {response.text[:500]}")
            return False
        elif response.status_code == 422:
            print("[ERROR] Character limit exceeded or invalid parameters")
            return False
        else:
            print(f"[ERROR] Audio generation failed: {response.status_code}")
            error_msg = response.json() if response.text else "No error message"
            print(f"Error: {error_msg}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to generate audio: {e}")
        return False

def check_env_file():
    """Check .env file configuration"""
    print("\n" + "="*60)
    print("CHECKING .ENV FILE")
    print("="*60)
    
    if not os.path.exists('.env'):
        print("[ERROR] .env file not found!")
        print("\nCreate .env file with:")
        print("ELEVENLABS_API_KEY=your_api_key_here")
        print("ELEVENLABS_VOICE_ID=voice_id_here (optional)")
        return False
    
    with open('.env', 'r') as f:
        content = f.read()
    
    if 'ELEVENLABS_API_KEY' not in content:
        print("[ERROR] ELEVENLABS_API_KEY not in .env file")
        print("\nAdd to .env:")
        print("ELEVENLABS_API_KEY=your_api_key_here")
        return False
    
    # Check if it's still the placeholder
    if 'your_elevenlabs_api_key_here' in content or 'your-elevenlabs-api-key' in content:
        print("[WARNING] ELEVENLABS_API_KEY appears to be a placeholder")
        print("\nGet your API key from:")
        print("https://elevenlabs.io/ → Profile → API Key")
        return False
    
    print("[OK] .env file configured")
    return True

def main():
    # Check .env first
    if not check_env_file():
        return
    
    # Test API
    if test_elevenlabs():
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("1. Your ElevenLabs API is working!")
        print("2. Run the production pipeline again:")
        print("   python run_full_production_pipeline.py")
        print("3. The TTS will now generate real audio")
    else:
        print("\n" + "="*60)
        print("TROUBLESHOOTING")
        print("="*60)
        print("1. Check your API key at https://elevenlabs.io/")
        print("2. Make sure you have characters remaining")
        print("3. Update .env with the correct key")
        print("4. Run this test again")

if __name__ == "__main__":
    main()