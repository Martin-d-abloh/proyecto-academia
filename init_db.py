import os
from dotenv import load_dotenv
from app import create_app
from models import db, Administrador

load_dotenv()
app = create_app()

with app.app_context():
    db.create_all()

    # Leer superadmin desde .env
    usuario = os.getenv("SUPERADMIN_USUARIO")
    contrasena = os.getenv("SUPERADMIN_CONTRASENA")

    if not usuario or not contrasena:
        raise Exception("Faltan SUPERADMIN_USUARIO o SUPERADMIN_CONTRASENA en el .env")

    if not Administrador.query.filter_by(usuario=usuario).first():
        nuevo_admin = Administrador(
            nombre="Super Admin",
            usuario=usuario,
            es_superadmin=True
        )
        nuevo_admin.password = contrasena
        db.session.add(nuevo_admin)
        db.session.commit()
        print(f"✅ Superadmin creado con usuario={usuario} y contraseña={contrasena}")
    else:
        print(f"ℹ️ Ya existe un administrador con usuario={usuario}")

    print("✅ Tablas creadas exitosamente!")
