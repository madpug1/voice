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
        """Transcribe audio using AssemblyAI from file."""
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
            return "Sorry, I encountered an error processing your message."
