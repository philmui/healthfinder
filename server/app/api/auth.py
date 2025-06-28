"""
HealthFinder Authentication API Module

This module implements authentication endpoints for the HealthFinder platform,
including OAuth integration with Google and user management.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
import httpx
from loguru import logger
import jwt
from jwt.exceptions import PyJWTError
from sqlalchemy.orm import Session
import secrets
import json
from urllib.parse import urlencode

from app.core.config import settings
from app.core.db import get_db

# Router definition
router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Pydantic models for authentication
class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_at: int  # Unix timestamp

class TokenData(BaseModel):
    """Token data model for decoded JWT."""
    sub: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    exp: int

class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    """User creation model."""
    pass

class UserInDB(UserBase):
    """User database model."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    """User response model."""
    id: int

    model_config = ConfigDict(from_attributes=True)

class GoogleAuthRequest(BaseModel):
    """Google OAuth authentication request."""
    code: str
    redirect_uri: str

# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserInDB:
    """
    Get the current user from the JWT token.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        UserInDB: Current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("email")
        
        if email is None:
            raise credentials_exception
        
        token_data = TokenData(
            sub=payload.get("sub"),
            email=email,
            name=payload.get("name"),
            picture=payload.get("picture"),
            exp=payload.get("exp")
        )
    except PyJWTError:
        raise credentials_exception
    
    # Here you would retrieve the user from the database
    # For now, we'll return a mock user
    # In a real implementation, you would query the database:
    # user = db.query(User).filter(User.email == token_data.email).first()
    
    # Mock user for demonstration
    user = UserInDB(
        id=1,
        email=token_data.email,
        name=token_data.name,
        picture=token_data.picture,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    if user is None:
        raise credentials_exception
    
    return user

# Authentication endpoints
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Args:
        form_data: OAuth2 password request form
        db: Database session
        
    Returns:
        Token: Access token information
    """
    # This is a placeholder for password-based authentication
    # In a real implementation, you would verify the user's credentials
    # For now, we'll raise an exception since we're focusing on OAuth
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Password-based authentication is not supported. Please use OAuth."
    )

@router.post("/google/login", response_model=Token)
async def google_login(request: GoogleAuthRequest, response: Response, db: Session = Depends(get_db)):
    """
    Authenticate with Google OAuth.
    
    Args:
        request: Google authentication request with authorization code
        response: FastAPI response object for setting cookies
        db: Database session
        
    Returns:
        Token: Access token information
    """
    try:
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": request.code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": request.redirect_uri,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            
            if token_response.status_code != 200:
                logger.error(f"Google OAuth token error: {token_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate Google credentials"
                )
            
            token_json = token_response.json()
            google_token = token_json.get("access_token")
            
            # Get user info from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
            headers = {"Authorization": f"Bearer {google_token}"}
            
            userinfo_response = await client.get(userinfo_url, headers=headers)
            
            if userinfo_response.status_code != 200:
                logger.error(f"Google userinfo error: {userinfo_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not get user info from Google"
                )
            
            user_data = userinfo_response.json()
            
            # Check if user exists in database, create if not
            # For now, we'll use the Google user data directly
            # In a real implementation, you would:
            # 1. Check if user exists in database
            # 2. If not, create a new user
            # 3. If yes, update user information if needed
            
            # Create access token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={
                    "sub": user_data.get("sub"),
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "picture": user_data.get("picture")
                },
                expires_delta=access_token_expires
            )
            
            expires_at = int((datetime.now(UTC) + access_token_expires).timestamp())
            
            # Set token as HTTP-only cookie
            response.set_cookie(
                key="access_token",
                value=f"Bearer {access_token}",
                httponly=True,
                secure=not settings.DEBUG,  # Secure in production
                samesite="lax",
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_at=expires_at
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

@router.get("/google/url")
async def google_login_url(redirect_uri: str):
    """
    Get Google OAuth authorization URL.
    
    Args:
        redirect_uri: Redirect URI after authentication
        
    Returns:
        Dict: Authorization URL and state
    """
    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Build Google OAuth URL
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state
    }
    
    authorization_url = f"{auth_url}?{urlencode(params)}"
    
    return {
        "authorization_url": authorization_url,
        "state": state
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: User information
    """
    return current_user

@router.post("/logout")
async def logout(response: Response):
    """
    Logout the current user by clearing the authentication cookie.
    
    Args:
        response: FastAPI response object for clearing cookies
        
    Returns:
        Dict: Logout status
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax"
    )
    
    return {"message": "Successfully logged out"}

# Dependency for optional authentication
async def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[UserInDB]:
    """
    Get the current user if authenticated, otherwise return None.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        Optional[UserInDB]: Current user or None
    """
    authorization = request.headers.get("Authorization")
    
    if not authorization:
        # Check for token in cookies
        access_token_cookie = request.cookies.get("access_token")
        if access_token_cookie and access_token_cookie.startswith("Bearer "):
            authorization = access_token_cookie
    
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None
