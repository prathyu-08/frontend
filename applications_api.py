from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID

from db import get_db
from models import User, CandidateProfile, Job, Application, UserRole, Resume
from auth_utils import decode_cognito_token

router = APIRouter(prefix="/applications", tags=["Applications"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ✅ Candidate applies to a job (with selected resume)
@router.post("/apply/{job_id}")
def apply_job(
    job_id: UUID,
    resume_id: UUID | None = None,  # ✅ NEW
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    payload = decode_cognito_token(token)
    sub = payload.get("sub")

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role != UserRole.user:
        raise HTTPException(status_code=403, detail="Only candidates can apply jobs")

    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # ✅ prevent duplicate applications
    already = (
        db.query(Application)
        .filter(Application.job_id == job_id, Application.candidate_id == candidate.id)
        .first()
    )
    if already:
        raise HTTPException(status_code=409, detail="You already applied for this job")

    # ✅ Validate resume belongs to this candidate (if provided)
    selected_resume = None
    if resume_id:
        selected_resume = (
            db.query(Resume)
            .filter(Resume.id == resume_id, Resume.candidate_id == candidate.id)
            .first()
        )
        if not selected_resume:
            raise HTTPException(status_code=404, detail="Resume not found or not yours")

    new_app = Application(
        job_id=job_id,
        candidate_id=candidate.id,
        resume_id=resume_id if resume_id else None,  # ✅ NEW
    )

    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    return {
        "message": "Applied successfully ✅",
        "application_id": str(new_app.id),
        "resume_id": str(resume_id) if resume_id else None,
    }


# ✅ Candidate view: my applied jobs list
@router.get("/my")
def my_applications(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    payload = decode_cognito_token(token)
    sub = payload.get("sub")

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role != UserRole.user:
        raise HTTPException(status_code=403, detail="Only candidates can view applications")

    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    apps = (
        db.query(Application)
        .filter(Application.candidate_id == candidate.id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    result = []
    for a in apps:
        # ✅ If your model has updated_at column, return it
        updated_at = None
        if hasattr(a, "updated_at") and getattr(a, "updated_at", None):
            updated_at = a.updated_at.isoformat()

        result.append(
            {
                "application_id": str(a.id),
                "job_id": str(a.job.id),
                "job_title": a.job.title,
                "company_name": a.job.company.name if a.job.company else "",
                "status": str(a.status),
                "applied_at": a.applied_at.isoformat() if a.applied_at else None,
                "updated_at": updated_at,  # ✅ NEW (safe)
                "resume_id": str(a.resume_id) if a.resume_id else None,
            }
        )

    return {"applications": result}


# ✅ NEW: Candidate can withdraw application
@router.delete("/withdraw/{application_id}")
def withdraw_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    payload = decode_cognito_token(token)
    sub = payload.get("sub")

    user = db.query(User).filter(User.cognito_sub == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.role != UserRole.user:
        raise HTTPException(status_code=403, detail="Only candidates can withdraw applications")

    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # ✅ Security: must belong to logged-in candidate
    if str(getattr(app, "candidate_id", "")) != str(candidate.id):
        raise HTTPException(status_code=403, detail="Not allowed to withdraw this application")

    db.delete(app)
    db.commit()

    return {"message": "✅ Application withdrawn successfully", "application_id": str(application_id)}
