import hashlib
import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, String, Integer, DateTime, Text, ForeignKey
from pydantic import BaseModel
from typing import Optional

from database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest = password_hash.split("$", 1)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()
    return secrets.compare_digest(candidate, digest)


class Employee(Base):
    __tablename__ = "employees"

    employee_no = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    employee_no = Column(String, ForeignKey("employees.employee_no"), nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SessionToken(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class Style(Base):
    __tablename__ = "styles"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class App(Base):
    __tablename__ = "apps"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    style_id = Column(String, ForeignKey("styles.id"), nullable=True)
    name = Column(String, nullable=False, default="新应用")
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default="creating")
    progress = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=0)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=_uuid)
    app_id = Column(String, ForeignKey("apps.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic response schemas

class UserResponse(BaseModel):
    employee_no: str
    is_admin: bool


class EmployeeResponse(BaseModel):
    employee_no: str
    name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AppResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    progress: Optional[str]
    style_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    version: int

    class Config:
        from_attributes = True


class StyleResponse(BaseModel):
    id: str
    name: str
    prompt: str
    sort_order: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    app_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
