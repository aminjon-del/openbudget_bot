import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # O'zingizning Telegram ID'ingiz
SHTAB_GROUP_ID = int(os.getenv("SHTAB_GROUP_ID", "-100123456789"))  # Shtab guruhi ID'si

# Baza sozlamalari
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "openbudget_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "secretpassword")