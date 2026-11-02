# DayFlow — Authentication Architecture Documentation

## 1. Overview & System Design

DayFlow implements a multi-tenant, production-grade authentication and session management architecture built upon:
- **Argon2id password hashing** using `pwdlib`.
- **Stateless signed JWT access tokens** (short-lived, 15 minutes default).
- **Cryptographically random refresh tokens** (7 days default) stored as SHA-256 hashes in PostgreSQL.
- **HttpOnly, SameSite, Secure cookies** for refresh-token delivery.
- **Refresh-token rotation and token-family reuse detection** to mitigate token theft and replay attacks.
- **CSRF / Origin validation** on state-changing cookie-authenticated endpoints.

---

## 2. Authentication Flows

### A. Registration Flow (`POST /api/v1/auth/register`)
```
Client                          API Endpoint                           Database (PostgreSQL)
  |                                   |                                          |
  |--- POST /auth/register ---------->|                                          |
  |    (email, name, password)        |--- Validate email format & password ----->|
  |                                   |--- Check if email already exists -------->|
  |                                   |    (reject 409 if duplicate)             |
  |                                   |--- Hash password with Argon2id ---------->|
  |                                   |--- Insert new User record -------------->|
  |                                   |    (id=UUID, is_active=True,             |
  |                                   |     is_verified=False)                   |
  |<-- 201 Created -------------------|                                          |
  |    (Safe UserResponse)            |                                          |
```

1. **Email normalization**: Strips whitespace and normalizes to lowercase.
2. **Password complexity**: Validated via Pydantic schemas (min 8 characters, at least 1 letter, at least 1 digit).
3. **Argon2id hashing**: Raw passwords never touch database records or logs.
4. **Safe response**: `hashed_password` is strictly omitted from output schemas.

---

### B. Login Flow (`POST /api/v1/auth/login`)
```
Client                          API Endpoint                           Database (PostgreSQL)
  |                                   |                                          |
  |--- POST /auth/login ------------->|                                          |
  |    (email, password)              |--- Fetch User by normalized email ------>|
  |                                   |--- Verify Argon2id password hash ------->|
  |                                   |    (reject 401 if invalid/not found)     |
  |                                   |    (reject 403 if inactive)              |
  |                                   |--- Mint JWT Access Token (15 min) ------>|
  |                                   |--- Generate secure random refresh token->|
  |                                   |--- Store SHA-256 hash in refresh_tokens->|
  |                                   |    (new family_id=UUID)                  |
  |<-- 200 OK ------------------------|                                          |
  |    Body: { access_token, ... }    |                                          |
  |    Set-Cookie: dayflow_refresh_token (HttpOnly, SameSite=Lax, Path=/api/v1/auth)
```

1. **Constant-time / generic errors**: Unknown emails and invalid passwords both yield `401 Unauthorized: Invalid email or password.`
2. **Access token**: JWT signed with `HS256` and secret key, containing claims (`sub`: user UUID, `jti`: token UUID, `iat`, `exp`, `type`: `access`).
3. **Refresh token cookie**: Emitted strictly in an HttpOnly cookie and never exposed in the JSON response body.

---

### C. Refresh-Token Rotation & Reuse Detection (`POST /api/v1/auth/refresh`)
```
Client                          API Endpoint                           Database (PostgreSQL)
  |                                   |                                          |
  |--- POST /auth/refresh ----------->|                                          |
  |    Cookie: dayflow_refresh_token  |--- Check Origin / Referer (CSRF) --------|
  |    Header: Origin: ...            |--- Compute SHA-256 hash ----------------->|
  |                                   |--- SELECT ... FOR UPDATE (Lock row) ----->|
  |                                   |                                          |
  |    [Scenario 1: Token already revoked (THEFT DETECTED)]                      |
  |                                   |--- Revoke ALL tokens in family_id ------>|
  |                                   |--- Commit & Return 401 Unauthorized ---->|
  |                                   |                                          |
  |    [Scenario 2: Valid Active Token]                                          |
  |                                   |--- Verify user still active ------------>|
  |                                   |--- Mint new JWT access token ----------->|
  |                                   |--- Generate new random refresh token --->|
  |                                   |--- Store new hash with SAME family_id --->|
  |                                   |--- Mark old token revoked & link --------|
  |                                   |    (replaced_by_id = new_token.id)       |
  |<-- 200 OK ------------------------|                                          |
  |    Body: { access_token, ... }    |                                          |
  |    Set-Cookie: dayflow_refresh_token (new token)                             |
```

- **Pessimistic concurrency protection**: Rows are fetched using `with_for_update()` to prevent race conditions during concurrent refresh requests.
- **Family revocation**: If an attacker attempts to replay an old refresh token, DayFlow detects reuse, immediately revokes the entire `family_id` hierarchy, and forces re-authentication.

---

### D. Logout & Logout-All Flow
- **`POST /api/v1/auth/logout`**:
  - Hashes the refresh token from the cookie and marks the record `revoked_at = now()`.
  - Clears the cookie with matching attributes (`Max-Age=0`).
  - Safe and idempotent; succeeds even if cookie is absent or expired.
- **`POST /api/v1/auth/logout-all`**:
  - Protected endpoint requiring a valid JWT access token.
  - Revokes all active refresh tokens for `current_user.id` across all devices.
  - Clears the caller's cookie.

---

### E. Protected Routes (`get_current_user` Dependency)
- Validates the `Authorization: Bearer <JWT>` header.
- Asserts algorithm, expiration, token type (`type == 'access'`), and subject.
- Loads user from PostgreSQL; verifies `user.is_active is True`.
- Injects validated `User` model into endpoint parameters.

---

## 3. Database Schema: `refresh_tokens`

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | `UUID` | `False` | Primary Key |
| `user_id` | `UUID` | `False` | Foreign Key (`users.id`, `ON DELETE CASCADE`), indexed |
| `token_hash` | `VARCHAR(64)` | `False` | SHA-256 hash of random token, unique index |
| `family_id` | `UUID` | `False` | Family identifier for token rotation, indexed |
| `expires_at` | `TIMESTAMP WITH TIME ZONE` | `False` | Expiration timestamp, indexed |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | `False` | Creation timestamp (`server_default=now()`) |
| `revoked_at` | `TIMESTAMP WITH TIME ZONE` | `True` | Revocation timestamp |
| `replaced_by_id` | `UUID` | `True` | Foreign Key (`refresh_tokens.id`, `ON DELETE SET NULL`) |
| `last_used_at` | `TIMESTAMP WITH TIME ZONE` | `True` | Last usage timestamp |

---

## 4. Security & Environment Configuration

| Setting | Type | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | `str` | `insecure-...` | HMAC signing key (validated against defaults in production) |
| `JWT_ALGORITHM` | `str` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | `15` | Lifetime of access tokens |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `int` | `7` | Lifetime of refresh tokens |
| `REFRESH_COOKIE_NAME` | `str` | `dayflow_refresh_token` | Name of HttpOnly cookie |
| `REFRESH_COOKIE_SECURE` | `bool` | `False` | Enforce HTTPS cookies (required `True` in production) |
| `REFRESH_COOKIE_SAMESITE` | `str` | `lax` | SameSite cookie policy |
| `REFRESH_COOKIE_PATH` | `str` | `/api/v1/auth` | Path restricting cookie transmission |
| `BACKEND_CORS_ORIGINS` | `list` | `["http://localhost:5173", ...]` | Explicit allowed origins for CORS & CSRF checks |


---

## 5. Email Verification & Password Recovery (Implementation 1B.4)

### A. Provider-Independent Architecture
DayFlow decouples email generation from transmission using the `EmailProvider` interface in `backend/app/services/email_service.py`:
- **Development**: `DevelopmentEmailProvider` outputs verification and password reset links to console/logs without making external requests.
- **Production Guard**: Application startup actively verifies `EMAIL_PROVIDER != "development"` when `APP_ENV == "production"`.

### B. Endpoints
- `POST /api/v1/auth/verify-email`: Accepts `{ "token": "<raw_token>" }`. Validates SHA-256 token hash against `security_tokens` and marks user `is_verified=True`.
- `POST /api/v1/auth/resend-verification`: Accepts `{ "email": "..." }`. Dispatches a new verification link without leaking account existence.
- `POST /api/v1/auth/forgot-password`: Accepts `{ "email": "..." }`. Dispatches a password reset link; returns a generic response regardless of whether the email exists.
- `POST /api/v1/auth/reset-password`: Accepts `{ "token": "...", "new_password": "..." }`. Enforces password rules, hashes via Argon2id, marks token used, and revokes all active refresh-token sessions.

### C. Database Table: `security_tokens`
- `id` (`UUID`, PK)
- `user_id` (`UUID`, FK to `users.id` with `ON DELETE CASCADE`)
- `token_type` (`Enum`: `email_verification`, `password_reset`)
- `token_hash` (`VARCHAR(64)`, unique index, storing SHA-256 hash)
- `expires_at` (`TIMESTAMP WITH TIME ZONE`)
- `created_at` (`TIMESTAMP WITH TIME ZONE`, default `now()`)
- `used_at` (`TIMESTAMP WITH TIME ZONE`, nullable)
- `revoked_at` (`TIMESTAMP WITH TIME ZONE`, nullable)

---

## 6. Authentication Email Rate Limiting (Implementation 1B.4.1)

To protect outbound transactional email systems against abuse and deny denial-of-service/enumeration attempts, DayFlow implements database-backed shared rate limiting on:
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/resend-verification`

### A. Design & Mechanics
1. **Shared PostgreSQL State**: Rather than an ephemeral in-memory dictionary, rate limits are tracked in `rate_limit_records` in PostgreSQL. This coordinates limits across multiple workers/nodes.
2. **Concurrency Safety**: Queries use PostgreSQL row-level locks (`SELECT ... FOR UPDATE`) and `ON CONFLICT DO NOTHING` on `(action, scope, identifier_hash)` to prevent race conditions from bypassing thresholds.
3. **Identifier Protection (Zero PII Storage)**: Client IPs and normalized email addresses are salted and hashed with SHA-256 (`hashlib.sha256(f"{salt}:{identifier}".encode("utf-8")).hexdigest()`) before storage.
4. **Client IP Rate Limit**: Allows a maximum of **3 requests per 15 minutes** per IP. Exceeding this limit immediately raises `429 Too Many Requests` with a standard `Retry-After` header.
5. **Per-Email Cooldown**: Enforces a **2-minute cooldown window** per normalized email. If multiple requests target the same account within 2 minutes, subsequent email deliveries are silently suppressed while preserving the exact generic success message, denying account existence discovery to attackers.
6. **Automatic Record Cleanup**: Expired records (`expires_at < current_time`) are pruned automatically during rate limit checks and can be scheduled periodically.

### B. Database Table: `rate_limit_records`
- `id` (`UUID`, PK)
- `action` (`VARCHAR(50)`, e.g., `forgot_password`, `resend_verification`)
- `scope` (`Enum`: `client_ip`, `email`)
- `identifier_hash` (`VARCHAR(64)`, salted SHA-256 hash)
- `request_count` (`INTEGER`, counter within the window)
- `window_start` (`TIMESTAMP WITH TIME ZONE`)
- `expires_at` (`TIMESTAMP WITH TIME ZONE`, indexed)
- Unique constraint / index: `uq_rate_limit_action_scope_hash (action, scope, identifier_hash)`

### C. Configuration Settings
| Setting | Default | Description |
|---|---|---|
| `AUTH_EMAIL_RATE_LIMIT_IP_MAX_REQUESTS` | `3` | Max email requests per IP window |
| `AUTH_EMAIL_RATE_LIMIT_IP_WINDOW_MINUTES` | `15` | IP rate limit window in minutes |
| `AUTH_EMAIL_COOLDOWN_PER_EMAIL_MINUTES` | `2` | Cooldown period per recipient email address |
| `RATE_LIMIT_SALT` | `dayflow-rate-limit-salt-change-me` | Secret cryptographic salt for IP and email hashes (min 16 chars in production) |
| `TRUSTED_PROXIES` | `[]` | List of reverse proxy IPs or CIDRs whose `X-Forwarded-For` headers are trusted |

### D. Security Considerations
1. **Salt Rotation Impact**: The `RATE_LIMIT_SALT` is combined with client identifiers prior to SHA-256 hashing. **Rotating or changing the salt resets the effective rate-limit identity space**, clearing existing throttles as hashes will change.
2. **Reverse Proxy & Client IP Trust**: DayFlow refuses to trust arbitrary `X-Forwarded-For` or `X-Real-IP` headers by default. Only connections arriving directly from an IP listed in `TRUSTED_PROXIES` will have their forwarded client headers evaluated; untrusted requests use the direct peer IP (`request.client.host`), preventing header spoofing attacks from bypassing limits.
3. **Zero Secret Leakage**: `RATE_LIMIT_SALT` is strictly kept in backend environment variables and is never exposed through API responses or logged in application traces. In production, startup fails if `RATE_LIMIT_SALT` is empty, matches development defaults, or is shorter than 16 characters.
