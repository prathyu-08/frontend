from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

from models import UserRole, JobStatus


class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# ==========================
# SIGNUP SCHEMAS
# ==========================

class SignupSchema(BaseSchema):
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    role: UserRole
    password: str


class CompleteSignupSchema(BaseSchema):
    cognito_sub: str
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    role: UserRole


# ==========================
# JOB SCHEMAS
# ==========================

class JobCreate(BaseSchema):
    title: str
    description: str
    location: Optional[str] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    employment_type: Optional[str] = None


class JobUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    employment_type: Optional[str] = None
    status: Optional[JobStatus] = None
    is_active: Optional[bool] = None


class JobRead(BaseSchema):
    id: UUID  # ✅ FIXED (was str)
    title: str
    description: str
    location: Optional[str] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    employment_type: Optional[str] = None
    status: JobStatus
    is_active: bool
    created_at: Optional[datetime] = None
