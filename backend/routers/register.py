from fastapi import APIRouter
from schemas.register import RegisterRequest
from database.connection import get_connection
from utils.password import hash_password

router = APIRouter(
    prefix="/api",
    tags=["Register"]
)

@router.post("/register")
def register(data: RegisterRequest):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE email = %s",
        (data.email,)
    )

    existing_user  = cursor.fetchone()

    if existing_user is not None:
        cursor.close()
        connection.close()

        return {
            "message": "Email yang anda masukkan sudah digunakan"
        }

    hashed_password = hash_password(data.password)

    cursor.execute(
        """
    INSERT INTO users (name, email, password)
    VALUES (%s, %s, %s)
    """,
    (
        data.name,
        data.email,
        hashed_password
    )
    )

    connection.commit()

    user_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return {
        "message": "Register berhasil",
        "user": {
            "id": user_id,
            "name": data.name,
            "email": data.email
        }
    }