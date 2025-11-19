from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pymongo import ReturnDocument

from app.config import files_collection
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
    """Lista todos los archivos (solo metadata)."""
    docs: list[FileOut] = []
    async for doc in files_collection.find().sort("upload_date", -1):
        docs.append(_doc_to_file(doc))
    return docs


@router.post("/", response_model=FileOut)
async def create_dummy_file():
    dummy_doc = {
        "name": "dummy.txt",
        "size": 0,
        "mime_type": "text/plain",
        "upload_date": datetime.utcnow(),
        "path": "/tmp/dummy.txt",
    }
    result = await files_collection.insert_one(dummy_doc)
    dummy_doc["_id"] = result.inserted_id
    return _doc_to_file(dummy_doc)


@router.put("/{file_id}", response_model=FileOut)
async def rename_file(file_id: str, payload: FileRename):
    """Renombra un archivo (solo cambia el campo name)."""
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
    """Elimina un archivo (por ahora solo metadata en Mongo)."""
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file id")

    result = await files_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="File not found")

    return {"deleted": True}
