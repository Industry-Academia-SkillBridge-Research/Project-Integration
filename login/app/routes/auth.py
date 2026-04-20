"""
Authentication routes for OAuth 2.0 login flow
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from app.database import get_db
from app.models import User
from app.oauth_service import oauth
from app.auth_utils import create_access_token, verify_token
from app.config import settings

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login/google")
async def login_google(request: Request):
    """
    Initiate Google OAuth login flow.

    This endpoint redirects the user to Google's OAuth consent screen.
    After the user grants permission, Google will redirect back to the callback URL.

    Frontend usage:
        window.location.href = 'http://localhost:8182/auth/login/google'
    """
    try:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials not configured in .env file")
        
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        print(f"[OAuth] Starting Google login flow with redirect_uri: {redirect_uri}")
        print(f"[OAuth] Client ID configured: {bool(settings.GOOGLE_CLIENT_ID)}")
        print(f"[OAuth] Client Secret configured: {bool(settings.GOOGLE_CLIENT_SECRET)}")
        
        return await oauth.google.authorize_redirect(request, redirect_uri)
    
    except TimeoutError as te:
        print(f"[OAuth] TIMEOUT connecting to Google: {str(te)}")
        print(f"[OAuth] Possible causes: No internet connection or Google servers unreachable")
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Google OAuth servers. Please check your internet connection and try again."
        )
    except Exception as e:
        print(f"[OAuth] ERROR in login_google: {str(e)}")
        print(f"[OAuth] Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"OAuth initialization failed: {str(e)}"
        )


@router.get("/google/callback", name="auth_callback_google")
async def auth_callback_google(request: Request, db: Session = Depends(get_db)):
    """
    Google OAuth callback endpoint.

    This endpoint receives the authorization code from Google,
    exchanges it for user information, and either:
    1. Creates a new user account (first-time login)
    2. Updates existing user information (returning user)

    Returns:
        Redirects to frontend with JWT token in query parameter
    """
    try:
        print(f"[OAuth] Callback received, processing authorization...")
        
        # Exchange authorization code for access token and get user info
        token = await oauth.google.authorize_access_token(request)
        print(f"[OAuth] Token obtained successfully")

        # Get user information from Google
        user_info = token.get('userinfo')
        if not user_info:
            print(f"[OAuth] userinfo not in token, fetching from Google API...")
            # Fallback: manually fetch user info if not in token
            resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
            user_info = resp.json()
            print(f"[OAuth] User info fetched: {user_info}")

        # Extract user data
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')
        provider_user_id = user_info.get('sub')  # Google's unique user ID

        print(f"[OAuth] User data - email: {email}, name: {name}")

        if not email or not provider_user_id:
            print(f"[OAuth] ERROR: Missing required user info (email={email}, sub={provider_user_id})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not retrieve user information from Google"
            )

        # Check if user already exists
        try:
            existing_user = db.query(User).filter(User.email == email).first()
        except Exception as db_err:
            print(f"[OAuth] Database error querying user: {db_err}")
            raise

        if existing_user:
            print(f"[OAuth] Updating existing user: {email}")
            # Update existing user information
            existing_user.name = name
            existing_user.picture = picture
            existing_user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(existing_user)
            user = existing_user
        else:
            print(f"[OAuth] Creating new user: {email}")
            # Create new user (automatic registration on first login)
            new_user = User(
                email=email,
                name=name,
                picture=picture,
                provider="google",
                provider_user_id=provider_user_id,
                is_active=True,
                last_login=datetime.utcnow()
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user
            print(f"[OAuth] New user created successfully")

        # Create JWT token with user information
        access_token = create_access_token(
            data={
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
            }
        )

        print(f"[OAuth] JWT token created for user {user.email}")

        # Redirect to frontend with token
        # Frontend should extract the token from URL and store it (localStorage/cookie)
        frontend_redirect = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
        print(f"[OAuth] Redirecting to: {frontend_redirect}")
        return RedirectResponse(url=frontend_redirect)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log complete error with traceback
        print(f"[OAuth] EXCEPTION in callback: {str(e)}")
        import traceback
        traceback.print_exc()

        # Redirect to frontend with error
        error_redirect = f"{settings.FRONTEND_URL}/auth/callback?error=authentication_failed&error_desc={str(e)}"
        print(f"[OAuth] Redirecting to error: {error_redirect}")
        return RedirectResponse(url=error_redirect)


@router.get("/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.

    Headers:
        Authorization: Bearer <your_jwt_token>

    Returns:
        User information as JSON

    Frontend usage:
        fetch('http://localhost:8000/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ")[1]

    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user.to_dict()


@router.post("/logout")
async def logout(request: Request) -> Dict[str, str]:
    """
    Logout endpoint.

    Since JWT tokens are stateless, logout is handled on the frontend
    by removing the token from storage. This endpoint exists for
    consistency and can be extended for token blacklisting if needed.

    Frontend usage:
        // Remove token from storage
        localStorage.removeItem('access_token');

        // Optional: call logout endpoint
        fetch('http://localhost:8000/auth/logout', { method: 'POST' })
    """
    return {"message": "Logged out successfully"}


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify the auth service is running.
    """
    return {
        "status": "healthy",
        "service": "oauth-authentication",
        "providers": ["google"]
    }
