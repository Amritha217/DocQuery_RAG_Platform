import os

from dotenv import load_dotenv

# load values from a .env file

load_dotenv()

# Tells SQLAlchemy which database to connect to

DATABASE_URL = os.getenv("DATABASE_URL")

# Secret used to sign and verify JWT tokens
SECRET_KEY = os.getenv("SECRET_KEY")

# JWT signing algorithm

ALGORITHM = os.getenv("ALGORITHM")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv("GROQ_MODEL")

GROQ_JUDGE_MODEL = os.getenv("GROQ_JUDGE_MODEL")

HF_TOKEN = os.getenv("HF_TOKEN")

HF_MODEL = os.getenv("HF_MODEL")
