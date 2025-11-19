from datetime import datetime
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.config import folders_collection, files_collection
from app.deps import get_current_user
from app.models import FolderCreate, FolderOut

router = APIRouter(prefix="/folders", tags=["folders"])


def _doc_to_folder(doc) -> FolderOut:
    return FolderOut(
        id=str(doc["_id"]),
        name=doc["name"],
        parent_id=str(doc["parent_id"]) if doc.get("parent_id") else None,
        owner=doc["owner"],
        created_at=doc["created_at"],
    )


@router.get("/", response_model=List[FolderOut])
async def list_folders(current_user: str = Depends(get_current_user)):
    """List all folders for the current user."""
    items: List[FolderOut] = []
    async for doc in folders_collection.find(
        {"owner": current_user}
    ).sort("created_at", 1):
        items.append(_doc_to_folder(doc))
    return items


@router.post("/", response_model=FolderOut)
async def create_folder(
    payload: FolderCreate,
    current_user: str = Depends(get_current_user),
):
    """Create a folder (optionally under parent_id)."""
    parent_oid: Optional[ObjectId] = None

    if payload.parent_id:
        try:
            parent_oid = ObjectId(payload.parent_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid parent_id")

        parent = await folders_collection.find_one(
            {"_id": parent_oid, "owner": current_user}
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent folder not found")

    doc = {
        "name": payload.name,
        "parent_id": parent_oid,
        "owner": current_user,
        "created_at": datetime.utcnow(),
    }

    res = await folders_collection.insert_one(doc)
    doc["_id"] = res.inserted_id
    return _doc_to_folder(doc)


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Delete a folder if it's empty (no subfolders, no files).
    """
    try:
        oid = ObjectId(folder_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid folder_id")

    folder = await folders_collection.find_one({"_id": oid, "owner": current_user})
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    child = await folders_collection.find_one({"parent_id": oid, "owner": current_user})
    if child:
        raise HTTPException(
            status_code=400,
            detail="Folder is not empty (has subfolders)",
        )

    file_doc = await files_collection.find_one({"folder_id": oid, "owner": current_user})
    if file_doc:
        raise HTTPException(
            status_code=400,
            detail="Folder is not empty (has files)",
        )

    await folders_collection.delete_one({"_id": oid, "owner": current_user})
    return {"deleted": True}
