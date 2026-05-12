import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY                     = os.getenv("SECRET_KEY", "vividai123secretkey456")
    SQLALCHEMY_DATABASE_URI        = "sqlite:///vividai.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    IMAGE_FOLDER                   = os.path.join("static", "images")
    MAX_PROMPT_LEN                 = 1000