from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rag_engine import RAGEngine
from twilio_handler import TwilioIVRHandler
from whatsapp_handler import WhatsAppHandler
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os as os_module
static_dir = os_module.path.join(os_module.path.dirname(__file__), 'static')
os_module.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

pdf_dir = os.getenv("PDF_DATA_DIR", "./data/documents")
index_path = os.getenv("VECTOR_INDEX_PATH", "./vector_index")
rag_engine = RAGEngine(index_path=index_path)

twilio_handler = TwilioIVRHandler(rag_engine)
whatsapp_handler = WhatsAppHandler(rag_engine)

twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_client = Client(twilio_account_sid, twilio_auth_token) if twilio_account_sid and twilio_auth_token else None

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    context: list
    num_sources: int

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting RAG API...")
    print(f"📁 PDF Directory: {pdf_dir}")
    print(f"💾 Vector Index Path: {index_path}")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  WARNING: GEMINI_API_KEY not set in .env file")
    else:
        print("✅ Gemini API Key configured")
    
    print("\n📚 Auto-ingesting PDFs...")
    try:
        result = rag_engine.ingest_pdfs(pdf_dir)
        if result["status"] == "success":
            print(f"✅ Successfully ingested {result['count']} chunks from PDFs")
        elif result["status"] == "warning":
            print(f"⚠️  {result['message']}")
        else:
            print(f"ℹ️  {result['message']}")
    except Exception as e:
        print(f"❌ Auto-ingestion failed: {e}")

@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "RAG API is operational",
        "version": "1.0.0"
    }

@app.get("/debug/index")
async def debug_index():
    if not rag_engine.metadata:
        return {"count": 0, "documents": []}
    
    documents = list(set([m['source'] for m in rag_engine.metadata]))
    return {
        "count": len(rag_engine.metadata),
        "num_documents": len(documents),
        "documents": documents
    }

@app.get("/clear_index")
async def clear_index():
    rag_engine.clear_index()
    return {"status": "success", "message": "Index cleared. Call /ingest to rebuild."}

@app.post("/ingest")
async def ingest_pdfs():
    try:
        result = rag_engine.ingest_pdfs(pdf_dir)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query(request: QueryRequest):
    try:
        result = rag_engine.query(request.query)
        return QueryResponse(
            answer=result["answer"],
            context=result["context"],
            num_sources=len(result["sources"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/incoming", response_class=Response)
async def voice_incoming(request: Request):
    form_data = await request.form()
    response_xml = twilio_handler.handle_incoming_call(dict(form_data))
    return Response(content=response_xml, media_type="application/xml")

@app.post("/voice/gather", response_class=Response)
async def voice_gather(request: Request):
    form_data = await request.form()
    response_xml = twilio_handler.handle_speech_result(dict(form_data))
    return Response(content=response_xml, media_type="application/xml")

@app.post("/whatsapp/incoming", response_class=Response)
async def whatsapp_incoming(
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaContentType0: str = Form(None),
    MediaUrl0: str = Form(None)
):
    logger.info(f"Received WhatsApp message from {From}")
    
    response = MessagingResponse()
    
    try:
        if NumMedia > 0 and MediaContentType0 and 'audio' in MediaContentType0 and MediaUrl0:
            logger.info("Processing voice message...")
            
            response.message("⏳ Awaiting response...")
            
            auth = (twilio_account_sid, twilio_auth_token)
            result = whatsapp_handler.process_voice_message(MediaUrl0, auth)
            
            
            if result['transcription']:
                if result.get('audio_file'):
                    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://rag-phone-bot.onrender.com")
                    audio_url = f"{base_url}/static/audio/{result['audio_file']}"
                    
                    audio_msg = response.message()
                    audio_msg.media(audio_url)
                    
                    transcription_msg = f"🎤 You said: \"{result['transcription']}\""
                    msg = response.message(transcription_msg)
                    
                    logger.info(f"Sending audio + transcription: {audio_url}")
                else:
                    answer = result['text']
                    if len(answer) > 1600:
                        answer = answer[:1597] + "..."
                    response.message(answer)
            else:
                response.message(result['text'][:1600])
        
        elif Body:
            logger.info(f"Processing text message: {Body}")
            answer = whatsapp_handler.process_text_message(Body)
            if len(answer) > 1600:
                answer = answer[:1597] + "..."
            logger.info(f"Sending response: {answer[:100]}...")
            response.message(answer)
        
        else:
            response.message("Please send a text message or voice note with your question!")
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        response.message("Sorry, I encountered an error. Please try again.")
    
    response_str = str(response)
    logger.info(f"TwiML response: {response_str[:200]}...")
    
    return Response(content=response_str, media_type="application/xml")
