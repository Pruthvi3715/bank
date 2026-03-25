from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

import os

SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "graphsentinel-dev-secret-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    user_id: str
    role: str
    disabled: bool = False


MOCK_USERS_DB: dict[str, dict] = {
    "investigator": {
        "user_id": "investigator",
        "role": "investigator",
        "hashed_password": pwd_context.hash("investigate123"),
        "disabled": False,
    },
    "senior_analyst": {
        "user_id": "senior_analyst",
        "role": "senior_analyst",
        "hashed_password": pwd_context.hash("analyst456"),
        "disabled": False,
    },
    "readonly": {
        "user_id": "readonly",
        "role": "readonly",
        "hashed_password": pwd_context.hash("readonly789"),
        "disabled": False,
    },
}


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(user_id: str) -> Optional[dict]:
    return MOCK_USERS_DB.get(user_id)


def authenticate_user(user_id: str, password: str) -> Optional[dict]:
    user = get_user(user_id)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role", "readonly")
        if user_id is None:
            raise credentials_exception
        return User(user_id=user_id, role=role)
    except JWTError:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(allowed_roles: list[str]):
    """Dependency factory — returns a dependency that enforces role."""

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not authorized for this action",
            )
        return current_user

    return role_checker
