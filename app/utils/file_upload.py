import hashlib
from fastapi import UploadFile
from ..config import settings


async def save_upload_file(file: UploadFile) -> str:
    # 生成文件哈希名
    file_bytes = await file.read()
    file_hash = hashlib.md5(file_bytes).hexdigest()
    ext = file.filename.split('.')[-1]
    filename = f"{file_hash}.{ext}"
    save_path = settings.UPLOAD_DIR / filename

    # 保存文件
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    return str(save_path)
