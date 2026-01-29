import os
from uuid import uuid4

import boto3
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import User, Resume, CandidateProfile
from auth_utils import get_current_user

router = APIRouter(prefix="/resume", tags=["Resume"])

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

if not S3_BUCKET_NAME:
    raise RuntimeError("S3_BUCKET_NAME is not set in environment variables")

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

ALLOWED_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

MAX_FILE_SIZE = 5 * 1024 * 1024  # ✅ 5MB
MAX_RESUMES_PER_USER = 10


def ensure_candidate_profile(db: Session, user: User):
    if user.candidate_profile:
        return user.candidate_profile

    candidate = CandidateProfile(user_id=user.id)
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def safe_presigned_get_url(s3_key: str, expires_in: int = 3600):
    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=expires_in,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate link: {str(e)}")


@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate_profile = ensure_candidate_profile(db, current_user)
    candidate_id = candidate_profile.id

    # ✅ Max 10 resumes check
    count = db.query(Resume).filter(Resume.candidate_id == candidate_id).count()
    if count >= MAX_RESUMES_PER_USER:
        raise HTTPException(status_code=400, detail="Max 10 resumes allowed. Delete one to upload new.")

    # ✅ validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF / DOC / DOCX files allowed.")

    # ✅ validate filename
    if not file.filename or "." not in file.filename:
        raise HTTPException(status_code=400, detail="Invalid file name.")

    ext = file.filename.rsplit(".", 1)[-1].lower()

    # ✅ size check (empty + max)
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size == 0:
        raise HTTPException(status_code=400, detail="Empty file not allowed.")

    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB allowed.")

    # ✅ upload to S3
    s3_key = f"resumes/{candidate_id}/{uuid4()}.{ext}"

    try:
        s3.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": file.content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 Upload Failed: {str(e)}")

    # ✅ save in Resume table + store file name
    new_resume = Resume(
        candidate_id=candidate_id,
        resume_s3_key=s3_key,
        is_primary=False,
        original_filename=file.filename,
        file_size=size,
        content_type=file.content_type,
    )

    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    return {
        "message": "✅ Resume uploaded successfully!",
        "resume_id": str(new_resume.id),
        "s3_key": s3_key,
        "filename": file.filename,
        "size_bytes": size,
        "content_type": file.content_type,
    }


@router.get("/my-resumes")
def my_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate_profile = ensure_candidate_profile(db, current_user)
    candidate_id = candidate_profile.id

    resumes = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate_id)
        .order_by(Resume.uploaded_at.desc())
        .all()
    )

    return {
        "count": len(resumes),
        "resumes": [
            {
                "resume_id": str(r.id),
                "s3_key": r.resume_s3_key,
                "uploaded_at": str(r.uploaded_at),
                "is_primary": bool(getattr(r, "is_primary", False)),
                "filename": getattr(r, "original_filename", None) or "Resume",
                "size_bytes": getattr(r, "file_size", None),
                "content_type": getattr(r, "content_type", None),
            }
            for r in resumes
        ],
    }


@router.get("/share-link")
def share_link(
    resume_id: str = None,
    expires_in: int = 3600,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate_profile = ensure_candidate_profile(db, current_user)
    candidate_id = candidate_profile.id

    if resume_id:
        resume = (
            db.query(Resume)
            .filter(Resume.id == resume_id, Resume.candidate_id == candidate_id)
            .first()
        )
    else:
        resume = (
            db.query(Resume)
            .filter(Resume.candidate_id == candidate_id)
            .order_by(Resume.uploaded_at.desc())
            .first()
        )

    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Upload resume first.")

    url = safe_presigned_get_url(resume.resume_s3_key, expires_in=expires_in)
    return {"share_url": url, "expires_in": expires_in}


@router.post("/set-primary/{resume_id}")
def set_primary_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate_profile = ensure_candidate_profile(db, current_user)
    candidate_id = candidate_profile.id

    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.candidate_id == candidate_id)
        .first()
    )

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    db.query(Resume).filter(Resume.candidate_id == candidate_id).update({"is_primary": False})
    db.commit()

    resume.is_primary = True
    db.commit()
    db.refresh(resume)

    return {"message": "✅ Primary resume updated successfully!", "primary_resume_id": str(resume.id)}


@router.delete("/delete/{resume_id}")
def delete_resume(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate_profile = ensure_candidate_profile(db, current_user)
    candidate_id = candidate_profile.id

    resume = (
        db.query(Resume)
        .filter(Resume.id == resume_id, Resume.candidate_id == candidate_id)
        .first()
    )

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    try:
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=resume.resume_s3_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete resume from S3: {str(e)}")

    db.delete(resume)
    db.commit()

    return {"message": "✅ Resume deleted successfully!"}
