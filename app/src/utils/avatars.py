import os
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from fastapi import UploadFile, HTTPException
from app.src.core.config import settings

MAX_BYTES = settings.MAX_AVATAR_MB * 1024 * 1024

def ensure_dir(directory: str):
    os.makedirs(directory, exist_ok=True)

async def read_limited(file: UploadFile, limit: int = MAX_BYTES) -> bytes:
    data = await file.read()
    if len(data) > limit:
        raise ValueError("File exceeds 2 MB limit.")
    return data

def verify_image(data: bytes):
    try:
        Image.open(BytesIO(data)).verify()
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file.")
