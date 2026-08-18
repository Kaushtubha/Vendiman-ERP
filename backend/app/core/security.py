"""
app/core/security.py — JWT Authentication & Password Hashing

PATTERN: Stateless JWT with short-lived access tokens + long-lived refresh tokens.

ARCHITECTURAL DECISIONS:

1. WHY JWT (not sessions):
   - Stateless: no session store required. Each API server validates tokens
     independently without Redis/DB lookup.
   - Horizontally scalable: all API pods share the same SECRET_KEY. Any
     pod can validate any token without coordination.
   - WHY NOT opaque tokens: Opaque tokens require a DB/Redis lookup on every
     request to validate — adds latency and a single point of failure.

2. WHY short access + long refresh token pattern:
   - Access token (60min): If stolen, the attacker's window is limited.
   - Refresh token (7 days): Stored in HttpOnly cookie or secure storage.
     When the access token expires, the client silently exchanges the refresh
     token for a new access token.
   - Revocation: Invalidate refresh tokens by storing them in Redis with a
     denylist. Access tokens cannot be individually revoked (stateless trade-off).

3. WHY HS256 (not RS256):
   - HS256 (HMAC-SHA256): Symmetric key — same key to sign and verify.
     Simpler for a single-service system.
   - RS256 (RSA) would be needed if external services (micro-services, mobile
     apps) need to verify tokens WITHOUT sharing the secret key. When that
     requirement arrives, change ALGORITHM=RS256 and provide key pair.

4. WHY bcrypt (not argon2, sha256):
   - bcrypt is intentionally slow (adjustable work factor). Brute-forcing
     bcrypt hashes is computationally infeasible.
   - argon2 is technically superior but passlib's argon2 binding has
     dependency issues on Alpine Linux (Docker).
   - sha256/MD5: NEVER use for passwords. They are cryptographic hashes,
     not password hashing functions — GPU-crackable in seconds.

SECURITY HARDENING:
   - Token contains user UUID (sub), email, role, and jti (JWT ID).
   - jti (JWT ID) is a unique token identifier. Used for revocation.
   - exp claim validates token expiry. python-jose raises ExpiredSignatureError.
   - nbf (not-before) prevents tokens from being used before issuance.
   - Passwords never logged, never returned in API responses.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ── Password Hashing Context ─────────────────────────────────────────────────
# WHY CryptContext over direct bcrypt calls:
#   CryptContext handles algorithm upgrades gracefully — if we switch from
#   bcrypt to argon2 in the future, existing hashes still verify via the
#   "deprecated" list, and new hashes use the new algorithm automatically.
#   Users don't need to reset passwords.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Work factor. Every +1 doubles hashing time. 12 ≈ 300ms.
)


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    The returned hash includes the algorithm, work factor, and salt —
    all stored together in the hash string. No separate salt storage needed.

    Args:
        plain_password: The raw password from registration/password reset.

    Returns:
        bcrypt hash string (60 characters, e.g., $2b$12$...)
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    WHY not just hash and compare: bcrypt salts are random per hash.
    The same password hashed twice produces different hashes. The verify()
    function extracts the salt from the stored hash and re-computes.

    Returns False on any error — never raises for security (timing attacks).
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(
    subject: str,            # User UUID — never use email (PII in logs)
    email: str,
    role: str,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived JWT access token.

    CLAIMS:
        sub: Subject (user UUID) — standard JWT claim
        email: User email — used by frontend to display user info
        role: User role — used by frontend for UI permission gating
              (never use JWT role claims alone for server-side authorization!)
        jti: JWT ID — unique token identifier for revocation
        type: "access" — prevents refresh tokens from being used as access tokens
        iat: Issued at — standard JWT claim
        exp: Expiry — standard JWT claim

    Args:
        subject: User UUID as string
        email: User email
        role: User's role enum value
        additional_claims: Any extra claims (e.g., permissions)

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "role": role,
        "type": "access",
        "jti": str(uuid4()),
        "iat": now,
        "exp": expire,
        "nbf": now,         # Not valid before "now"
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    """
    Create a long-lived JWT refresh token.

    WHY separate function: Refresh tokens have different claims (no email/role).
    They carry minimal payload to reduce the blast radius if intercepted.

    Args:
        subject: User UUID as string

    Returns:
        Tuple of (encoded_token, expiry_datetime)
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": now,
        "exp": expire,
        "nbf": now,
    }

    token = jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )
    return token, expire


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Validation performed by python-jose:
        - Signature verification (HMAC-SHA256)
        - Expiry (exp claim)
        - Not-before (nbf claim)
        - Algorithm verification (prevents algorithm confusion attacks)

    Raises:
        JWTError: If token is invalid, expired, or tampered.

    Returns:
        Decoded payload dictionary.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],  # Explicit algorithm prevents confusion attacks
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT decode failed: %s", exc)
        raise


def extract_token_claims(token: str) -> dict[str, Any] | None:
    """
    Safely decode a token for informational purposes (e.g., audit logging).

    WHY: decode_token() raises on invalid tokens, which is correct for auth flows.
    But for logging/auditing, we want to extract what we can without raising.

    Returns None if the token is completely invalid (not parseable).
    """
    settings = get_settings()
    try:
        # options={"verify_exp": False} allows reading expired tokens for auditing
        return jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"verify_exp": False},
        )
    except JWTError:
        return None
