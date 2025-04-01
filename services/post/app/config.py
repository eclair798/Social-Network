import os
from dotenv import load_dotenv
load_dotenv()

POST_DATABASE_URI = os.getenv("POST_DATABASE_URI", "postgresql://postgres:password@db:5432/post_db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret_key")
