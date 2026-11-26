import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    gmail_address: str
    gmail_app_password: str
    alert_to_email: str
    nvidia_careers_url: str

def get_settings() -> Settings:
    values = {
        "GMAIL_ADDRESS": os.getenv("GMAIL_ADDRESS", "").strip(),
        "GMAIL_APP_PASSWORD": os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", ""),
        "ALERT_TO_EMAIL": os.getenv("ALERT_TO_EMAIL", "").strip(),
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing environment variables: " + ", ".join(missing) +
            ". Copy .env.example to .env and fill in the values."
        )
    return Settings(
        gmail_address=values["GMAIL_ADDRESS"],
        gmail_app_password=values["GMAIL_APP_PASSWORD"],
        alert_to_email=values["ALERT_TO_EMAIL"],
        nvidia_careers_url=os.getenv(
            "NVIDIA_CAREERS_URL", "https://jobs.nvidia.com/careers"
        ).strip(),
    )
