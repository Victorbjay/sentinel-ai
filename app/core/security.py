import secrets
from fastapi import Header, HTTPException, status
from app.core.config import settings


async def verify_reviewer_key(
    x_reviewer_key: str = Header(
        default="",
        alias="X-Reviewer-Key",
        description="Accredited fact-checker / observer access key",
    )
) -> str:
    """
    Protects Human-in-the-Loop adjudication endpoints from unauthenticated tampering.
    Uses constant-time comparison against settings.REVIEWER_API_KEY.
    """
    expected = settings.REVIEWER_API_KEY
    if not expected:
        return "open_dev"
    if not x_reviewer_key or not secrets.compare_digest(x_reviewer_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Reviewer-Key. Accredited observer authorization required.",
        )
    return "accredited_reviewer"
