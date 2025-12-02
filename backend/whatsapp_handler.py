import os
import requests
import assemblyai as aai
from gtts import gTTS
from typing import Dict
from rag_engine import RAGEngine
import logging
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppHandler:
    def __init__(self, rag_engine: RAGEngine):
        self.rag_engine = rag_engine
        # Configure AssemblyAI
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
    
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
    
    def transcribe_audio(self, audio_file: str) -> str:
        """Transcribe audio using AssemblyAI."""
        try:
            if not os.getenv("ASSEMBLYAI_API_KEY"):
                logger.error("ASSEMBLYAI_API_KEY not set")
                return ""
            
            logger.info("Transcribing with AssemblyAI...")
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_file)
            
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"Transcription error: {transcript.error}")
                return ""
            
            logger.info(f"Transcribed: {transcript.text}")
            return transcript.text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    def process_voice_message(self, media_url: str, auth: tuple) -> Dict[str, str]:
        """Download and transcribe voice message."""
        audio_file = None
        
        try:
            # Download audio
            logger.info("Downloading voice message...")
            audio_file = self.download_audio(media_url, auth)
            
            # Transcribe
            transcription = self.transcribe_audio(audio_file)
            
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
    
    def process_text_message(self, text: str) -> str:
        """Process text message and generate response."""
        try:
            logger.info(f"Processing text: {text}")
            result = self.rag_engine.query(text)
            return result['answer']
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Sorry, I encountered an error processing your message."
