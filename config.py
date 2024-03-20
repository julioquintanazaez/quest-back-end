from dotenv import load_dotenv
from os import getenv

#Load envirnment variables
load_dotenv()

ALGORITHM = getenv("ALGORITHM")
SECRET_KEY = getenv("SECRET_KEY")
APP_NAME = getenv("APP_NAME")
ACCESS_TOKEN_EXPIRE_MINUTES = getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
ADMIN_USER = getenv("ADMIN_USER")
ADMIN_NAME = getenv("ADMIN_NAME")
ADMIN_EMAIL = getenv("ADMIN_EMAIL")
ADMIN_PASS = getenv("ADMIN_PASS")