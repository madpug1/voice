import os
import requests
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
    
    def process_text_message(self, text: str) -> str:
        """Process text message and generate response."""
        try:
            logger.info(f"Processing text: {text}")
            result = self.rag_engine.query(text)
            return result['answer']
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Sorry, I encountered an error processing your message."
