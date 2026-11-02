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

