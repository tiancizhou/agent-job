from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Style, StyleResponse, User
from services.auth_service import get_current_user

router = APIRouter()


@router.get("/styles", response_model=list[StyleResponse])
def list_styles(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Style)
        .filter(Style.is_active == True)
        .order_by(Style.sort_order.asc(), Style.created_at.desc())
        .all()
    )
