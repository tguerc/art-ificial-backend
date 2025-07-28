from passlib.context import CryptContext # type: ignore

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hashear_password(password: str) -> str:
    return pwd_context.hash(password)