from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional, Union
from datetime import datetime, timedelta

from app import models, schemas, security
from app.db import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/token")

def getUser(db: Session, email: str) -> Optional[schemas.UserDB]:
    return db.query(models.User).filter(models.User.email == email).first()

def getAdmin(db: Session, email: str) -> Optional[schemas.AdminDB]:
    return db.query(models.Admin).filter(models.Admin.email == email).first()

def getSupervisor(db: Session, email: str) -> Optional[schemas.SupervisorDB]:
    return db.query(models.Supervisors).filter(models.Supervisors.username == email).first()

async def getCurrentUser(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> schemas.UserDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = getUser(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def getCurrentAdmin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> schemas.AdminDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        print(payload, "\n")
        email: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin", False)
        if email is None or not is_admin:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    admin = getAdmin(db, email=token_data.email)
    if admin is None:
        raise credentials_exception
    return admin

async def getCurrentSupervisor(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> schemas.SupervisorDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        is_supervisor: bool = payload.get("is_supervisor", False)
        if email is None or not is_supervisor:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    supervisor = getSupervisor(db, email=token_data.email)
    if supervisor is None:
        raise credentials_exception
    return supervisor

async def get_current_any_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Union[schemas.UserDB, schemas.AdminDB, schemas.SupervisorDB]:
    """
    Authenticate any user type (user, admin, or supervisor) using a JWT token.
    
    Args:
        token: JWT token from the Authorization header.
        db: Database session.
    
    Returns:
        Union[UserDB, AdminDB, SupervisorDB]: The authenticated user, admin, or supervisor.
    
    Raises:
        HTTPException: If credentials are invalid or user type is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # Check user types in order: user, admin, supervisor
    user = getUser(db, email=token_data.email)
    if user:
        return user
    
    admin = getAdmin(db, email=token_data.email)
    if admin:
        return admin
    
    supervisor = getSupervisor(db, email=token_data.email)
    if supervisor:
        return supervisor
    
    raise credentials_exception