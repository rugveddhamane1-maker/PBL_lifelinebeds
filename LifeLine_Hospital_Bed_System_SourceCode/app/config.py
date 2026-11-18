import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "LifeLine - Real-Time Hospital Bed Availability System"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./lifeline_beds.db")
    STAFF_DEFAULT_PIN: str = os.getenv("STAFF_DEFAULT_PIN", "1234")
    CITY_DEFAULT: str = os.getenv("CITY_DEFAULT", "Metro City")

settings = Settings()
