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

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite and CRA defaults
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for audio responses
import os as os_module
static_dir = os_module.path.join(os_module.path.dirname(__file__), 'static')
os_module.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize RAG engine
pdf_dir = os.getenv("PDF_DATA_DIR", "./data/documents")
index_path = os.getenv("VECTOR_INDEX_PATH", "./vector_index")
rag_engine = RAGEngine(index_path=index_path)

# Initialize Twilio IVR handler
twilio_handler = TwilioIVRHandler(rag_engine)

# Initialize WhatsApp handler
whatsapp_handler = WhatsAppHandler(rag_engine)

# Initialize Twilio client
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
    """Auto-ingest PDFs on startup if data directory exists."""
    print("🚀 Starting RAG API...")
    print(f"📁 PDF Directory: {pdf_dir}")
    print(f"💾 Vector Index Path: {index_path}")
    
    # Check if API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  WARNING: GEMINI_API_KEY not set in .env file")
    else:
        print("✅ Gemini API Key configured")
    
    # Auto-ingest PDFs on startup
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
    """Health check endpoint."""
    return {
        "status": "running",
        "message": "RAG API is operational",
        "version": "1.0.0"
    }

@app.get("/debug/index")
async def debug_index():
    """Debug endpoint to check ingested documents."""
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
    """Clear the entire index (for debugging)."""
    rag_engine.clear_index()
    return {"status": "success", "message": "Index cleared. Call /ingest to rebuild."}

@app.post("/ingest")
async def ingest_pdfs():
    """
    Ingest all PDFs from the configured directory.
    This will extract text, chunk it, and store embeddings in ChromaDB.
    """
    try:
        result = rag_engine.ingest_pdfs(pdf_dir)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest):
    """
    Query the knowledge base with RAG.
    Retrieves relevant context and generates a response using Gemini API.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        result = rag_engine.query(request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get statistics about the knowledge base."""
    try:
        count = rag_engine.collection.count()
        return {
            "total_chunks": count,
            "collection_name": rag_engine.collection.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/voice/incoming")
async def voice_incoming():
    """
    Handle incoming phone call from Twilio.
    Returns TwiML response with welcome message and speech gathering.
    """
    twiml = twilio_handler.handle_incoming_call()
    return Response(content=twiml, media_type="application/xml")

@app.post("/voice/gather")
async def voice_gather(SpeechResult: str = Form(None)):
    """
    Handle transcribed speech from user.
    Query RAG engine and return response as TwiML.
    """
    twiml = twilio_handler.handle_speech_input(SpeechResult or "")
    return Response(content=twiml, media_type="application/xml")

@app.post("/voice/continue")
async def voice_continue(SpeechResult: str = Form(None)):
    """
    Handle user's response to continue prompt.
    Returns TwiML to continue or end conversation.
    """
    twiml = twilio_handler.handle_continue(SpeechResult or "")
    return Response(content=twiml, media_type="application/xml")

@app.post("/whatsapp/incoming")
async def whatsapp_incoming(
    From: str = Form(...),
    Body: str = Form(None),
    NumMedia: int = Form(0),
    MediaContentType0: str = Form(None),
    MediaUrl0: str = Form(None)
):
    """
    Handle incoming WhatsApp messages (text and voice notes).
    """
    logger.info(f"Received WhatsApp message from {From}")
    
    response = MessagingResponse()
    
    try:
        # Check if there's a voice message
        if NumMedia > 0 and MediaContentType0 and 'audio' in MediaContentType0 and MediaUrl0:
            logger.info("Processing voice message...")
            
            # Download and transcribe voice message
            auth = (twilio_account_sid, twilio_auth_token)
            result = whatsapp_handler.process_voice_message(MediaUrl0, auth)
            
            
            if result['transcription']:
                # Send audio response if available
                if result.get('audio_file'):
                    # Get the public URL for the audio file  
                    base_url = os.getenv("RENDER_EXTERNAL_URL", "https://rag-phone-bot.onrender.com")
                    audio_url = f"{base_url}/static/audio/{result['audio_file']}"
                    
                    # Send audio as media
                    msg = response.message()
                    msg.media(audio_url)
                    logger.info(f"Sending audio response: {audio_url}")
                else:
                    # Fallback to text
                    answer = result['text']
                    if len(answer) > 1600:
                        answer = answer[:1597] + "..."
                    response.message(answer)
            else:
                response.message(result['text'][:1600])
        
        elif Body:
            # Handle text message
            logger.info(f"Processing text message: {Body}")
            answer = whatsapp_handler.process_text_message(Body)
            # Limit to 1600 chars
            if len(answer) > 1600:
                answer = answer[:1597] + "..."
            logger.info(f"Sending response: {answer[:100]}...")  # Log first 100 chars
            response.message(answer)
        
        else:
            response.message("Please send a text message or voice note with your question!")
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        response.message("Sorry, I encountered an error. Please try again.")
    
    logger.info(f"TwiML response: {str(response)[:200]}")  # Log the TwiML
    return Response(content=str(response), media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
