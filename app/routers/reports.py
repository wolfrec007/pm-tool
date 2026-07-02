from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.database import get_db
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/allocations/download")
def download_allocations(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Streaming CSV export of all assignments."""
    generator = report_service.stream_allocation_csv(db)
    return StreamingResponse(
        generator,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=allocations.csv"},
    )
