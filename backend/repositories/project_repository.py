from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.project import Project
from backend.models.user import User


def get_project_for_user(db: Session, user: User, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PROJECT_NOT_FOUND")
    if project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return project


def get_project_or_404(db: Session, project_id: int) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()
