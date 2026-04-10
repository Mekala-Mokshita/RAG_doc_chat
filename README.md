#  RAG Doc Chat

An AI-powered document assistant that allows users to upload PDFs and ask questions using Retrieval-Augmented Generation (RAG).

---

## Features

- Upload PDF documents
- Semantic search using FAISS
- AI-based question answering
- ChatGPT-like UI
- Multi-chat session support
- User authentication system

---

## Tech Stack

- Backend: FastAPI (Python)
- Frontend: HTML, CSS, JavaScript
- Vector DB: FAISS
- Embeddings: Sentence Transformers
- LLM: Groq (LLaMA)

---

## How It Works

1. Upload PDF
2. Text is split into chunks
3. Embeddings are generated
4. Stored in FAISS
5. Query → similarity search
6. Context → LLM → Answer

---

## Run Locally
uvicorn main:app --reload
