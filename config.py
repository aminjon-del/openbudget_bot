import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
SHTAB_GROUP_ID = int(os.getenv("SHTAB_GROUP_ID", "-100123456789"))

# Baza havolasi (Render uchun bittalik havola)
DATABASE_URL = os.getenv("DATABASE_URL", None)

# Alohida parametrlar (agar URL berilmasa)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "openbudget_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "secretpassword")
