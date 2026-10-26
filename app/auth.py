# Handles password hashing , verifies password , create login tokens , check which user is making request


from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import models
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from app.database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Read the Bearer token from the request
security_scheme = HTTPBearer()

# 1. Hash a password before storing it in the database.

# - Accepts the user's plain-text password
# - Uses bcrypt through pwd_context to create a password hash
# - Returns the hash for storage in the database ( we store hashed password not original text password)

def hash_password(password: str) -> str:
    """Convert a plain password into a hashed password."""
    return pwd_context.hash(password)



# 2. Check whether a password entered during login matches the stored password hash

# - Accepts the entered password and stored hash
# - Uses the password-hashing library to compare them
# - Returns True if they match, otherwise False

def verify_password(password: str, hashed_password: str) -> bool:
    """Check whether a password matches its stored hash."""
    return pwd_context.verify(password, hashed_password)


# 3. Create a JWT (JSON Web Token) after successful login

# - Copies the supplied user data, usually including the user's email in the sub field
# - Adds an expiration time
# - Signs the token using SECRET_KEY and ALGORITHM
# - Returns the token as a string

def create_access_token(data: dict) -> str:
    """Create a JWT token for a logged-in user."""
    token_data = data.copy()

    expiration = datetime.now(UTC) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    token_data["exp"] = expiration

    token = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return token



# 4. Validate and read a JWT token

# - Receives a token from a request
# - Verifies its signature and expiration using the configured secret and algorithm
# - Returns the token's payload if valid
# - Returns None if JWT decoding or validation fails


def decode_access_token(token: str):
    """Decode a token and return its data, or None if invalid."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload

    except JWTError:
        return None



# 5. Identify the logged-in user for a protected API request

# - Gets the Bearer token from the HTTP request's Authorization header
# - Calls decode_access_token() to validate the token
# - Reads the user's email from the sub field
# - Searches the database for that user
# - Returns the user object if found; otherwise, raises an HTTP 401 error
    

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
):
    """Verify the token and return the logged-in user."""

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: user information is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(
        models.User.email == email
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
