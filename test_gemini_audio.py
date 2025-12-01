import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv('backend/.env')

# Test different Gemini endpoints for audio
api_key = os.getenv("GEMINI_API_KEY")

# Create a small test audio file (you can replace this with an actual audio file)
test_audio_file = "test_audio.ogg"  # You'll need to provide this

if not os.path.exists(test_audio_file):
    print("Please provide a test audio file named 'test_audio.ogg'")
    exit(1)

with open(test_audio_file, 'rb') as f:
    audio_data = base64.standard_b64encode(f.read()).decode('utf-8')

# Try different endpoints
endpoints = [
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
]

payload = {
    "contents": [{
        "parts": [
            {
                "inline_data": {
                    "mime_type": "audio/ogg",
                    "data": audio_data
                }
            },
            {
                "text": "Transcribe this audio. Only return the transcribed text."
            }
        ]
    }]
}

for endpoint in endpoints:
    url = f"{endpoint}?key={api_key}"
    print(f"\nTrying: {endpoint}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS! Response: {result}")
            transcription = result['candidates'][0]['content']['parts'][0]['text']
            print(f"Transcription: {transcription}")
            break
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
