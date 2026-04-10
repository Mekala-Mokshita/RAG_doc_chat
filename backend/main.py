import os
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Depends, Header, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from jose import jwt, JWTError

from rag_pipeline import process_pdf, ask_question
from auth import users_db, hash_password, verify_password, create_access_token

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= PATH FIX =================
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_FOLDER = BASE_DIR / "backend/uploads"
VECTOR_FOLDER = BASE_DIR / "backend/vector_store"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VECTOR_FOLDER, exist_ok=True)

# serve css & js
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# serve login page
@app.get("/", response_class=HTMLResponse)
def serve_login():
    return FileResponse(FRONTEND_DIR / "login.html")

# serve chat page
@app.get("/chat", response_class=HTMLResponse)
def serve_chat():
    return FileResponse(FRONTEND_DIR / "index.html")


# ================= AUTHENTICATION =================

# ---------------- REGISTER ----------------
@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):

    if username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    users_db[username] = hash_password(password)

    return {"message": "User registered successfully"}


# ---------------- LOGIN ----------------
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):

    if username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid username")

    if not verify_password(password, users_db[username]):
        raise HTTPException(status_code=401, detail="Wrong password")

    token = create_access_token(username)

    return {"access_token": token}




# -------- TOKEN VERIFY --------
def verify_token(authorization: str = Header(None)):

    if authorization is None:
        raise HTTPException(status_code=401, detail="Please login first")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, "genagentsecretkey123", algorithms=["HS256"])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired. Please login again")


# ================= UPLOAD =================
@app.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: str = Depends(verify_token)
):

    # remove old index
    faiss_file = VECTOR_FOLDER / "faiss.index"
    chunk_file = VECTOR_FOLDER / "chunks.pkl"

    if faiss_file.exists():
        faiss_file.unlink()

    if chunk_file.exists():
        chunk_file.unlink()

    # save file
    file_location = UPLOAD_FOLDER / file.filename

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # process in background
    background_tasks.add_task(process_pdf, str(file_location))

    return {"message": f"📄 Uploaded by {user}. Processing... wait 15 seconds."}


# ================= ASK =================
@app.get("/ask")
def ask(query: str, user: str = Depends(verify_token)):
    return ask_question(query)
