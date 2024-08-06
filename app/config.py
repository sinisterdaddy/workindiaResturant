import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('SECRET_KEY')
    # Print the environment variables to verify
    print(f"SECRET_KEY: {SECRET_KEY}")
    print(f"DATABASE_URL: {SQLALCHEMY_DATABASE_URI}")
    print(f"JWT_SECRET_KEY: {JWT_SECRET_KEY}")