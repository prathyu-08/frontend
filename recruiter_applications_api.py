from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
import boto3
import os

from db import get_db
from models import User, UserRole, Job, Application, Resume, Recruiter
from auth_utils import get_current_user

router = APIRouter(prefix="/recruiter/applications", tags=["Recruiter Applications"])

# ✅ FIXED: match resume_api.py env name
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

s3_client = boto3.client("s3", region_name=AWS_REGION)


# ✅ Helper: Get recruiter profile from logged-in user
def get_recruiter_profile(db: Session, current_user: User):
    recruiter_profile = db.query(Recruiter).filter(Recruiter.user_id == current_user.id).first()
    return recruiter_profile


# ✅ Helper: Find candidate/user id field in Application safely
def get_application_candidate_id(app: Application):
    if hasattr(app, "candidate_id"):
        return getattr(app, "candidate_id")
    if hasattr(app, "user_id"):
        return getattr(app, "user_id")
    return None


# ✅ Helper: Generate Presigned URL for Resume
def generate_presigned_resume_url(resume: Resume):
    if not resume or not getattr(resume, "resume_s3_key", None):
        return None

    # ✅ FIXED: use correct bucket name
    if not S3_BUCKET_NAME:
        return None

    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": resume.resume_s3_key},
            ExpiresIn=3600,
        )
        return url
    except Exception as e:
        print("Presigned URL Error:", e)
        return None


# ✅ 1) View applications for a job (Recruiter Only)
@router.get("/job/{job_id}")
def view_applications_for_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ✅ Only recruiter allowed
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters allowed")

    recruiter_profile = get_recruiter_profile(db, current_user)
    if not recruiter_profile:
        raise HTTPException(status_code=403, detail="Recruiter profile not found")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # ✅ Ownership check fixed
    if job.recruiter_id != recruiter_profile.id:
        raise HTTPException(status_code=403, detail="Not allowed to view applicants for this job")

    applications = db.query(Application).filter(Application.job_id == job_id).all()

    results = []
    for app in applications:
        resume_url = None
        resume_id = getattr(app, "resume_id", None)

        if resume_id:
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            resume_url = generate_presigned_resume_url(resume)

        candidate_id = get_application_candidate_id(app)

        # ✅ FIX: Fetch candidate email using candidate_id
        candidate_email = "-"
        if candidate_id:
            candidate_user = db.query(User).filter(User.id == candidate_id).first()
            if candidate_user and getattr(candidate_user, "email", None):
                candidate_email = candidate_user.email

        results.append(
            {
                "application_id": str(app.id),
                "job_id": str(app.job_id),

                "candidate_id": str(candidate_id) if candidate_id else None,
                "candidate_email": candidate_email,  # ✅ ADDED

                "resume_id": str(resume_id) if resume_id else None,
                "resume_url": resume_url,

                "status": str(getattr(app, "status", "applied")),
                "applied_at": app.applied_at.isoformat() if getattr(app, "applied_at", None) else None,
            }
        )

    return {
        "job_id": str(job.id),
        "job_title": job.title,
        "applications": results,
        "count": len(results),
    }


# ✅ 2) Update application status (Recruiter Only)
@router.put("/{application_id}/status")
def update_application_status(
    application_id: UUID,
    status: str = Query(..., description="New status (applied, shortlisted, rejected, hired...)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters allowed")

    recruiter_profile = get_recruiter_profile(db, current_user)
    if not recruiter_profile:
        raise HTTPException(status_code=403, detail="Recruiter profile not found")

    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    job = db.query(Job).filter(Job.id == app.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # ✅ Ownership check fixed
    if job.recruiter_id != recruiter_profile.id:
        raise HTTPException(status_code=403, detail="Not allowed to update this application")

    app.status = status
    db.commit()
    db.refresh(app)

    return {
        "message": "Status updated ✅",
        "application_id": str(app.id),
        "status": str(app.status),
    }
