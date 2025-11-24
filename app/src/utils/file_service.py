import uuid
import os
from fastapi import UploadFile

MEDIA_ROOT = "/var/sehati-media"

async def save_upload_with_uuid(file: UploadFile, folder: str):
    ext = file.filename.split(".")[-1].lower()
    new_name = f"{uuid.uuid4()}.{ext}"

    save_dir = os.path.join(MEDIA_ROOT, folder)
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, new_name)

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return new_name
