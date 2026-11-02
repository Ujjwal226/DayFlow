import time
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User


def test_user_creation(db_session):
    """Test standard user creation with default fields."""
    user = User(
        email="test@example.com",
        display_name="Test User",
        hashed_password="hashed_secure_password_string",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.email == "test@example.com"
    assert user.display_name == "Test User"
    assert user.hashed_password == "hashed_secure_password_string"
    assert user.is_active is True
    assert user.is_verified is False
    assert user.created_at is not None
    assert user.updated_at is not None


def test_user_uuid_generation(db_session):
    """Test that two users receive different unique UUIDs automatically."""
    user1 = User(
        email="user1@example.com",
        display_name="User One",
        hashed_password="hash1",
    )
    user2 = User(
        email="user2@example.com",
        display_name="User Two",
        hashed_password="hash2",
    )
    db_session.add_all([user1, user2])
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)

    assert isinstance(user1.id, uuid.UUID)
    assert isinstance(user2.id, uuid.UUID)
    assert user1.id != user2.id


def test_user_email_uniqueness(db_session):
    """Test that duplicate emails violate unique constraint."""
    user1 = User(
        email="duplicate@example.com",
        display_name="User One",
        hashed_password="hash1",
    )
    db_session.add(user1)
    db_session.commit()

    user2 = User(
        email="duplicate@example.com",
        display_name="User Two",
        hashed_password="hash2",
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_active_and_verified_defaults(db_session):
    """Test that is_active defaults to True and is_verified defaults to False."""
    user = User(
        email="defaults@example.com",
        display_name="Default User",
        hashed_password="hash",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.is_active is True
    assert user.is_verified is False


def test_user_custom_active_and_verified_values(db_session):
    """Test that is_active and is_verified can be set explicitly."""
    user = User(
        email="verified@example.com",
        display_name="Verified User",
        hashed_password="hash",
        is_active=False,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.is_active is False
    assert user.is_verified is True


def test_user_timestamps_and_update(db_session):
    """Test creation and update timestamp behavior."""
    user = User(
        email="timestamp@example.com",
        display_name="Timestamp User",
        hashed_password="hash",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.created_at is not None
    assert user.updated_at is not None
    initial_updated_at = user.updated_at

    # Small delay to ensure timestamp change
    time.sleep(0.01)

    user.display_name = "Updated User Name"
    db_session.commit()
    db_session.refresh(user)

    assert user.display_name == "Updated User Name"
    assert user.updated_at >= initial_updated_at


def test_password_hash_storage(db_session):
    """Test that hashed password is stored as string and preserved exactly."""
    sample_hash = "$2b$12$e8kZ1uIe9xH4kLpQeR7tY.o0XyBqA1wZs5v7g9t1u3p5r7t9u1v3w"
    user = User(
        email="hashcheck@example.com",
        display_name="Hash Check",
        hashed_password=sample_hash,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.hashed_password == sample_hash


def test_user_repr():
    """Test __repr__ does not leak hashed password."""
    user = User(
        id=uuid.uuid4(),
        email="repr@example.com",
        display_name="Repr User",
        hashed_password="secret_hashed_password",
    )
    user_repr = repr(user)
    assert "repr@example.com" in user_repr
    assert "Repr User" in user_repr
    assert "secret_hashed_password" not in user_repr
