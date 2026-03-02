# config.py
import os
from dotenv import load_dotenv

load_dotenv()

def is_dev_mode() -> bool:
    return os.getenv("DEV_MODE", "0") == "1"