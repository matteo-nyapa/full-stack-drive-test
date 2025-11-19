from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pymongo import ReturnDocument

from app.config import files_collection, folders_collection
from app.deps import get_current_user
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
        folder_id=str(doc["folder_id"]) if doc.get("folder_id") else None,
        owner=doc["owner"],
    )


@router.get("/", response_model=List[FileOut])
async def list_files(
    folder_id: Optional[str] = Query(
        default=None, description="Filter by folder id (null = root)"
    ),
    q: Optional[str] = Query(
        default=None, description="Search by file name (substring, case-insensitive)"
    ),
    current_user: str = Depends(get_current_user),
):
    """
    List files for the authenticated user, optionally filtered by folder and name.
    """
    query: dict = {"owner": current_user}

    if folder_id is not None:
        if folder_id == "root":
            query["folder_id"] = None
        else:
            try:
                oid = ObjectId(folder_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid folder_id")
            query["folder_id"] = oid

    if q:
        query["name"] = {"$regex": q, "$options": "i"}

    items: List[FileOut] = []
    async for doc in files_collection.find(query).sort("upload_date", -1):
        items.append(_doc_to_file(doc))
    return items


@router.post("/", response_model=FileOut)
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(default=None),
    current_user: str = Depends(get_current_user),
):
    """
    Upload a file for the authenticated user.
    Optionally associate it with a folder.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="File has no name")

    object_name = f"{uuid4()}-{file.filename}"

    await upload_to_minio(file, object_name)

    upload_date = datetime.utcnow()
    dummy_size = 0

    folder_oid: Optional[ObjectId] = None
    if folder_id:
        if folder_id != "root":
            try:
                folder_oid = ObjectId(folder_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid folder id")

            folder = await folders_collection.find_one(
                {"_id": folder_oid, "owner": current_user}
            )
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")

    doc = {
        "name": file.filename,
        "size": dummy_size,
        "mime_type": file.content_type or "application/octet-stream",
        "upload_date": upload_date,
        "path": object_name,
        "folder_id": folder_oid,
        "owner": current_user,
    }

    result = await files_collection.insert_one(doc)
    doc["_id"] = result.inserted_id

    return _doc_to_file(doc)


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: str = Depends(get_current_user),
):
    """Download a file for the authenticated user."""
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file id")

    doc = await files_collection.find_one({"_id": oid, "owner": current_user})
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
async def rename_file(
    file_id: str,
    payload: FileRename,
    current_user: str = Depends(get_current_user),
):
    """Rename a file for the authenticated user."""
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file id")

    updated = await files_collection.find_one_and_update(
        {"_id": oid, "owner": current_user},
        {"$set": {"name": payload.name}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="File not found")

    return _doc_to_file(updated)


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: str = Depends(get_current_user),
):
    """Delete a file for the authenticated user."""
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file id")

    doc = await files_collection.find_one({"_id": oid, "owner": current_user})
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")

    delete_from_minio(doc["path"])

    result = await files_collection.delete_one({"_id": oid, "owner": current_user})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete file metadata",
        )

    return {"deleted": True}
