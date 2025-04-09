import os
from dotenv import load_dotenv
load_dotenv()

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user:5000/user")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret_key")

POST_SERVICE_HOST = "post"  
POST_SERVICE_PORT = "6000"
