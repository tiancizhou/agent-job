from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import App, Employee, EmployeeResponse, Style, StyleResponse, User
from services.auth_service import require_admin

router = APIRouter()


class EmployeeCreateRequest(BaseModel):
    employee_no: str
    name: str


class StyleCreateRequest(BaseModel):
    name: str
    prompt: str
    sort_order: int = 0


class StyleUpdateRequest(BaseModel):
    name: str | None = None
    prompt: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


@router.get("/admin/employees", response_model=list[EmployeeResponse])
def list_employees(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Employee).order_by(Employee.created_at.desc()).all()


@router.post("/admin/employees", response_model=EmployeeResponse, status_code=201)
def create_employee(
    body: EmployeeCreateRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    employee_no = body.employee_no.strip()
    if db.query(Employee).filter(Employee.employee_no == employee_no).first():
        raise HTTPException(status_code=409, detail="工号已存在")
    employee = Employee(employee_no=employee_no, name=body.name.strip() or employee_no, status="active")
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.post("/admin/employees/{employee_no}/disable", response_model=EmployeeResponse)
def disable_employee(
    employee_no: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(Employee.employee_no == employee_no).first()
    if not employee:
        raise HTTPException(status_code=404, detail="工号不存在")
    employee.status = "disabled"
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/admin/styles", response_model=list[StyleResponse])
def list_admin_styles(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Style).order_by(Style.sort_order.asc(), Style.created_at.desc()).all()


@router.post("/admin/styles", response_model=StyleResponse, status_code=201)
def create_style(
    body: StyleCreateRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    name = body.name.strip()
    prompt = body.prompt.strip()
    if not name or not prompt:
        raise HTTPException(status_code=400, detail="风格名称和提示词不能为空")
    style = Style(name=name, prompt=prompt, sort_order=body.sort_order, is_active=True)
    db.add(style)
    db.commit()
    db.refresh(style)
    return style


@router.put("/admin/styles/{style_id}", response_model=StyleResponse)
def update_style(
    style_id: str,
    body: StyleUpdateRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    style = db.query(Style).filter(Style.id == style_id).first()
    if not style:
        raise HTTPException(status_code=404, detail="风格不存在")
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="风格名称不能为空")
        style.name = name
    if body.prompt is not None:
        prompt = body.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="提示词不能为空")
        style.prompt = prompt
    if body.sort_order is not None:
        style.sort_order = body.sort_order
    if body.is_active is not None:
        style.is_active = body.is_active
    db.commit()
    db.refresh(style)
    return style


@router.delete("/admin/styles/{style_id}")
def delete_style(
    style_id: str,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    style = db.query(Style).filter(Style.id == style_id).first()
    if not style:
        raise HTTPException(status_code=404, detail="风格不存在")
    db.query(App).filter(App.style_id == style_id).update({"style_id": None})
    db.delete(style)
    db.commit()
    return {"ok": True}
