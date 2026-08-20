import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SHTAB_GROUP_ID = int(os.getenv("SHTAB_GROUP_ID", "0"))

# Render uchun PostgreSQL to'liq havola (Internal Database URL)
DATABASE_URL = os.getenv("DATABASE_URL", None)

# Lokal yoki Docker-compose uchun parametrlar
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "openbudget_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "secretpassword")
