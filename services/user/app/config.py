import os
from dotenv import load_dotenv
load_dotenv()

USER_DATABASE_URI = os.getenv("USER_DATABASE_URI", "postgresql://postgres:password@db:5432/social_db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret_key")
