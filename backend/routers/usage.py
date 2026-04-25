from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from database import get_db
from models import App, UsageRecord, UsageRecordResponse, UsageSummaryResponse, User
from services.auth_service import get_current_user

router = APIRouter()


@router.get("/usage/summary", response_model=UsageSummaryResponse)
def get_usage_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = (
        db.query(
            func.coalesce(func.sum(UsageRecord.prompt_tokens), 0),
            func.coalesce(func.sum(UsageRecord.completion_tokens), 0),
            func.coalesce(func.sum(UsageRecord.total_tokens), 0),
            func.count(UsageRecord.id),
            func.coalesce(func.sum(case((UsageRecord.is_estimated == True, 1), else_=0)), 0),
            func.coalesce(func.sum(case((UsageRecord.status == "success", 1), else_=0)), 0),
            func.coalesce(func.sum(case((UsageRecord.status == "failed", 1), else_=0)), 0),
            func.min(UsageRecord.created_at),
            func.max(UsageRecord.created_at),
        )
        .filter(UsageRecord.user_id == current_user.id)
        .one()
    )
    return UsageSummaryResponse(
        prompt_tokens=int(row[0] or 0),
        completion_tokens=int(row[1] or 0),
        total_tokens=int(row[2] or 0),
        record_count=int(row[3] or 0),
        estimated_record_count=int(row[4] or 0),
        successful_record_count=int(row[5] or 0),
        failed_record_count=int(row[6] or 0),
        first_record_at=row[7],
        last_record_at=row[8],
    )


@router.get("/usage/records", response_model=list[UsageRecordResponse])
def list_usage_records(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(UsageRecord, App.name)
        .outerjoin(App, and_(UsageRecord.app_id == App.id, App.user_id == current_user.id))
        .filter(UsageRecord.user_id == current_user.id)
        .order_by(UsageRecord.created_at.desc(), UsageRecord.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        UsageRecordResponse(
            id=record.id,
            app_id=record.app_id,
            app_name=app_name,
            action=record.action,
            provider=record.provider,
            model=record.model,
            prompt_tokens=record.prompt_tokens,
            completion_tokens=record.completion_tokens,
            total_tokens=record.total_tokens,
            cost=float(record.cost or 0),
            is_estimated=record.is_estimated,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        for record, app_name in rows
    ]
