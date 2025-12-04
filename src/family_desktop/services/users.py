from __future__ import annotations

from sqlalchemy import select

from ..database import get_session
from ..models import User
from ..utils.security import hash_password, verify_password


def list_users() -> list[dict]:
    with get_session() as session:
        users = session.scalars(select(User)).all()
        return [user.to_dict() for user in users]


def create_user(username: str, password: str, role: str = "admin") -> dict:
    with get_session() as session:
        if session.scalar(select(User).where(User.username == username)):
            raise ValueError("Username already exists")
        record = User(username=username, password_hash=hash_password(password), role=role)
        session.add(record)
        session.flush()
        return record.to_dict()


def authenticate(username: str, password: str) -> dict | None:
    with get_session() as session:
        user = session.scalar(select(User).where(User.username == username))
        if user and verify_password(password, user.password_hash):
            return user.to_dict()
        return None


def ensure_default_admin() -> None:
    with get_session() as session:
        if session.scalar(select(User.id).limit(1)):
            return
        admin = User(username="admin", password_hash=hash_password("admin123"), role="admin")
        session.add(admin)

