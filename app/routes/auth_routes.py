# Purpose: Handles user registration and authentication using JWT tokens.


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

ALLOWED_DOMAIN = "test.com"


# Register a new user

# - Checks that the email ends with @test.com
# - Checks whether the email is already registered
# - Hashes the password so the original password is not stored in the database
#  - Creates and saves the new user
# - Returns the user's information

@router.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if ALLOWED_DOMAIN and not user.email.endswith(f"@{ALLOWED_DOMAIN}"):
        raise HTTPException(status_code=400, detail="Email domain not allowed")

    existing_user = db.query(models.User).filter_by(email=user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        email=user.email,
        hashed_password=auth.hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


#  Log in and create a JWT token

# - Searches the database for the supplied email
# - Verifies the supplied password against the stored password hash
# - Returns an HTTP 401 Unauthorized error if the credentials are invalid
# - Creates an access token containing the user's email
# - Returns the token and its type, bearer

@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter_by(email=user.email).first()

    if not db_user or not auth.verify_password(
        user.password, db_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = auth.create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}


#  Get the logged-in user's information - returns the details of the currently authenticated user


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
