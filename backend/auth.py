import hashlib
from datetime import datetime, timedelta
from jose import jwt

# simple in-memory DB
users_db = {}

SECRET_KEY = "genagentsecretkey123"
ALGORITHM = "HS256"


# ---------- PASSWORD HASH ----------
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str):
    return hashlib.sha256(password.encode()).hexdigest() == hashed


# ---------- TOKEN ----------
def create_access_token(username: str):
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(hours=2)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token
