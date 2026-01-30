from passlib.context import CryptContext

# Use PBKDF2 to avoid bcrypt backend issues + 72 byte limit
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    # You can still enforce length rules in the router (min 8, max e.g. 256)
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)