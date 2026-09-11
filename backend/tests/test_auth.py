import uuid
from datetime import timedelta

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.database import SessionLocal
from backend.main import app
from backend.models.user import User
from backend.security import ALGORITHM, SECRET_KEY, create_access_token, get_current_user


def _unique_email(prefix: str = "student") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def _cleanup_user_by_email(email: str) -> None:
    with SessionLocal() as db:
        db.query(User).filter(User.email == email).delete()
        db.commit()


def test_successful_registration():
    email = _unique_email("register")
    payload = {"name": "Student", "email": email, "password": "password123"}

    try:
        response = TestClient(app).post("/api/auth/register", json=payload)
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["name"] == "Student"
        assert body["email"] == email
        assert body["role"] == "PROJECT_MANAGER"
        assert "password" not in body
    finally:
        _cleanup_user_by_email(email)


def test_password_is_hashed_not_plaintext():
    email = _unique_email("hash")
    payload = {"name": "Student", "email": email, "password": "password123"}

    try:
        response = TestClient(app).post("/api/auth/register", json=payload)
        assert response.status_code == 201, response.text

        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).one()
            assert user.password_hash != "password123"
            assert user.password_hash.startswith("$2b$")
    finally:
        _cleanup_user_by_email(email)


def test_duplicate_email_returns_409_email_already_exists():
    email = _unique_email("duplicate")
    payload = {"name": "Student", "email": email, "password": "password123"}
    client = TestClient(app)

    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201, first.text

    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 409, second.text
    assert second.json()["detail"] == "EMAIL_ALREADY_EXISTS"

    _cleanup_user_by_email(email)


def test_successful_login():
    email = _unique_email("login")
    payload = {"name": "Student", "email": email, "password": "password123"}
    client = TestClient(app)

    try:
        register = client.post("/api/auth/register", json=payload)
        assert register.status_code == 201, register.text

        response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["tokenType"] == "Bearer"
        assert body["user"]["id"] > 0
        assert body["user"]["name"] == "Student"
        assert body["user"]["role"] == "PROJECT_MANAGER"
        assert body["accessToken"]
    finally:
        _cleanup_user_by_email(email)


def test_invalid_password_returns_401_invalid_credentials():
    email = _unique_email("badpass")
    payload = {"name": "Student", "email": email, "password": "password123"}
    client = TestClient(app)

    try:
        register = client.post("/api/auth/register", json=payload)
        assert register.status_code == 201, register.text

        response = client.post("/api/auth/login", json={"email": email, "password": "wrong-password"})
        assert response.status_code == 401, response.text
        assert response.json()["detail"] == "INVALID_CREDENTIALS"
    finally:
        _cleanup_user_by_email(email)


def test_missing_authorization_header_returns_401():
    protected_app = FastAPI()

    @protected_app.get("/protected")
    def protected(current_user=Depends(get_current_user)):
        return {"id": current_user.id}

    response = TestClient(protected_app).get("/protected")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_invalid_jwt_returns_401():
    protected_app = FastAPI()

    @protected_app.get("/protected")
    def protected(current_user=Depends(get_current_user)):
        return {"id": current_user.id}

    response = TestClient(protected_app).get(
        "/protected",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "INVALID_TOKEN"


def test_expired_jwt_returns_401():
    protected_app = FastAPI()

    @protected_app.get("/protected")
    def protected(current_user=Depends(get_current_user)):
        return {"id": current_user.id}

    email = _unique_email("expired")
    payload = {"name": "Student", "email": email, "password": "password123"}

    try:
        register = TestClient(app).post("/api/auth/register", json=payload)
        assert register.status_code == 201, register.text

        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).one()
            token = create_access_token({"sub": str(user.id)}, expires_delta=timedelta(minutes=-5))

        response = TestClient(protected_app).get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "TOKEN_EXPIRED"
    finally:
        _cleanup_user_by_email(email)


def test_valid_bearer_token_resolves_correct_user():
    protected_app = FastAPI()

    @protected_app.get("/protected")
    def protected(current_user=Depends(get_current_user)):
        return {"id": current_user.id, "name": current_user.name, "email": current_user.email}

    email = _unique_email("token")
    payload = {"name": "Student", "email": email, "password": "password123"}

    try:
        register = TestClient(app).post("/api/auth/register", json=payload)
        assert register.status_code == 201, register.text

        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).one()
            token = create_access_token({"sub": str(user.id)})

        response = TestClient(protected_app).get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["email"] == email
        assert body["name"] == "Student"
    finally:
        _cleanup_user_by_email(email)
