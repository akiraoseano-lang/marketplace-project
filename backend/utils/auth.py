from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from utils.jwt import SECRET_KEY, ALGORITHM

security  = HTTPBearer()

def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Maaf, token yang anda masukkan tidak valid atau sudah expired"
        )

def get_current_admin(
        current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Maaf, Akses ini hanya untuk admin"
        )

    return current_user