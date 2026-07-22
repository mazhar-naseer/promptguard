from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.detection import analyze_prompt
from app.services.auth import get_current_user
from app.core.rate_limit import limiter
from app.core.config import settings

router = APIRouter()


@router.post("/api/analyze", response_model=AnalyzeResponse)
@limiter.limit(settings.rate_limit_anonymous)
async def analyze(
    request: Request,
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    user_id = user.id if user else None
    result = await analyze_prompt(db, payload.prompt, user_id=user_id)
    return result
