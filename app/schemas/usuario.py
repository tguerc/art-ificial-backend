from pydantic import BaseModel, EmailStr # type: ignore

class UsuarioCreate(BaseModel):
    email: EmailStr
    userName: str
    password: str