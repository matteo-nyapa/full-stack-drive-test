from datetime import datetime
from typing import List
from uuid import uuid4

from bson import ObjectId
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pymongo import ReturnDocument

from app.config import files_collection
from app.minio_client import (
    delete_from_minio,
    download_from_minio,
    upload_to_minio,
)
from app.models import FileOut, FileRename

router = APIRouter(prefix="/files", tags=["files"])


def _doc_to_file(doc) -> FileOut:
    return FileOut(
        id=str(doc["_id"]),
        name=doc["name"],
        size=doc["size"],
        mime_type=doc["mime_type"],
        upload_date=doc["upload_date"],
        path=doc["path"],
    )


@router.get("/", response_model=List[FileOut])
async def list_files():
    """List all files (metadata only)."""
    docs: List[FileOut] = []
    async for doc in files_collection.find().sort("upload_date", -1):
        docs.append(_doc_to_file(doc))
    return docs


@router.post("/", response_model=FileOut)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file:
    - Save it to MinIO
    - Save the metadata to MongoDB
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="File has no name")

    object_name = f"{uuid4()}-{file.filename}"

    await upload_to_minio(file, object_name)

    upload_date = datetime.utcnow()

    dummy_size = 0

    doc = {
        "name": file.filename,
        "size": dummy_size,
        "mime_type": file.content_type or "application/octet-stream",
        "upload_date": upload_date,
        "path": object_name,
    }

    result = await files_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    return _doc_to_file(doc)


@router.get("/{file_id}/download")
async def download_file(file_id: str):
    """Download a file from MinIO using its metadata in Mongo."""
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file id")

    doc = await files_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")

    obj = download_from_minio(doc["path"])

    return StreamingResponse(
        obj,
        media_type=doc.get("mime_type", "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="{doc["name"]}"'
        },
    )


@router.put("/{file_id}", response_model=FileOut)
async def rename_file(file_id: str, payload: FileRename):
    """Rename a file (only change the name field)."""
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file id")

    updated = await files_collection.find_one_and_update(
        {"_id": oid},
        {"$set": {"name": payload.name}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="File not found")

    return _doc_to_file(updated)


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Delete a file:
    - Delete the object in MinIO
    - Delete the metadata in MongoDB
    """
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file id")

    doc = await files_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")

    delete_from_minio(doc["path"])

    result = await files_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Failed to delete file metadata")

    return {"deleted": True}
