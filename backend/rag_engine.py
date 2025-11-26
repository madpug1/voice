import os
import requests
from typing import List, Dict
from PyPDF2 import PdfReader
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

class RAGEngine:
    def __init__(self, chroma_path: str = "./chroma_db"):
        """Initialize the RAG engine with ChromaDB and embedding model."""
        self.chroma_path = chroma_path
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name="pdf_knowledge")
        except:
            self.collection = self.chroma_client.create_collection(
                name="pdf_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
        
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks

    def ingest_pdfs(self, pdf_directory: str) -> Dict[str, int]:
        """Load and index all PDFs from the specified directory."""
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)
            return {"status": "error", "message": "PDF directory created but empty", "count": 0}
        
        pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]
        
        if not pdf_files:
            return {"status": "warning", "message": "No PDF files found", "count": 0}
        
        total_chunks = 0
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_directory, pdf_file)
            
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                continue
            
            # Chunk text
            chunks = self.chunk_text(text)
            
            # Generate embeddings and store in ChromaDB
            for idx, chunk in enumerate(chunks):
                embedding = self.embedding_model.encode(chunk).tolist()
                
                self.collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{"source": pdf_file, "chunk_id": idx}],
                    ids=[f"{pdf_file}_{idx}"]
                )
                total_chunks += 1
        
        return {
            "status": "success",
            "message": f"Ingested {len(pdf_files)} PDF(s)",
            "count": total_chunks
        }

    def retrieve_context(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant chunks from the vector database."""
        query_embedding = self.embedding_model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        if results and results['documents']:
            return results['documents'][0]
        return []

    def generate_response(self, query: str, context: List[str]) -> str:
        """Generate a response using Gemini API with retrieved context."""
        # Prepare context
        context_text = "\n\n".join(context)
        
        # Create prompt with context
        prompt = f"""You are a helpful assistant answering questions based on the provided context.

Context:
{context_text}

Question: {query}

Please provide a comprehensive answer based on the context above. If the context doesn't contain relevant information, say so."""

        # Call Gemini API
        try:
            response = requests.post(
                self.gemini_url,
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and len(data['candidates']) > 0:
                    return data['candidates'][0]['content']['parts'][0]['text']
                else:
                    return "Error: No response generated"
            else:
                return f"Error: API returned status {response.status_code}"
                
        except Exception as e:
            return f"Error calling Gemini API: {str(e)}"

    def query(self, question: str) -> Dict[str, any]:
        """Main query function that retrieves context and generates response."""
        # Retrieve relevant context
        context = self.retrieve_context(question)
        
        if not context:
            return {
                "answer": "I couldn't find relevant information in the knowledge base. Please make sure PDFs are ingested.",
                "context": [],
                "sources": []
            }
        
        # Generate response
        answer = self.generate_response(question, context)
        
        return {
            "answer": answer,
            "context": context,
            "num_sources": len(context)
        }
