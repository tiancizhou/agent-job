from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Employee, User, UserResponse, hash_password, verify_password
from services.auth_service import SESSION_COOKIE, clear_session, create_session, get_current_user

router = APIRouter()


class AuthRequest(BaseModel):
    employee_no: str
    password: str


@router.post("/auth/register", response_model=UserResponse)
def register(body: AuthRequest, response: Response, db: Session = Depends(get_db)):
    employee_no = body.employee_no.strip()
    employee = db.query(Employee).filter(Employee.employee_no == employee_no).first()
    if not employee or employee.status != "active":
        raise HTTPException(status_code=403, detail="工号未开通")
    existing = db.query(User).filter(User.employee_no == employee_no).first()
    if existing:
        raise HTTPException(status_code=409, detail="账号已注册")
    user = User(employee_no=employee_no, password_hash=hash_password(body.password), is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    create_session(user, db, response)
    return user


@router.post("/auth/login", response_model=UserResponse)
def login(body: AuthRequest, response: Response, db: Session = Depends(get_db)):
    employee_no = body.employee_no.strip()
    user = db.query(User).filter(User.employee_no == employee_no).first()
    employee = db.query(Employee).filter(Employee.employee_no == employee_no).first()
    if not user or not employee or employee.status != "active" or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="工号或密码错误")
    create_session(user, db, response)
    return user


@router.post("/auth/logout")
def logout(
    response: Response,
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_db),
):
    clear_session(session_id, db, response)
    return {"ok": True}


@router.get("/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
