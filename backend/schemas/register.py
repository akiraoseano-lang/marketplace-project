from pydantic import BaseModel

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str