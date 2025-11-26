# 🤖 RAG Knowledge Assistant

A Retrieval-Augmented Generation (RAG) application that allows you to query knowledge stored in PDF files. Built with FastAPI backend, React frontend, ChromaDB for vector storage, and powered by Google's Gemini 2.0 Flash API.

## ✨ Features

- 📄 **PDF Ingestion**: Automatically load and index PDF documents
- 🔍 **Semantic Search**: Find relevant context using vector similarity
- 🤖 **AI-Powered Responses**: Generate answers using Gemini 2.0 Flash
- 💬 **Modern Chat Interface**: Beautiful, responsive UI with dark mode
- ⚡ **Real-time Updates**: Smooth animations and loading states

## 🏗️ Architecture

```
voiceCall/
├── backend/
│   ├── main.py                 # FastAPI server
│   ├── rag_engine.py           # Core RAG logic
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (create this)
│   ├── data/pdfs/              # Place your PDF files here
│   └── chroma_db/              # Vector database (auto-created)
└── frontend/
    ├── src/
    │   ├── App.jsx             # Main React component
    │   ├── index.css           # Styles
    │   └── main.jsx            # Entry point
    └── package.json
```

## 🚀 Setup Instructions

### Backend Setup

1. **Navigate to backend directory**:
   ```powershell
   cd backend
   ```

2. **Install Python dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Create .env file** (copy from .env.example):
   ```powershell
   cp .env.example .env
   ```

4. **Add your Gemini API key** to `.env`:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

5. **Create PDF directory and add files**:
   ```powershell
   mkdir -p data/pdfs
   # Place your knowledge PDF files in data/pdfs/
   ```

6. **Start the backend server**:
   ```powershell
   uvicorn main:app --reload
   ```

   Backend will run at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```powershell
   cd frontend
   ```

2. **Install dependencies**:
   ```powershell
   npm install
   ```

3. **Start the development server**:
   ```powershell
   npm run dev
   ```

   Frontend will run at `http://localhost:5173`

## 📖 Usage

1. **Ingest PDFs**: Click the "📚 Ingest PDFs" button to load and index your documents
2. **Ask Questions**: Type your question in the chat input
3. **Get Answers**: The AI will retrieve relevant context and generate a response

## 🔧 API Endpoints

- `GET /` - Health check
- `POST /ingest` - Ingest PDFs from the data directory
- `POST /query` - Query the knowledge base
  ```json
  {
    "query": "What is the main topic?"
  }
  ```
- `GET /stats` - Get knowledge base statistics

## 🎨 Tech Stack

- **Backend**: FastAPI, ChromaDB, Sentence Transformers
- **Frontend**: React, Vite
- **AI**: Google Gemini 2.0 Flash API
- **Vector DB**: ChromaDB (local persistent storage)

## 📝 Notes

- PDFs are stored locally in `backend/data/pdfs/`
- Vector embeddings are persisted in `backend/chroma_db/`
- The system uses `all-MiniLM-L6-v2` for generating embeddings
- Text is chunked with 500 words per chunk and 50 words overlap

## 🔐 Environment Variables

Required in `backend/.env`:
- `GEMINI_API_KEY` - Your Google Gemini API key
- `CHROMA_DB_PATH` - Path to ChromaDB storage (default: `./chroma_db`)
- `PDF_DATA_DIR` - Path to PDF directory (default: `./data/pdfs`)

## 🚀 Production Deployment

For production:
1. Build the React app: `cd frontend && npm run build`
2. Serve the build folder with a static server
3. Run FastAPI with `uvicorn main:app --host 0.0.0.0 --port 8000`
4. Configure proper CORS origins in `main.py`

---

Made with ❤️ using FastAPI, React, and Gemini AI
