"""Authentication API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.schemas import TokenRequest, TokenResponse
from app.config import settings

router = APIRouter()
security = HTTPBearer()


def create_access_token(user_id: str) -> tuple[str, datetime]:
    """Create JWT access token"""
    expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expires_at,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_at


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.post("/token", response_model=TokenResponse)
async def get_token(request: TokenRequest):
    """Generate JWT token for user"""
    token, expires_at = create_access_token(request.user_id)
    return TokenResponse(
        access_token=token,
        expires_at=expires_at
    )


# Dependency for protected routes
async def get_current_user(user_id: str = Depends(verify_token)) -> str:
    """Get current authenticated user"""
    return user_id
