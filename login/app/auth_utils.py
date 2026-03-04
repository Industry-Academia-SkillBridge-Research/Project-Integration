"""
JWT token utilities for user authentication
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

# Security scheme for JWT Bearer token
security = HTTPBearer()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing the payload data (usually user_id, email, etc.)
        expires_delta: Optional custom expiration time. If not provided,
                      uses ACCESS_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
        Encoded JWT token as a string

    Example:
        token = create_access_token(
            data={"user_id": 123, "email": "user@example.com"}
        )
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add expiration to token payload
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    # Encode and return JWT token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token string to verify

    Returns:
        Dictionary containing the decoded token payload if valid, None otherwise

    Example:
        payload = verify_token(token)
        if payload:
            user_id = payload.get("user_id")
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode JWT token without verification (for debugging only).

    Args:
        token: The JWT token string to decode

    Returns:
        Dictionary containing the decoded token payload

    Raises:
        JWTError: If token cannot be decoded
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"verify_signature": False}
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    This function is used with FastAPI's Depends() to protect routes.
    It extracts the JWT token from the Authorization header, verifies it,
    and returns the authenticated user object.
    
    Args:
        credentials: HTTP Bearer token credentials from request header
        db: Database session
        
    Returns:
        User object of the authenticated user
        
    Raises:
        HTTPException 401: If token is invalid or user not found
        
    Example:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify and decode token
        payload = verify_token(token)
        
        if payload is None:
            raise credentials_exception
        
        # Extract user_id from token payload
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user
