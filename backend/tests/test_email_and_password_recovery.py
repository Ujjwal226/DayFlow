from datetime import datetime, timedelta, timezone
import pytest
from app.core.security import generate_secure_token, hash_token
from app.models.security_token import SecurityToken, TokenType
from app.models.user import User


@pytest.fixture
def unverified_user(db_session):
    from app.core.security import hash_password
    user = User(
        email="unverified@example.com",
        display_name="Unverified User",
        hashed_password=hash_password("ValidPassword123!"),
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def verified_user(db_session):
    from app.core.security import hash_password
    user = User(
        email="verified@example.com",
        display_name="Verified User",
        hashed_password=hash_password("ValidPassword123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# --- Email Verification Tests ---

def test_verify_email_success(client, unverified_user, db_session):
    raw_token = generate_secure_token(32)
    token_record = SecurityToken(
        user_id=unverified_user.id,
        token_type=TokenType.EMAIL_VERIFICATION,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(token_record)
    db_session.commit()

    res = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert res.status_code == 200
    assert "verified successfully" in res.json()["message"]

    db_session.refresh(unverified_user)
    assert unverified_user.is_verified is True


def test_verify_email_invalid_token(client):
    res = client.post("/api/v1/auth/verify-email", json={"token": "invalid-token-12345"})
    assert res.status_code == 400
    assert "Invalid or expired" in res.json()["detail"]


def test_verify_email_expired_token(client, unverified_user, db_session):
    raw_token = generate_secure_token(32)
    token_record = SecurityToken(
        user_id=unverified_user.id,
        token_type=TokenType.EMAIL_VERIFICATION,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(token_record)
    db_session.commit()

    res = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert res.status_code == 400
    assert "expired" in res.json()["detail"]


def test_verify_email_token_reuse(client, unverified_user, db_session):
    raw_token = generate_secure_token(32)
    token_record = SecurityToken(
        user_id=unverified_user.id,
        token_type=TokenType.EMAIL_VERIFICATION,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(token_record)
    db_session.commit()

    # First attempt succeeds
    res1 = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert res1.status_code == 200

    # Second attempt fails
    res2 = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert res2.status_code == 400
    assert "already been used" in res2.json()["detail"]


def test_resend_verification_generic_response(client, unverified_user):
    # Existing unverified user
    res1 = client.post("/api/v1/auth/resend-verification", json={"email": unverified_user.email})
    assert res1.status_code == 200
    assert "If an unverified account exists" in res1.json()["message"]

    # Non-existent user returns the identical response
    res2 = client.post("/api/v1/auth/resend-verification", json={"email": "nonexistent@example.com"})
    assert res2.status_code == 200
    assert res1.json()["message"] == res2.json()["message"]


# --- Password Reset Tests ---

def test_forgot_password_generic_response(client, verified_user):
    # Existing user
    res1 = client.post("/api/v1/auth/forgot-password", json={"email": verified_user.email})
    assert res1.status_code == 200
    assert "If an account exists" in res1.json()["message"]

    # Non-existent email returns identical generic response
    res2 = client.post("/api/v1/auth/forgot-password", json={"email": "ghost@example.com"})
    assert res2.status_code == 200
    assert res1.json()["message"] == res2.json()["message"]


def test_reset_password_success(client, verified_user, db_session):
    raw_token = generate_secure_token(32)
    token_record = SecurityToken(
        user_id=verified_user.id,
        token_type=TokenType.PASSWORD_RESET,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
    )
    db_session.add(token_record)
    db_session.commit()

    res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewSecurePassword456!"},
    )
    assert res.status_code == 200
    assert "reset successfully" in res.json()["message"]

    # Verify user can login with new password
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": verified_user.email, "password": "NewSecurePassword456!"},
    )
    assert login_res.status_code == 200


def test_reset_password_invalid_token(client):
    res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "bogus-token-12345", "new_password": "NewSecurePassword456!"},
    )
    assert res.status_code == 400
    assert "Invalid or expired" in res.json()["detail"]


def test_reset_password_expired_token(client, verified_user, db_session):
    raw_token = generate_secure_token(32)
    token_record = SecurityToken(
        user_id=verified_user.id,
        token_type=TokenType.PASSWORD_RESET,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    db_session.add(token_record)
    db_session.commit()

    res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewSecurePassword456!"},
    )
    assert res.status_code == 400
    assert "expired" in res.json()["detail"]


def test_reset_password_revokes_refresh_sessions(client, verified_user, db_session):
    # 1. Login to obtain a refresh token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": verified_user.email, "password": "ValidPassword123!"},
    )
    cookie_token = login_res.cookies["dayflow_refresh_token"]

    # 2. Issue a password reset token
    raw_token = generate_secure_token(32)
    token_record = SecurityToken(
        user_id=verified_user.id,
        token_type=TokenType.PASSWORD_RESET,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
    )
    db_session.add(token_record)
    db_session.commit()

    # 3. Perform password reset
    reset_res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "BrandNewPassword999!"},
    )
    assert reset_res.status_code == 200

    # 4. Old refresh cookie must now be rejected
    refresh_res = client.post(
        "/api/v1/auth/refresh",
        cookies={"dayflow_refresh_token": cookie_token},
        headers={"Origin": "http://localhost:5173"},
    )
    assert refresh_res.status_code == 401




def test_concurrent_token_consumption_simulation(client, unverified_user, db_session):
    """Verify that if two requests attempt to consume the same verification token, only one succeeds."""
    raw_token = generate_secure_token(32)
    token_record = SecurityToken(
        user_id=unverified_user.id,
        token_type=TokenType.EMAIL_VERIFICATION,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(token_record)
    db_session.commit()

    # First consumption succeeds
    res1 = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert res1.status_code == 200

    # Simultaneous second consumption is rejected because token is now marked used
    res2 = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert res2.status_code == 400
    assert "already been used" in res2.json()["detail"]


def test_production_fails_with_development_email_provider():
    """Verify that APP_ENV=production with EMAIL_PROVIDER=development fails startup."""
    from app.core.config import Settings
    settings_prod = Settings(
        APP_ENV="production",
        SECRET_KEY="production-quality-secret-key-that-is-long-enough",
        REFRESH_COOKIE_SECURE=True,
        EMAIL_PROVIDER="development",
    )
    with pytest.raises(ValueError, match="Development email provider cannot be used"):
        settings_prod.validate_security()


def test_revoked_security_token_rejected(client, unverified_user, db_session):
    """Verify explicitly revoked tokens are rejected."""
    raw_token = generate_secure_token(32)
    token_record = SecurityToken(
        user_id=unverified_user.id,
        token_type=TokenType.EMAIL_VERIFICATION,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        revoked_at=datetime.now(timezone.utc),
    )
    db_session.add(token_record)
    db_session.commit()

    res = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
    assert res.status_code == 400
    assert "invalidated" in res.json()["detail"]


def test_raw_token_not_in_database(unverified_user, db_session):
    """Verify raw token is not stored in the database in plaintext."""
    raw_token = "raw-secret-token-value-to-search-for"
    token_record = SecurityToken(
        user_id=unverified_user.id,
        token_type=TokenType.PASSWORD_RESET,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=60),
    )
    db_session.add(token_record)
    db_session.commit()
    db_session.refresh(token_record)

    assert token_record.token_hash != raw_token
    assert raw_token not in repr(token_record)
