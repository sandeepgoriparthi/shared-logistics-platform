"""
Authentication Service

Handles password hashing, JWT token creation/verification, and user authentication.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

from src.api.schemas.auth import UserCreate, UserRole, TokenData

logger = structlog.get_logger()

# Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, use env variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory user store (replace with database in production)
users_db: Dict[str, Dict[str, Any]] = {}
users_by_email: Dict[str, str] = {}  # email -> user_id mapping


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if user_id is None:
            return None

        return TokenData(user_id=user_id, email=email, role=role)
    except JWTError as e:
        logger.warning("jwt_decode_error", error=str(e))
        return None


def create_user(user_data: UserCreate) -> Dict[str, Any]:
    """Create a new user"""
    # Check if email already exists
    if user_data.email.lower() in users_by_email:
        raise ValueError("Email already registered")

    user_id = str(uuid4())
    now = datetime.utcnow()

    user = {
        "id": user_id,
        "email": user_data.email.lower(),
        "full_name": user_data.full_name,
        "company_name": user_data.company_name,
        "phone": user_data.phone,
        "role": user_data.role.value,
        "hashed_password": get_password_hash(user_data.password),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    users_db[user_id] = user
    users_by_email[user_data.email.lower()] = user_id

    logger.info("user_created", user_id=user_id, email=user_data.email)
    return user


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user by email and password"""
    email_lower = email.lower()

    if email_lower not in users_by_email:
        return None

    user_id = users_by_email[email_lower]
    user = users_db.get(user_id)

    if not user:
        return None

    if not user.get("is_active", False):
        return None

    if not verify_password(password, user["hashed_password"]):
        return None

    logger.info("user_authenticated", user_id=user_id, email=email)
    return user


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get a user by their ID"""
    return users_db.get(user_id)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by their email"""
    email_lower = email.lower()
    if email_lower not in users_by_email:
        return None
    return users_db.get(users_by_email[email_lower])


def update_user(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a user's information"""
    if user_id not in users_db:
        return None

    user = users_db[user_id]

    for key, value in updates.items():
        if key not in ["id", "email", "hashed_password", "created_at"] and value is not None:
            user[key] = value

    user["updated_at"] = datetime.utcnow()
    users_db[user_id] = user

    logger.info("user_updated", user_id=user_id)
    return user


def change_password(user_id: str, current_password: str, new_password: str) -> bool:
    """Change a user's password"""
    user = users_db.get(user_id)
    if not user:
        return False

    if not verify_password(current_password, user["hashed_password"]):
        return False

    user["hashed_password"] = get_password_hash(new_password)
    user["updated_at"] = datetime.utcnow()
    users_db[user_id] = user

    logger.info("password_changed", user_id=user_id)
    return True


def deactivate_user(user_id: str) -> bool:
    """Deactivate a user account"""
    if user_id not in users_db:
        return False

    users_db[user_id]["is_active"] = False
    users_db[user_id]["updated_at"] = datetime.utcnow()

    logger.info("user_deactivated", user_id=user_id)
    return True


def get_user_response(user: Dict[str, Any]) -> Dict[str, Any]:
    """Get a user response without sensitive data"""
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "company_name": user.get("company_name"),
        "phone": user.get("phone"),
        "role": user["role"],
        "is_active": user["is_active"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }
