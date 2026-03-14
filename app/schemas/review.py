from datetime import date, datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(default=None, max_length=200)
    body: Optional[str] = None
    noise_rating: Optional[int] = Field(default=None, ge=1, le=5)
    wifi_rating: Optional[int] = Field(default=None, ge=1, le=5)
    outlet_rating: Optional[int] = Field(default=None, ge=1, le=5)
    visited_at: Optional[date] = None


class VoteCreate(BaseModel):
    vote: Literal["upvote", "downvote", "helpful", "unhelpful"]


class ReviewResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    cafe_id: UUID
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    noise_rating: Optional[int] = None
    wifi_rating: Optional[int] = None
    outlet_rating: Optional[int] = None
    visited_at: Optional[date] = None
    is_verified_visit: bool
    reviewer_name: str
    helpful_count: int = 0
    unhelpful_count: int = 0
    my_vote: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReviewListResponse(BaseModel):
    items: List[ReviewResponse]
    next_cursor: Optional[str] = None
    limit: int
    total_count: int
