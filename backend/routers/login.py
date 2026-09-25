from fastapi import APIRouter, Depends
from schemas.login import LoginRequest
from database.connection import get_connection
from utils.password import verify_password
from utils.jwt import create_access_token
from utils.auth import get_current_user

router  = APIRouter(
    prefix="/api",
    tags=["Login"]
)

@router.post("/login")
def login(data: LoginRequest):

    connection = get_connection()
    cursor =  connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE email = %s",
        (data.email,)
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user is None:
        return {
            "message": "Maaf, email atau password anda salah"
        }

    if not verify_password(data.password, user["password"]):
        return {
            "message": "Emmail atau password yang anda masukkan salah"
        }

    access_token = create_access_token({
        "user_id": user["id"],
        "email": user["email"],
        "role": user["role"]
    })

    return {
        "message": "Login berhasil",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@router.get("/profile")
def profile(current_user: dict = Depends(get_current_user)):
    return {
        "message": "Token valid",
        "user": current_user
    }