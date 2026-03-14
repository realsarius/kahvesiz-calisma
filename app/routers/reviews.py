import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse, VoteCreate
from app.services import review_service


router = APIRouter()


@router.get("/cafes/{cafe_id}/reviews", response_model=ReviewListResponse)
async def list_cafe_reviews(
    cafe_id: uuid.UUID,
    request: Request,
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    current_user = await review_service.get_current_user(request, db, required=False)
    return await review_service.list_reviews(
        cafe_id=cafe_id,
        db=db,
        limit=limit,
        cursor=cursor,
        current_user=current_user,
    )


@router.post(
    "/cafes/{cafe_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cafe_review(
    cafe_id: uuid.UUID,
    payload: ReviewCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    current_user = await review_service.get_current_user(request, db, required=True)
    return await review_service.create_review(
        cafe_id=cafe_id,
        payload=payload,
        current_user=current_user,
        db=db,
    )


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_review(
    review_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    current_user = await review_service.get_current_user(request, db, required=True)
    await review_service.delete_review(
        review_id=review_id,
        current_user=current_user,
        db=db,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reviews/{review_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def vote_review(
    review_id: uuid.UUID,
    payload: VoteCreate,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    current_user = await review_service.get_current_user(request, db, required=True)
    await review_service.upsert_review_vote(
        review_id=review_id,
        payload=payload,
        current_user=current_user,
        db=db,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/reviews/{review_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def unvote_review(
    review_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    current_user = await review_service.get_current_user(request, db, required=True)
    await review_service.delete_review_vote(
        review_id=review_id,
        current_user=current_user,
        db=db,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
