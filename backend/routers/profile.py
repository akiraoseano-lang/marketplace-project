from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from database.connection import get_connection
from utils.auth import get_current_user
from pydantic import BaseModel
from utils.password import hash_password, verify_password

router = APIRouter(
    prefix="/api/profile",
    tags=["Profile"]
)

class ProfileUpdate(BaseModel):
    name: str
    email: EmailStr

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

@router.get("/")
def get_profile(
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, name, email, role
            FROM users
            WHERE id = %s
            """,
            (current_user["user_id"],)
        )

        user = cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Sorry, user not found"
            )

        return {
            "message": "Profile succes to found",
            "user": user
        }

    finally:
        cursor.close()
        connection.close()

@router.put("/")
def update_profile(
    data: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id FROM users
            WHERE email = %s AND id != %s
            """,
            (data.email, current_user["user_id"])
        )

        existing_user = cursor.fetchone()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already use"
            )

        cursor.execute(
            """
            UPDATE users
            SET name = %s, email = %s
            WHERE id = %s
            """,
            (
                data.name,
                data.email,
                current_user["user_id"]
            )
        )

        connection.commit()

        return {
            "message": "profil is already update",
            "user": {
                "id": current_user["user_id"],
                "name": data.name,
                "email": data.email
            }
        }
    
    finally:
            cursor.close()
            connection.close()

    

@router.put("/password")
def change_password(
    data: ChangePassword,
    current_user: dict = Depends(get_current_user)
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT password
            FROM users
            WHERE id = %s
            """,
            (current_user["user_id"])
        )

        user = cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="sorry, user not found"
            )

        if not verify_password(
            data.old_password,
            user["password"]
        ):
            raise HTTPException(
                status_code=400,
                detail="Old password is incorect"
            )

        if len(data.new_password) < 6:
            raise HTTPException(
                status_code=400,
                detail="New password must be at least 6 character"
            )

        if data.old_password == data.new_password:
            raise HTTPException(
                status_code=400,
                detail="The new password must be different"
            )

        new_hashed_password = hash_password(
            data.new_password
        )

        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE id = %s
            """,
            (
                new_hashed_password,
                current_user["user_id"]
            )
        )

        connection.commit()

        return {
            "message" : "Password already update"
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()