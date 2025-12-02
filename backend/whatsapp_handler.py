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
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
    
    def download_audio(self, media_url: str, auth: tuple) -> str:
        try:
            response = requests.get(media_url, auth=auth)
            response.raise_for_status()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ogg')
            temp_file.write(response.content)
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            raise
    
    def convert_to_wav(self, ogg_file: str) -> str:
        try:
            import subprocess
            
            wav_file = ogg_file.replace('.ogg', '.wav')
            
            subprocess.run([
                'ffmpeg', '-i', ogg_file,
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                wav_file
            ], check=True, capture_output=True)
            
            return wav_file
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            return ogg_file
    
    def transcribe_audio(self, audio_file: str) -> str:
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
    
    def generate_audio_response(self, text: str) -> str:
        try:
            import hashlib
            import time
            
            static_dir = os.path.join(os.path.dirname(__file__), 'static', 'audio')
            os.makedirs(static_dir, exist_ok=True)
            
            timestamp = str(int(time.time()))
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            filename = f"response_{timestamp}_{text_hash}.mp3"
            audio_path = os.path.join(static_dir, filename)
            
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(audio_path)
            
            logger.info(f"Generated audio response: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return None
    
    def process_voice_message(self, media_url: str, auth: tuple) -> Dict[str, str]:
        audio_file = None
        wav_file = None
        
        try:
            logger.info("Downloading voice message...")
            audio_file = self.download_audio(media_url, auth)
            
            logger.info("Converting audio to WAV...")
            wav_file = self.convert_to_wav(audio_file)
            
            logger.info("Transcribing with AssemblyAI...")
            transcription = self.transcribe_audio(wav_file)
            
            if not transcription:
                return {
                    "text": "Sorry, I couldn't understand the audio. Please try again or send a text message.",
                    "transcription": "",
                    "audio_file": None
                }
            
            logger.info(f"Querying RAG: {transcription}")
            result = self.rag_engine.query(transcription)
            
            logger.info("Generating audio response...")
            audio_response = self.generate_audio_response(result['answer'])
            
            return {
                "text": result['answer'],
                "transcription": transcription,
                "audio_file": audio_response
            }
            
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            return {
                "text": "Sorry, I encountered an error processing your voice message. Please try sending a text message.",
                "transcription": "",
                "audio_file": None
            }
        finally:
            if audio_file and os.path.exists(audio_file):
                os.unlink(audio_file)
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
        aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
    
    def download_audio(self, media_url: str, auth: tuple) -> str:
        try:
            response = requests.get(media_url, auth=auth)
            response.raise_for_status()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.ogg')
            temp_file.write(response.content)
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            raise
    
    def convert_to_wav(self, ogg_file: str) -> str:
        try:
            import subprocess
            
            wav_file = ogg_file.replace('.ogg', '.wav')
            
            subprocess.run([
                'ffmpeg', '-i', ogg_file,
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                wav_file
            ], check=True, capture_output=True)
            
            return wav_file
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            return ogg_file
    
    def transcribe_audio(self, audio_file: str) -> str:
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
    
    def generate_audio_response(self, text: str) -> str:
        try:
            import hashlib
            import time
            
            static_dir = os.path.join(os.path.dirname(__file__), 'static', 'audio')
            os.makedirs(static_dir, exist_ok=True)
            
            timestamp = str(int(time.time()))
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            filename = f"response_{timestamp}_{text_hash}.mp3"
            audio_path = os.path.join(static_dir, filename)
            
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(audio_path)
            
            logger.info(f"Generated audio response: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return None
    
    def process_voice_message(self, media_url: str, auth: tuple) -> Dict[str, str]:
        audio_file = None
        wav_file = None
        
        try:
            logger.info("Downloading voice message...")
            audio_file = self.download_audio(media_url, auth)
            
            logger.info("Converting audio to WAV...")
            wav_file = self.convert_to_wav(audio_file)
            
            logger.info("Transcribing with AssemblyAI...")
            transcription = self.transcribe_audio(wav_file)
            
            if not transcription:
                return {
                    "text": "Sorry, I couldn't understand the audio. Please try again or send a text message.",
                    "transcription": "",
                    "audio_file": None
                }
            
            logger.info(f"Querying RAG: {transcription}")
            result = self.rag_engine.query(transcription)
            
            logger.info("Generating audio response...")
            audio_response = self.generate_audio_response(result['answer'])
            
            return {
                "text": result['answer'],
                "transcription": transcription,
                "audio_file": audio_response
            }
            
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            return {
                "text": "Sorry, I encountered an error processing your voice message. Please try sending a text message.",
                "transcription": "",
                "audio_file": None
            }
        finally:
            if audio_file and os.path.exists(audio_file):
                os.unlink(audio_file)
            if wav_file and wav_file != audio_file and os.path.exists(wav_file):
                os.unlink(wav_file)
    
    def process_text_message(self, text: str) -> str:
        try:
            logger.info(f"Processing text: {text}")
            
            greetings = ['hi', 'hello', 'hey', 'hii', 'hiii', 'good morning', 'good afternoon', 'good evening']
            if text.lower().strip() in greetings:
                return "Hello! 👋 I'm your AI assistant. Ask me anything about the knowledge base!"
            
            result = self.rag_engine.query(text)
            return result['answer']
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Sorry, I encountered an error processing your message."
