"""auth.py — JWT authentication para o Bolao Survivor"""

import os, hashlib
from datetime import datetime, timedelta
from typing import Optional

SENHA_ADMIN = os.environ.get("SENHA_ADMIN", "admin123")

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY  = os.environ.get("SECRET_KEY", "bolao-survivor-secret-change-in-prod")
ALGORITHM   = "HS256"
TOKEN_EXPIRE_HOURS = 24

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def verificar_senha(senha: str, hashed: str) -> bool:
    return hash_senha(senha) == hashed


def criar_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_usuario_atual(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decodificar_token(token)
    uid  = payload.get("sub")
    role = payload.get("role", "user")
    if not uid:
        raise HTTPException(status_code=401, detail="Token invalido")
    return {"uid": uid, "role": role}


def get_admin_atual(usuario=Depends(get_usuario_atual)) -> dict:
    if usuario.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao admin")
    return usuario
