# jwtUtils.py
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

SECRET_KEY = None  # Will be set dynamically
ALGORITHM = "HS256"

def set_secret_key(secret_key):
    global SECRET_KEY
    SECRET_KEY = secret_key

def create_access_token(data: dict, expires_delta: timedelta = None):
    if SECRET_KEY is None:
        raise ValueError("SECRET_KEY not set")
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    if SECRET_KEY is None:
        raise ValueError("SECRET_KEY not set")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return {"username": username, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

def role_required(required_role: str):
    def role_dependency(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted",
            )
        return current_user
    return role_dependency

def get_current_username_optional(token: str = Depends(oauth2_scheme)):
    if SECRET_KEY is None:
        raise ValueError("SECRET_KEY not set")
    if not token:
        return "anonymous"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return "anonymous"
        return username
    except jwt.PyJWTError:
        return "anonymous"
