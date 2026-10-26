# Handles dataabase connection and session management

# connects  FastAPI application to a database and makes database sessions available to  API endpoints.

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

# Create the database engine
# Set up the connection interface between  application and  database

engine = create_engine(DATABASE_URL)

# Create a reusable factory that produces database sessions

# Sessions lets to perform db operations - adding new user , finding doc , saving chat message , updating/deleting db record

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the model base class

# Provide a common base class for your database models - used by the models defined in models.py

Base = declarative_base()

# Give an API request a database session and make sure that session is closed afterward

def get_db():

    # creates a new database session
    db = SessionLocal()

    try:

        # provides that session to the API endpoint
        yield db

    finally:

        # closes the session
        db.close()