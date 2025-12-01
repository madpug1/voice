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
    
    def convert_audio_to_wav(self, input_file: str) -> str:
        """Convert audio to WAV format for speech recognition."""
        try:
            audio = AudioSegment.from_file(input_file)
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
                logger.info(f"Transcribed: {text}")
                return text
        except sr.UnknownValueError:
            logger.error("Could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return ""
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    def process_voice_message(self, media_url: str, auth: tuple) -> Dict[str, str]:
        """Download and transcribe voice message."""
        audio_file = None
        wav_file = None
        
        try:
            # Download audio
            logger.info("Downloading voice message...")
            audio_file = self.download_audio(media_url, auth)
            
            # Convert to WAV
            logger.info("Converting audio format...")
            wav_file = self.convert_audio_to_wav(audio_file)
            
            # Transcribe
            logger.info("Transcribing audio...")
            transcription = self.transcribe_audio(wav_file)
            
            if not transcription:
                return {
                    "text": "Sorry, I couldn't understand the audio. Please try again or send a text message.",
                    "transcription": ""
                }
            
            # Query RAG
            logger.info(f"Querying RAG: {transcription}")
            result = self.rag_engine.query(transcription)
            
            return {
                "text": result['answer'],
                "transcription": transcription
            }
            
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            return {
                "text": "Sorry, I encountered an error processing your voice message. Please try sending a text message.",
                "transcription": ""
            }
        finally:
            # Cleanup
            if audio_file and os.path.exists(audio_file):
                os.unlink(audio_file)
            if wav_file and os.path.exists(wav_file):
                os.unlink(wav_file)
    
    def process_text_message(self, text: str) -> str:
        """Process text message and generate response."""
        try:
            logger.info(f"Processing text: {text}")
            result = self.rag_engine.query(text)
            return result['answer']
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Sorry, I encountered an error processing your message."
