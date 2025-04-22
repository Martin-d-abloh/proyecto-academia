from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from app import create_app
from models import db

# Test de URI
print("🧪 URI directa desde os.getenv:", os.getenv("SQLALCHEMY_DATABASE_URI"))

app = create_app()

print("📦 URI desde .env:", os.getenv("SQLALCHEMY_DATABASE_URI"))
print("📦 Usando URI:", app.config["SQLALCHEMY_DATABASE_URI"])

with app.app_context():
    db.create_all()
    print("✅ Tablas creadas correctamente en la base de datos REAL")
