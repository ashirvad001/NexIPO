"""
Shared pytest fixtures for NexIPO backend tests.

Provides:
- In-memory SQLite test database (fast, isolated)
- FastAPI TestClient with dependency overrides
- Factory fixtures for creating test users, IPOs, auth headers
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.models.ipo import IPO, IPOStatus, IPOType
from app.models.user import User
from app.services.auth_service import AuthService


# ── In-memory SQLite engine (shared across a test session) ─────────────────

SQLALCHEMY_DATABASE_URL = "sqlite://"  # in-memory

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # required for in-memory SQLite across threads
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Core Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Provide a clean database session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """
    FastAPI TestClient with the database dependency overridden
    to use the in-memory test database.
    """
    from main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Factory Fixtures ───────────────────────────────────────────────────────

@pytest.fixture()
def create_test_user(db_session):
    """Factory fixture to create a test user in the database."""

    def _create(
        email="test@example.com",
        username="testuser",
        password="TestPassword123",
        full_name="Test User",
    ):
        hashed_password = AuthService.get_password_hash(password)
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create


@pytest.fixture()
def test_user(create_test_user):
    """Convenience fixture: a pre-created test user."""
    return create_test_user()


@pytest.fixture()
def auth_headers(test_user):
    """Provide Authorization headers with a valid JWT for the test user."""
    token = AuthService.create_access_token(
        {"sub": str(test_user.id), "email": test_user.email}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def create_test_ipo(db_session):
    """Factory fixture to create a test IPO in the database."""

    def _create(
        company_name="Test Corp Ltd",
        symbol="TESTCORP",
        status=IPOStatus.UPCOMING,
        ipo_type=IPOType.MAINBOARD,
        lot_size=100,
        price_band_upper=150.0,
        price_band_lower=140.0,
        issue_size_rs_cr=500.0,
        retail_subscription=0.0,
        total_subscription=0.0,
        open_date=None,
        close_date=None,
        **kwargs,
    ):
        ipo = IPO(
            company_name=company_name,
            symbol=symbol,
            status=status,
            ipo_type=ipo_type,
            lot_size=lot_size,
            price_band_upper=price_band_upper,
            price_band_lower=price_band_lower,
            issue_size_rs_cr=issue_size_rs_cr,
            retail_subscription=retail_subscription,
            total_subscription=total_subscription,
            open_date=open_date,
            close_date=close_date,
            **kwargs,
        )
        db_session.add(ipo)
        db_session.commit()
        db_session.refresh(ipo)
        return ipo

    return _create


@pytest.fixture()
def test_ipo(create_test_ipo):
    """Convenience fixture: a pre-created test IPO."""
    return create_test_ipo()


@pytest.fixture()
def active_ipo(create_test_ipo):
    """An IPO that is currently open for subscription."""
    return create_test_ipo(
        company_name="Active IPO Corp",
        symbol="ACTIVE",
        status=IPOStatus.OPEN,
        open_date=datetime.now() - timedelta(days=1),
        close_date=datetime.now() + timedelta(days=2),
        retail_subscription=3.5,
        total_subscription=5.2,
        qib_subscription=8.0,
        nii_subscription=2.5,
    )


@pytest.fixture()
def listed_ipo(create_test_ipo):
    """An IPO that has already been listed."""
    return create_test_ipo(
        company_name="Listed Corp",
        symbol="LISTED",
        status=IPOStatus.LISTED,
        issue_price=100.0,
        listing_price=145.0,
        listing_date=datetime.now() - timedelta(days=30),
    )
