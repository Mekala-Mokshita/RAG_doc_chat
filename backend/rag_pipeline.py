import os
import pickle
import numpy as np
import faiss
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from groq import Groq

load_dotenv()

# ---------- Paths ----------
# ---------- Paths ----------
VECTOR_DIR = "vector_store"

# create folder automatically
os.makedirs(VECTOR_DIR, exist_ok=True)

VECTOR_DB_PATH = os.path.join(VECTOR_DIR, "faiss.index")
CHUNK_PATH = os.path.join(VECTOR_DIR, "chunks.pkl")
# ---------- Models ----------
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# =========================================================
#                PDF INGESTION (VERY IMPORTANT)
# =========================================================
def process_pdf(file_path):

    print("Loading PDF...")
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    print("Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(docs)
    TEXT_STORE = [chunk.page_content for chunk in chunks]

    if len(TEXT_STORE) == 0:
        print("No text extracted from PDF")
        return

    print("Creating embeddings...")
    embeddings = embedding_model.encode(TEXT_STORE)
    embeddings = np.array(embeddings).astype("float32")

    print("Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # Save vector DB
    faiss.write_index(index, VECTOR_DB_PATH)

    # Save chunks
    with open(CHUNK_PATH, "wb") as f:
        pickle.dump(TEXT_STORE, f)

    print("PDF processing completed. RAG ready.")


# =========================================================
#                     QUESTION ANSWERING
# =========================================================
def ask_question(query):

    # If user asks before processing finishes
    if not os.path.exists(VECTOR_DB_PATH):
        return {"answer": "⚠️ Please upload a PDF first."}

    if not os.path.exists(CHUNK_PATH):
        return {"answer": "⏳ Document still processing. Please wait 20–30 seconds and try again."}

    try:
        # Load chunks
        with open(CHUNK_PATH, "rb") as f:
            text_store = pickle.load(f)

        # Load FAISS index
        index = faiss.read_index(VECTOR_DB_PATH)

        # Embed query
        query_embedding = embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")

        # Search
        D, I = index.search(query_embedding, k=3)

        retrieved_chunks = []
        for idx in I[0]:
            if idx != -1 and idx < len(text_store):
                retrieved_chunks.append(text_store[idx])

        if len(retrieved_chunks) == 0:
            return {"answer": "Not found in document."}

        context = "\n".join(retrieved_chunks)

        prompt = f"""
You are a helpful assistant.
Answer ONLY using the context below.
If answer not present, reply "Not found in document."

Context:
{context}

Question:
{query}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return {"answer": response.choices[0].message.content.strip()}

    except Exception as e:
        print("RAG ERROR:", e)
        return {"answer": "⚠️ Error reading the document. Try re-uploading the PDF."}
