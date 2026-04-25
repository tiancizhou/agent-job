from datetime import datetime, timedelta

from fastapi import Cookie, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from database import get_db
from models import Employee, SessionToken, User

SESSION_COOKIE = "quickapp_session"
SESSION_DAYS = 7


def create_session(user: User, db: Session, response: Response, request: Request) -> None:
    session = SessionToken(
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.utcnow() + timedelta(days=SESSION_DAYS),
    )
    db.add(session)
    db.commit()
    response.set_cookie(
        SESSION_COOKIE,
        session.id,
        httponly=True,
        samesite="lax",
        max_age=SESSION_DAYS * 24 * 60 * 60,
    )


def clear_session(session_id: str | None, db: Session, response: Response) -> None:
    if session_id:
        db.query(SessionToken).filter(SessionToken.id == session_id).delete()
        db.commit()
    response.delete_cookie(SESSION_COOKIE)


def get_current_user(
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_db),
) -> User:
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = db.query(SessionToken).filter(SessionToken.id == session_id).first()
    if not session or session.expires_at <= datetime.utcnow():
        if session:
            db.delete(session)
            db.commit()
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Not authenticated")
    employee = db.query(Employee).filter(Employee.employee_no == user.employee_no).first()
    if not employee or employee.status != "active":
        db.delete(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    return user
