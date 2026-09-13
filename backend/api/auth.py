from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.schemas.auth import UserLoginRequest, UserLoginResponse, UserRegisterRequest, UserRegisterResponse, UserAuthSummary
from backend.security import get_current_user, get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserRegisterResponse)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="EMAIL_ALREADY_EXISTS")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role="PROJECT_MANAGER",
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        orig = getattr(exc, "orig", None)
        pgcode = getattr(orig, "pgcode", None)
        err_msg = str(exc).lower()
        if pgcode == "23505" or "email" in err_msg or "unique" in err_msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="EMAIL_ALREADY_EXISTS")
        raise

    return UserRegisterResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


@router.post("/login", response_model=UserLoginResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")

    access_token = create_access_token({"sub": str(user.id)})
    return UserLoginResponse(
        accessToken=access_token,
        tokenType="Bearer",
        user=UserAuthSummary(
            id=user.id,
            name=user.name,
            role=user.role,
        ),
    )

