from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID

from db import get_db
from models import Job, Recruiter, User, UserRole
from schemas import JobCreate, JobRead, JobUpdate
from auth_api import decode_cognito_token

router = APIRouter(prefix="/jobs", tags=["Jobs"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ✅ Candidate can view ALL jobs (recruiter posted jobs)
@router.get("/")
def list_all_jobs(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    # token validate (both user/recruiter can view jobs)
    payload = decode_cognito_token(token)
    sub = payload["sub"]

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    jobs = db.query(Job).order_by(Job.created_at.desc()).all()

    result = []
    for j in jobs:
        result.append({
            "job_id": str(j.id),
            "title": j.title,
            "description": j.description,
            "location": j.location,
            "min_experience": j.min_experience,
            "max_experience": j.max_experience,
            "salary_min": j.salary_min,
            "salary_max": j.salary_max,
            "employment_type": j.employment_type,
            "company_name": j.company.name if j.company else ""
        })

    return {"jobs": result}


# ✅ Recruiter creates a job
@router.post("/", response_model=JobRead)
def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    payload = decode_cognito_token(token)
    sub = payload["sub"]

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can post jobs")

    recruiter = db.query(Recruiter).filter(Recruiter.user_id == user.id).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")

    new_job = Job(
        recruiter_id=recruiter.id,
        company_id=recruiter.company_id,
        title=job.title,
        description=job.description,
        location=job.location,
        min_experience=job.min_experience,
        max_experience=job.max_experience,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        employment_type=job.employment_type,
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job


# ✅ Recruiter can view all his jobs
@router.get("/my", response_model=list[JobRead])
def list_my_jobs(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    payload = decode_cognito_token(token)
    sub = payload["sub"]

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can view their jobs")

    recruiter = db.query(Recruiter).filter(Recruiter.user_id == user.id).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")

    jobs = (
        db.query(Job)
        .filter(Job.recruiter_id == recruiter.id)
        .order_by(Job.created_at.desc())
        .all()
    )

    return jobs


# ✅ Recruiter can get a job by job_id
@router.get("/{job_id}", response_model=JobRead)
def get_job_by_id(
    job_id: UUID,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    payload = decode_cognito_token(token)
    sub = payload["sub"]

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    recruiter = db.query(Recruiter).filter(Recruiter.user_id == user.id).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")

    job = db.query(Job).filter(Job.id == job_id, Job.recruiter_id == recruiter.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


# ✅ Recruiter can UPDATE (edit) his job
@router.put("/{job_id}", response_model=JobRead)
def update_job(
    job_id: UUID,
    data: JobUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    payload = decode_cognito_token(token)
    sub = payload["sub"]

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can edit jobs")

    recruiter = db.query(Recruiter).filter(Recruiter.user_id == user.id).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")

    job = db.query(Job).filter(Job.id == job_id, Job.recruiter_id == recruiter.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(job, key, value)

    db.commit()
    db.refresh(job)

    return job


# ✅ Recruiter can DELETE his job after recruitment is done
@router.delete("/{job_id}")
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    payload = decode_cognito_token(token)
    sub = payload["sub"]

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can delete jobs")

    recruiter = db.query(Recruiter).filter(Recruiter.user_id == user.id).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter profile not found")

    job = db.query(Job).filter(Job.id == job_id, Job.recruiter_id == recruiter.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(job)
    db.commit()

    return {"message": "Job deleted successfully ✅"}
