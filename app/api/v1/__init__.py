"""API v1 — JSON endpoints for the Next.js frontend."""

from fastapi import APIRouter

from app.api.v1 import auth, dashboard, team_members, clients, engagements, assignments, leaves, approval, extensions

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(dashboard.router)
router.include_router(team_members.router)
router.include_router(clients.router)
router.include_router(engagements.router)
router.include_router(assignments.router)
router.include_router(leaves.router)
router.include_router(approval.router)
router.include_router(extensions.router)
