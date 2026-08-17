"""Teams router — read-only list for dropdowns."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.engine import get_session
from app.models.user import User
from app.repositories.team_repo import TeamRepository

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


class TeamResponse(BaseModel):
    """Public team representation."""

    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get(
    "",
    response_model=list[TeamResponse],
)
async def list_teams(
    session: Annotated[AsyncSession, Depends(get_session)],
    _user: Annotated[User, Depends(get_current_user)],
) -> list[TeamResponse]:
    """List all teams (for filter dropdowns and forms)."""
    repo = TeamRepository(session)
    teams = await repo.list_all()
    return [TeamResponse.model_validate(t) for t in teams]
