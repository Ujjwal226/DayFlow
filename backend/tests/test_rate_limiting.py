import concurrent.futures
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.rate_limit import RateLimitRecord, RateLimitScope
from app.models.user import User
from app.repositories.rate_limit_repository import RateLimitRepository
from app.services.rate_limit_service import RateLimitService


@pytest.fixture
def verified_user(db_session: Session) -> User:
    user = User(
        email="verified_ratelimit@example.com",
        display_name="Rate Limit User",
        hashed_password=hash_password("ValidPassword123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_ip_rate_limit_enforcement(client: TestClient, verified_user: User, monkeypatch):
    """Verify that more than 3 requests within 15 minutes from the same IP result in HTTP 429."""
    # When testclient is a trusted proxy, X-Forwarded-For is honored
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", ["testclient", "127.0.0.1"])
    headers = {"X-Forwarded-For": "203.0.113.195"}

    # Requests 1, 2, 3 should succeed
    for i in range(3):
        res = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": f"test{i}@example.com"},
            headers=headers,
        )
        assert res.status_code == 200, f"Request {i+1} should succeed"
        assert "If an account exists" in res.json()["message"]

    # 4th request from same IP must be throttled with HTTP 429
    res4 = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "another@example.com"},
        headers=headers,
    )
    assert res4.status_code == 429
    assert "Too many requests" in res4.json()["detail"]
    assert "Retry-After" in res4.headers
    retry_after = int(res4.headers["Retry-After"])
    assert retry_after > 0

    # Resend verification from the same IP should also be throttled (or vice versa if using separate or same IP tracker)
    res_resend = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "unverified@example.com"},
        headers=headers,
    )
    # Different action: if using different action names ("resend_verification" vs "forgot_password"), each has its own budget or shared
    # In our implementation action="resend_verification" has 3 requests as well
    assert res_resend.status_code == 200

    # Exhaust resend_verification for this IP
    client.post("/api/v1/auth/resend-verification", json={"email": "u1@example.com"}, headers=headers)
    client.post("/api/v1/auth/resend-verification", json={"email": "u2@example.com"}, headers=headers)
    res_resend_blocked = client.post(
        "/api/v1/auth/resend-verification", json={"email": "u3@example.com"}, headers=headers
    )
    assert res_resend_blocked.status_code == 429
    assert "Retry-After" in res_resend_blocked.headers


def test_email_cooldown_enforcement(client: TestClient, verified_user: User, db_session: Session, monkeypatch):
    """
    Verify that multiple requests for the same email from different IPs suppress duplicate email dispatch
    while returning identical generic responses.
    """
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", ["testclient", "127.0.0.1"])
    target_email = verified_user.email

    # Request 1 from IP 1
    res1 = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": target_email},
        headers={"X-Forwarded-For": "198.51.100.1"},
    )
    assert res1.status_code == 200
    msg1 = res1.json()["message"]

    # Request 2 from IP 2 (so IP rate limit is not tripped)
    res2 = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": target_email},
        headers={"X-Forwarded-For": "198.51.100.2"},
    )
    assert res2.status_code == 200
    msg2 = res2.json()["message"]

    # Generic message must be identical
    assert msg1 == msg2

    # Verify that the email cooldown record exists and count is 1 (second attempt was suppressed)
    repo = RateLimitRepository(db_session)
    ident_hash = repo.hash_identifier(target_email.lower())
    record = repo.get_for_update("forgot_password", RateLimitScope.EMAIL, ident_hash)
    assert record is not None
    assert record.request_count == 1


def test_cooldown_expiration_allows_new_request(db_session: Session):
    """Verify that after the cooldown period has expired, a new request is permitted."""
    repo = RateLimitRepository(db_session)
    service = RateLimitService(db_session)

    test_email = "cooldown_expire_test@example.com"
    base_time = datetime(2026, 11, 3, 12, 0, 0, tzinfo=timezone.utc)

    # First request at base_time: allowed
    allowed1 = service.check_and_apply_email_cooldown(test_email, action="test_action", now=base_time)
    assert allowed1 is True

    # Immediate second request: blocked by cooldown
    allowed2 = service.check_and_apply_email_cooldown(test_email, action="test_action", now=base_time + timedelta(seconds=30))
    assert allowed2 is False

    # Third request after cooldown expires (e.g. +3 minutes, cooldown default is 2 minutes)
    future_time = base_time + timedelta(minutes=settings.AUTH_EMAIL_COOLDOWN_PER_EMAIL_MINUTES + 1)
    allowed3 = service.check_and_apply_email_cooldown(test_email, action="test_action", now=future_time)
    assert allowed3 is True


def test_concurrent_rate_limit_increments(db_session: Session):
    """
    Verify that concurrent threads hitting check_and_increment for the same IP
    cannot bypass the rate limit due to database row locking (with_for_update).
    """
    # SQLite does not support PostgreSQL's ON CONFLICT DO NOTHING or row-level FOR UPDATE
    # between separate connections in the same test transaction. If in SQLite, verify the repository logic.
    raw_ip = "192.0.2.100"
    max_requests = 3
    window_minutes = 15

    # Check dialect
    bind = db_session.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        results = []

        def make_attempt():
            db = SessionLocal()
            try:
                repo = RateLimitRepository(db)
                allowed, count, retry = repo.check_and_increment(
                    action="concurrent_test",
                    scope=RateLimitScope.CLIENT_IP,
                    raw_identifier=raw_ip,
                    max_requests=max_requests,
                    window_minutes=window_minutes,
                )
                db.commit()
                return allowed
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(make_attempt) for _ in range(6)]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        assert results.count(True) == max_requests
        assert results.count(False) == 3
    else:
        # For SQLite in-memory test database, test sequential increments ensuring limit cutoff
        repo = RateLimitRepository(db_session)
        results = []
        for _ in range(6):
            allowed, count, retry = repo.check_and_increment(
                action="concurrent_test",
                scope=RateLimitScope.CLIENT_IP,
                raw_identifier=raw_ip,
                max_requests=max_requests,
                window_minutes=window_minutes,
            )
            results.append(allowed)
        assert results.count(True) == max_requests
        assert results.count(False) == 3


def test_generic_responses_for_existing_and_nonexistent_email(client: TestClient, verified_user: User):
    """
    Verify that response statuses, messages, and schemas are identical
    for registered existing vs non-existent accounts under rate-limited flows.
    """
    ip_headers = {"X-Forwarded-For": "198.51.100.99"}

    # Forgot password
    res_existing = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": verified_user.email},
        headers=ip_headers,
    )
    res_nonexistent = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "completely_imaginary_987@example.com"},
        headers=ip_headers,
    )
    assert res_existing.status_code == 200
    assert res_nonexistent.status_code == 200
    assert res_existing.json() == res_nonexistent.json()

    # Resend verification
    ip_headers2 = {"X-Forwarded-For": "198.51.100.100"}
    res_v_existing = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": verified_user.email},
        headers=ip_headers2,
    )
    res_v_nonexistent = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "nonexistent_verification_456@example.com"},
        headers=ip_headers2,
    )
    assert res_v_existing.status_code == 200
    assert res_v_nonexistent.status_code == 200
    assert res_v_existing.json() == res_v_nonexistent.json()


def test_cleanup_expired_rate_limit_records(db_session: Session):
    """Verify cleanup_expired successfully purges old windows without affecting active ones."""
    repo = RateLimitRepository(db_session)
    now = datetime.now(timezone.utc)

    # Insert an expired record
    expired_record = RateLimitRecord(
        action="cleanup_test",
        scope=RateLimitScope.CLIENT_IP,
        identifier_hash=repo.hash_identifier("10.0.0.1"),
        request_count=3,
        window_start=now - timedelta(minutes=30),
        expires_at=now - timedelta(minutes=15),
    )
    # Insert an active record
    active_record = RateLimitRecord(
        action="cleanup_test",
        scope=RateLimitScope.CLIENT_IP,
        identifier_hash=repo.hash_identifier("10.0.0.2"),
        request_count=1,
        window_start=now,
        expires_at=now + timedelta(minutes=15),
    )
    db_session.add_all([expired_record, active_record])
    db_session.commit()

    deleted = repo.cleanup_expired(now=now)
    db_session.commit()
    assert deleted >= 1

    # Active record should still be in database
    active_in_db = repo.get_for_update("cleanup_test", RateLimitScope.CLIENT_IP, repo.hash_identifier("10.0.0.2"))
    assert active_in_db is not None


# --- A. RATE_LIMIT_SALT Security Tests ---

def test_production_fails_with_missing_rate_limit_salt():
    """Ensure validate_security fails when RATE_LIMIT_SALT is empty in production."""
    from app.core.config import Settings
    s = Settings(
        APP_ENV="production",
        SECRET_KEY="a-very-secure-secret-key-for-prod-testing",
        REFRESH_COOKIE_SECURE=True,
        EMAIL_PROVIDER="smtp",
        RATE_LIMIT_SALT="",
    )
    with pytest.raises(ValueError, match="RATE_LIMIT_SALT"):
        s.validate_security()


def test_production_fails_with_default_rate_limit_salt():
    """Ensure validate_security fails when default development salt is used in production."""
    from app.core.config import Settings
    s = Settings(
        APP_ENV="production",
        SECRET_KEY="a-very-secure-secret-key-for-prod-testing",
        REFRESH_COOKIE_SECURE=True,
        EMAIL_PROVIDER="smtp",
        RATE_LIMIT_SALT="dayflow-rate-limit-salt-change-me",
    )
    with pytest.raises(ValueError, match="RATE_LIMIT_SALT"):
        s.validate_security()


def test_production_fails_with_short_rate_limit_salt():
    """Ensure validate_security fails when salt is shorter than 16 characters in production."""
    from app.core.config import Settings
    s = Settings(
        APP_ENV="production",
        SECRET_KEY="a-very-secure-secret-key-for-prod-testing",
        REFRESH_COOKIE_SECURE=True,
        EMAIL_PROVIDER="smtp",
        RATE_LIMIT_SALT="short-salt",
    )
    with pytest.raises(ValueError, match="RATE_LIMIT_SALT"):
        s.validate_security()


def test_production_succeeds_with_strong_rate_limit_salt():
    """Ensure validate_security succeeds when a strong, custom salt is provided in production."""
    from app.core.config import Settings
    s = Settings(
        APP_ENV="production",
        SECRET_KEY="a-very-secure-secret-key-for-prod-testing",
        REFRESH_COOKIE_SECURE=True,
        EMAIL_PROVIDER="smtp",
        RATE_LIMIT_SALT="super-secret-production-salt-at-least-16-chars",
    )
    # Should not raise any ValueError
    s.validate_security()


def test_development_allows_default_rate_limit_salt():
    """Ensure development environment permits the default placeholder salt."""
    from app.core.config import Settings
    s = Settings(
        APP_ENV="development",
        RATE_LIMIT_SALT="dayflow-rate-limit-salt-change-me",
    )
    # Should not raise
    s.validate_security()


# --- B. Client IP & Trusted Proxy Security Tests ---

def test_untrusted_proxy_spoofed_forwarded_headers_ignored(client: TestClient, monkeypatch):
    """
    Verify that if the immediate client is NOT a trusted proxy, arbitrary
    X-Forwarded-For and X-Real-IP headers are ignored, using direct peer IP instead.
    """
    # Configure trusted proxies with an unrelated IP, so 'testclient' is untrusted
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", ["10.0.0.1"])

    # Attempt to spoof 4 different client IPs via X-Forwarded-For
    # Since testclient is untrusted, all 4 requests are attributed to 'testclient' peer IP
    for i in range(3):
        res = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": f"spoof{i}@example.com"},
            headers={"X-Forwarded-For": f"198.51.100.{i+10}"},
        )
        assert res.status_code == 200

    # 4th request with yet another spoofed IP must be blocked because direct peer 'testclient' exceeded 3
    res_blocked = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "spoof_blocked@example.com"},
        headers={"X-Forwarded-For": "198.51.100.99"},
    )
    assert res_blocked.status_code == 429
    assert "Too many requests" in res_blocked.json()["detail"]


def test_trusted_proxy_honors_forwarded_for_header(client: TestClient, monkeypatch):
    """
    Verify that when the connection comes from a trusted proxy, the forwarded
    client IP is honored to differentiate downstream clients.
    """
    # Trust the test client
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", ["testclient"])

    # 3 requests from Client A
    for i in range(3):
        res = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": f"clientA_{i}@example.com"},
            headers={"X-Forwarded-For": "203.0.113.10"},
        )
        assert res.status_code == 200

    # Client A's 4th request is throttled
    res_client_a_blocked = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "clientA_blocked@example.com"},
        headers={"X-Forwarded-For": "203.0.113.10"},
    )
    assert res_client_a_blocked.status_code == 429

    # But Client B from behind the same trusted proxy is NOT throttled
    res_client_b = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "clientB@example.com"},
        headers={"X-Forwarded-For": "203.0.113.20"},
    )
    assert res_client_b.status_code == 200

