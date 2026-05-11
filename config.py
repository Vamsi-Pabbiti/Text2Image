import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY          = os.getenv("SECRET_KEY", "fallback-secret-key")
    SQLALCHEMY_DATABASE_URI        = "sqlite:///vividai.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY                 = os.getenv("GEMINI_API_KEY")
    IMAGE_FOLDER  = os.path.join("static", "images")
    MAX_PROMPT_LEN = 1000