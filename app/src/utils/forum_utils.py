import uuid
from io import BytesIO
from pathlib import Path
from fastapi import UploadFile
from PIL import Image

MEDIA_ROOT = Path("/var/sehati-media/forum")

async def save_forum_image(file: UploadFile) -> str:
    ext = file.filename.split(".")[-1].lower()
    name = f"{uuid.uuid4()}.{ext}"
    dest = MEDIA_ROOT / name
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

    data = await file.read()
    img = Image.open(BytesIO(data))
    img.verify()

    with open(dest, "wb") as f:
        f.write(data)

    return f"/media/forum/{name}"
