"""
Authentication API Routes

Handles user registration, login, logout, and profile management.
"""
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import structlog

from src.api.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    Token,
    PasswordChange,
)
from src.services.auth_service import (
    create_user,
    authenticate_user,
    get_user_by_id,
    update_user,
    change_password,
    create_access_token,
    decode_token,
    get_user_response,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

logger = structlog.get_logger()
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    user = get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """Ensure the current user is active"""
    if not current_user.get("is_active", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user account.

    Returns a JWT access token upon successful registration.
    """
    try:
        user = create_user(user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"]
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**get_user_response(user))
    )


@router.post("/login", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Login with email and password.

    Returns a JWT access token upon successful authentication.
    Uses OAuth2 password flow for compatibility with OpenAPI.
    """
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"]
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    logger.info("user_login_success", user_id=user["id"], email=user["email"])

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**get_user_response(user))
    )


@router.post("/login/json", response_model=Token)
async def login_json(credentials: UserLogin):
    """
    Login with JSON body (alternative to form-based login).

    Returns a JWT access token upon successful authentication.
    """
    user = authenticate_user(credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(
        data={
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"]
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**get_user_response(user))
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[dict, Depends(get_current_active_user)]):
    """
    Get the current authenticated user's profile.
    """
    return UserResponse(**get_user_response(current_user))


@router.put("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """
    Update the current user's profile.
    """
    updates = user_update.model_dump(exclude_unset=True)
    updated_user = update_user(current_user["id"], updates)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(**get_user_response(updated_user))


@router.post("/change-password")
async def change_user_password(
    password_data: PasswordChange,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """
    Change the current user's password.
    """
    success = change_password(
        current_user["id"],
        password_data.current_password,
        password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(current_user: Annotated[dict, Depends(get_current_active_user)]):
    """
    Logout the current user.

    Note: Since we use stateless JWT tokens, the actual logout is handled
    client-side by removing the token. This endpoint is provided for
    logging purposes and future token blacklisting.
    """
    logger.info("user_logout", user_id=current_user["id"])
    return {"message": "Successfully logged out"}


@router.get("/verify")
async def verify_token(current_user: Annotated[dict, Depends(get_current_active_user)]):
    """
    Verify if the current token is valid.
    """
    return {
        "valid": True,
        "user_id": current_user["id"],
        "email": current_user["email"],
        "role": current_user["role"]
    }
