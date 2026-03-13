from fastapi import APIRouter, status
from pydantic import BaseModel


router = APIRouter()


class MagicLinkRequest(BaseModel):
    email: str


@router.post("/magic-link", status_code=status.HTTP_202_ACCEPTED)
async def request_magic_link(payload: MagicLinkRequest):
    # Implementation will be wired to auth_tokens + Resend service in next step.
    return {
        "message": "Magic link talebi alindi.",
        "email": payload.email,
        "status": "queued",
    }
