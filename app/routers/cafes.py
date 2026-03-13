from typing import Optional
from fastapi import APIRouter, Query


router = APIRouter()


@router.get("")
async def list_cafes(
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    return {"items": [], "next_cursor": None, "cursor": cursor, "limit": limit}


@router.get("/{slug}")
async def get_cafe(slug: str):
    return {"slug": slug, "message": "Cafe detayi sonraki adimda eklenecek."}
