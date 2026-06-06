from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import jwt, JWTError
import bcrypt
from core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(
    organization_id: UUID,
    recruiter_id: UUID,
    recruiter_email: str,
    expires_delta: timedelta = timedelta(hours=8)
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(recruiter_id),
        "organization_id": str(organization_id),
        "email": recruiter_email,
        "exp": expire
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm="HS256"
    )

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        return payload
    except JWTError:
        return None
