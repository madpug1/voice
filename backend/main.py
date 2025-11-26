from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from rag_engine import RAGEngine
from twilio_handler import TwilioIVRHandler
import os
from dotenv import load_dotenv

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

# Initialize RAG engine
pdf_dir = os.getenv("PDF_DATA_DIR", "./data/pdfs")
index_path = os.getenv("VECTOR_INDEX_PATH", "./vector_index")
rag_engine = RAGEngine(index_path=index_path)

# Initialize Twilio IVR handler
twilio_handler = TwilioIVRHandler(rag_engine)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
