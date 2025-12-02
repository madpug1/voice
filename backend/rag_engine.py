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
        self.index_path = index_path
        self.vectorizer = TfidfVectorizer(max_features=None, stop_words='english')
        
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
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks

    def save_index(self):
        with open(self.index_file, 'wb') as f:
            pickle.dump({
                'vectors': self.vectors,
                'vectorizer': self.vectorizer
            }, f)
        with open(self.metadata_file, 'wb') as f:
            pickle.dump(self.metadata, f)

    def clear_index(self):
        self.metadata = []
        self.vectors = None
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        if os.path.exists(self.metadata_file):
            os.remove(self.metadata_file)

    def ingest_pdfs(self, pdf_directory: str) -> Dict[str, int]:
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)
            return {"status": "error", "message": "PDF directory created but empty", "count": 0}

        self.clear_index()

        pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]

        if not pdf_files:
            return {"status": "warning", "message": "No PDF files found", "count": 0}

        all_chunks = []
        total_chunks = 0
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_directory, pdf_file)
            
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                print(f"⚠️  WARNING: No text extracted from {pdf_file}")
                continue
            
            print(f"✅ Extracted {len(text)} characters from {pdf_file}")
            
            chunks = self.chunk_text(text)
            
            for idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                self.metadata.append({
                    "text": chunk,
                    "source": pdf_file,
                    "chunk_id": idx
                })
                total_chunks += 1
        
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
        if self.vectors is None or len(self.metadata) == 0:
            print("⚠️  Index is empty")
            return []
        
        sources = set(m['source'] for m in self.metadata)
        print(f"📚 Index contains {len(sources)} documents: {list(sources)}")
        
        try:
            print(f"🔍 Processing Query: '{query}'")
            
            terms = query.lower().split()
            known_terms = [t for t in terms if t in self.vectorizer.vocabulary_]
            print(f"   Vocabulary matches: {known_terms} (out of {terms})")
            
            query_vector = self.vectorizer.transform([query])
            
            if query_vector.nnz == 0:
                print(f"⚠️  Query has NO matching terms in the vocabulary!")
                return []
            
            similarities = cosine_similarity(query_vector, self.vectors).flatten()
            
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
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
        if not self.gemini_api_key:
            return "Error: GEMINI_API_KEY not configured"
        
        if not context:
            return "I couldn't find relevant information in the knowledge base. Please make sure PDFs are ingested."
        
        context_text = "\n\n".join(context)
        
        system_prompt = """You are a helpful AI assistant that answers questions based ONLY on the provided knowledge base.

CRITICAL RULES:
1. ONLY use information from the knowledge base provided below
2. If the answer is not in the knowledge base, say: "I don't have this information in the knowledge base provided."
3. Be concise and direct - this is for WhatsApp messaging
4. Keep responses under 500 characters when possible
5. Use simple language, avoid jargon
6. Do NOT make up information or use external knowledge
7. Always refer to the source as "knowledge base" not "document"

KNOWLEDGE BASE:
{context}

USER QUESTION: {query}

YOUR ANSWER (concise, knowledge base only):"""
        
        prompt = system_prompt.format(context=context_text, query=query)
        
        try:
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 500
                }
            }
            
            response = requests.post(
                self.gemini_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    answer = result['candidates'][0]['content']['parts'][0]['text']
                    return answer.strip()
                else:
                    return "I couldn't generate a response. Please try rephrasing your question."
            else:
                print(f"Gemini API error: {response.status_code} - {response.text}")
                return f"Error generating response. Please try again."
                
        except requests.exceptions.Timeout:
            return "Request timed out. Please try again."
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "An error occurred while generating the response."

    def query(self, query: str) -> Dict:
        context = self.retrieve_context(query)
        answer = self.generate_response(query, context)
        
        sources = list(set([m['source'] for m in self.metadata if m['text'] in context]))
        
        return {
            "answer": answer,
            "context": context,
            "sources": sources
        }
