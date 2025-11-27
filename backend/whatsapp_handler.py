import os
import requests
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from typing import Dict
from rag_engine import RAGEngine
import logging
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppHandler:
    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine
        self.recognizer = sr.Recognizer()
    
    def download_audio(self, media_url: str, auth: tuple) -> str:
        """Download audio file from Twilio."""
        try:
            response = requests.get(media_url, auth=auth)
            response.raise_for_status()
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ogg')
            temp_file.write(response.content)
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            raise
    
    def convert_audio_format(self, input_file: str) -> str:
        """Convert audio to WAV format for speech recognition."""
        try:
            # Load audio file
            audio = AudioSegment.from_file(input_file)
            
            # Convert to WAV
            wav_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            audio.export(wav_file.name, format='wav')
            
            return wav_file.name
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            raise
    
    def transcribe_audio(self, audio_file: str) -> str:
        """Transcribe audio to text using Google Speech Recognition."""
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                logger.info(f"Transcribed text: {text}")
                return text
        except sr.UnknownValueError:
            logger.error("Could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return ""
    
    def generate_voice_response(self, text: str) -> str:
        """Convert text to speech and return file path."""
        try:
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(temp_file.name)
            
            return temp_file.name
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            raise
    
    def process_voice_message(self, media_url: str, auth: tuple) -> Dict[str, str]:
        """Process incoming voice message and generate response."""
        audio_file = None
        wav_file = None
        
        try:
            # Download audio
            logger.info("Downloading audio...")
            audio_file = self.download_audio(media_url, auth)
            
            # Convert to WAV
            logger.info("Converting audio format...")
            wav_file = self.convert_audio_format(audio_file)
            
            # Transcribe
            logger.info("Transcribing audio...")
            transcribed_text = self.transcribe_audio(wav_file)
            
            if not transcribed_text:
                return {
                    "text": "Sorry, I couldn't understand the audio. Please try again.",
                    "transcription": ""
                }
            
            # Query RAG
            logger.info(f"Querying RAG with: {transcribed_text}")
            result = self.rag_engine.query(transcribed_text)
            
            return {
                "text": result['answer'],
                "transcription": transcribed_text
            }
            
        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            return {
                "text": "Sorry, I encountered an error processing your message.",
                "transcription": ""
            }
        finally:
            # Cleanup temporary files
            if audio_file and os.path.exists(audio_file):
                os.unlink(audio_file)
            if wav_file and os.path.exists(wav_file):
                os.unlink(wav_file)
