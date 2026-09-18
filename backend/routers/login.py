from fastapi import APIRouter
from schemas.login import LoginRequest
from database.connection import get_connection

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

    if user["password"] != data.password:
        return {
            "message": "Maaf, email atau password anda salah"
        }

    return {
        "message": "Login berhasil",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    }