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
        # Use all unique words (no limit) to ensure small documents are fully indexed
        self.vectorizer = TfidfVectorizer(max_features=None, stop_words='english')
        
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

    def clear_index(self):
        """Completely clear vectors and metadata, both in memory and on disk."""
        self.metadata = []
        self.vectors = None
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        if os.path.exists(self.metadata_file):
            os.remove(self.metadata_file)

    def ingest_pdfs(self, pdf_directory: str) -> Dict[str, int]:
        """Load and index all PDFs from the specified directory."""
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)
            return {"status": "error", "message": "PDF directory created but empty", "count": 0}

        # 🔁 HARD RESET: clear in-memory index + metadata
        self.clear_index()

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
                print(f"⚠️  WARNING: No text extracted from {pdf_file}")
                continue
            
            print(f"✅ Extracted {len(text)} characters from {pdf_file}")
            
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
            print(f"✅ Vocabulary size: {len(self.vectorizer.vocabulary_)} unique terms")
            self.save_index()
        
        return {
            "status": "success",
            "message": f"Ingested {len(pdf_files)} PDF(s)",
            "count": total_chunks
        }

    def retrieve_context(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant chunks using TF-IDF similarity."""
        if self.vectors is None or len(self.metadata) == 0:
            print("⚠️  Index is empty")
            return []
        
        # Debug: Print available documents
        sources = set(m['source'] for m in self.metadata)
        print(f"📚 Index contains {len(sources)} documents: {list(sources)}")
        
        try:
            print(f"🔍 Processing Query: '{query}'")
            
            # Check if query terms are in vocabulary
            terms = query.lower().split()
            known_terms = [t for t in terms if t in self.vectorizer.vocabulary_]
            print(f"   Vocabulary matches: {known_terms} (out of {terms})")
            
            # Vectorize query
            query_vector = self.vectorizer.transform([query])
            
            # Check if query vector is empty
            if query_vector.nnz == 0:
                print(f"⚠️  Query has NO matching terms in the vocabulary!")
                return []
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, self.vectors).flatten()
            
            # Get top k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            # Get corresponding texts
            results = []
            for idx in top_indices:
                score = similarities[idx]
                if score > 0:
                    meta = self.metadata[idx]
                    print(f"   📄 Match: {meta['source']} (Score: {score:.4f})")
                    results.append(meta["text"])
            
            if not results:
                print("⚠️  No relevant chunks found (all scores 0)")
                
            return results
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []

    def generate_response(self, query: str, context: List[str]) -> str:
        """Generate a response using Gemini API with retrieved context."""
        # Prepare context
        context_text = "\n\n".join(context)
        
        # Create prompt with context
        prompt = f"""You are an AI assistant that answers user questions only using the information found in the provided knowledge base (RAG context).
The user is chatting with you via WhatsApp, so keep messages clear, short, and easy to read.

Context:
{context_text}

Question: {query}

Core Rules:

1. Use only the provided knowledge base
   - Base your answers strictly on the content in the retrieved context
   - If the answer is not clearly supported by the knowledge base, say: "I don't have this information"
   - Do not guess, invent, or rely on outside knowledge

2. Be straight to the point
   - Start with the direct answer in the first sentence
   - Use short, precise sentences
   - Avoid long introductions, disclaimers, or explanations unless asked

3. Respect the knowledge base
   - If the knowledge base is unclear or conflicting, explain briefly and say you cannot be certain
   - If multiple interpretations exist, mention them briefly and stay neutral

4. If the question is outside scope
   - If the user asks about anything not covered in the knowledge base, respond: "I don't have this information in the knowledge base provided."

5. Formatting & style (for WhatsApp)
   - Keep answers compact (1-4 short paragraphs or a brief list)
   - Use lists only when they improve clarity
   - Avoid emojis unless the user uses them first
   - Use simple language, no heavy jargon unless it appears in the knowledge base

6. Follow-up questions
   - If the question is ambiguous but about the knowledge base, ask one short clarifying question
   - If you cannot answer even with clarification, reply: "I don't have this information"

Answer:"""

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
                    return "I don't have this information in the knowledge base provided."
            else:
                # Log the error for debugging
                error_msg = f"Gemini API error {response.status_code}: {response.text}"
                print(error_msg)
                return "I don't have this information in the knowledge base provided."
                
        except Exception as e:
            print(f"Gemini API exception: {str(e)}")
            return "I don't have this information in the knowledge base provided."

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
