from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from app import create_app
from models import db, Administrador

# Test de URI
print("🧪 URI directa desde os.getenv:", os.getenv("SQLALCHEMY_DATABASE_URI"))

app = create_app()

print("📦 URI desde .env:", os.getenv("SQLALCHEMY_DATABASE_URI"))
print("📦 Usando URI:", app.config["SQLALCHEMY_DATABASE_URI"])

with app.app_context():
    db.create_all()
    print("✅ Tablas creadas correctamente en la base de datos REAL")

    # Crear superadmin si no existe
    usuario = os.getenv("SUPERADMIN_USUARIO")
    contrasena = os.getenv("SUPERADMIN_CONTRASENA")

    if not usuario or not contrasena:
        raise Exception("Debes definir SUPERADMIN_USUARIO y SUPERADMIN_CONTRASENA en tu archivo .env")

    admin_existente = Administrador.query.filter_by(usuario=usuario).first()
    if not admin_existente:
        superadmin = Administrador(
            nombre="Super Admin",
            usuario=usuario,
            es_superadmin=True
        )
        superadmin.password = contrasena
        db.session.add(superadmin)
        db.session.commit()
        print("✅ Superadmin creado correctamente:", usuario)
    else:
        print("ℹ️ Superadmin ya existe:", usuario)
