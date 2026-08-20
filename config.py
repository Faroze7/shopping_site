import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv(
        "FLASK_SECRET_KEY",
        "development-secret-key"
    )

    STRIPE_SECRET_KEY = os.getenv(
        "STRIPE_SECRET_KEY"
    )

    STRIPE_WEBHOOK_SECRET = os.getenv(
        "STRIPE_WEBHOOK_SECRET"
    )