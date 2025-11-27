import os
import requests
import pickle
from typing import List, Dict
from PyPDF2 import PdfReader
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

class RAGEngine:
    def __init__(self, index_path: str = "./vector_index"):
        """Initialize the RAG engine with TF-IDF vectorizer."""
        self.index_path = index_path
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
        # Storage for documents and vectors
        self.index_file = os.path.join(index_path, "vectors.pkl")
        self.metadata_file = os.path.join(index_path, "metadata.pkl")
        
        if os.path.exists(self.index_file):
            with open(self.index_file, 'rb') as f:
                data = pickle.load(f)
                self.vectors = data['vectors']
                self.vectorizer = data['vectorizer']
            with open(self.metadata_file, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            self.vectors = None
            self.metadata = []
            os.makedirs(index_path, exist_ok=True)
        
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

    def save_index(self):
        """Save vectors and metadata to disk."""
        with open(self.index_file, 'wb') as f:
            pickle.dump({
                'vectors': self.vectors,
                'vectorizer': self.vectorizer
            }, f)
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(self.metadata, f)

    def ingest_pdfs(self, pdf_directory: str) -> Dict[str, int]:
        """Load and index all PDFs from the specified directory."""
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)
            return {"status": "error", "message": "PDF directory created but empty", "count": 0}
        
        pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]
        
        if not pdf_files:
            return {"status": "warning", "message": "No PDF files found", "count": 0}
        
        all_chunks = []
        total_chunks = 0
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_directory, pdf_file)
            
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                continue
            
            # Chunk text
            chunks = self.chunk_text(text)
            
            # Store metadata
            for idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                self.metadata.append({
                    "text": chunk,
                    "source": pdf_file,
                    "chunk_id": idx
                })
                total_chunks += 1
        
        # Vectorize all chunks at once
        if all_chunks:
            self.vectors = self.vectorizer.fit_transform(all_chunks)
            self.save_index()
        
        return {
            "status": "success",
            "message": f"Ingested {len(pdf_files)} PDF(s)",
            "count": total_chunks
        }

    def retrieve_context(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant chunks using TF-IDF similarity."""
        if self.vectors is None or len(self.metadata) == 0:
            return []
        
        # Vectorize query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, self.vectors)[0]
        
        # Get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Get corresponding texts
        results = []
        for idx in top_indices:
            if idx < len(self.metadata):
                results.append(self.metadata[idx]["text"])
        
        return results

    def generate_response(self, query: str, context: List[str]) -> str:
        """Generate a response using Gemini API with retrieved context."""
        # Prepare context
        context_text = "\n\n".join(context)
        
        # Create prompt with context
        prompt = f"""You are a helpful AI assistant. Answer questions concisely and clearly.

Context:
{context_text}

Question: {query}

Instructions:
- Provide a brief, direct answer (2-4 sentences maximum)
- Summarize key points in your own words - DO NOT copy-paste entire paragraphs
- Use simple, conversational language
- If the context doesn't have the answer, say "I don't have that information in my knowledge base"
- Be specific and to the point"""

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
