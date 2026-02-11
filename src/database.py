from databases import Database
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://xyz_user:xyz_password@localhost:5432/xyz_db")

database = Database(POSTGRES_URL)

async def get_db():
    if not database.is_connected:
        await database.connect()
    return database
