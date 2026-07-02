from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Health check — no DB, no auth required."""
    return {"status": "ok"}
