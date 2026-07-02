from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth.auth import get_current_user
from app.database import get_db
from app.services import report_service
from app.templates_setup import templates

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/bench", response_class=HTMLResponse)
def bench_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    items = report_service.get_bench_data(db)
    return templates.TemplateResponse(request, "dashboard/bench.html", {
        "items": items,
    })
