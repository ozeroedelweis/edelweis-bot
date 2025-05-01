import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))

BOOKING_URL = os.getenv("BOOKING_URL")
RULES_URL = os.getenv("RULES_URL")
LOCATION_URL = os.getenv("LOCATION_URL")
SOCIAL_URL = os.getenv("SOCIAL_URL")
