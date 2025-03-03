import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URI = os.getenv("DATABASE_URI")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret_key")
