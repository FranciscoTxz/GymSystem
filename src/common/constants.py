import os

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
MONGODB_URI = os.getenv("MONGODB_URI")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
