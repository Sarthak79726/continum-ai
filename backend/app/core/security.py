import re
import uuid
import secrets
import hashlib
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from app.core.config import settings

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

def validate_password_strength(password: str) -> None:
    """
    Enforces strong password policy:
    - Minimum 8 characters, maximum 128 characters (prevents bcrypt DoS)
    - At least one uppercase letter [A-Z]
    - At least one lowercase letter [a-z]
    - At least one digit or symbol
    """
    if not password:
        raise ValueError("Password is required.")
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long.")
    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must not exceed {PASSWORD_MAX_LENGTH} characters.")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter (A-Z).")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter (a-z).")
    if not re.search(r'[\d!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        raise ValueError("Password must contain at least one number or special character.")
    return True

def get_password_hash(password: str) -> str:
    """Hashes password with bcrypt using 12 work rounds."""
    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValueError("Password exceeds maximum allowed length.")
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def generate_secure_random_token(nbytes: int = 32) -> str:
    """Generates cryptographically random URL-safe token."""
    return secrets.token_urlsafe(nbytes)

def hash_token(token: str) -> str:
    """Computes SHA-256 hash of a token for secure database storage."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates signed, short-lived JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "type": "access",
        "iat": now,
        "exp": expire,
        "jti": uuid.uuid4().hex
    })
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates signed, long-lived JWT refresh token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "type": "refresh",
        "iat": now,
        "exp": expire,
        "jti": uuid.uuid4().hex
    })
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str, expected_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Decodes and validates token signature, expiration, algorithm, and type."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]}
        )
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except Exception:
        return None

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes access token, rejecting tokens that are not explicitly typed as access."""
    payload = decode_token(token, expected_type="access")
    # Backwards compatibility: allow legacy tokens without explicit type during migration
    if not payload:
        try:
            legacy_payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            if legacy_payload.get("type") is None:
                return legacy_payload
        except Exception:
            return None
    return payload

def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and verifies a refresh token."""
    return decode_token(token, expected_type="refresh")
