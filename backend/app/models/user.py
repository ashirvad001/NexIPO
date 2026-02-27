from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.db.database import Base


class UserRole(PyEnum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default=UserRole.user.value, nullable=False)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    designation = Column(String(255), nullable=True)
    bio = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - simple helper
        return f"<User id={self.id} email={self.email} username={self.username}>"
