from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import os
from database import init_db
from models import db, Administrador, Alumno, Tabla, Documento
from routes.admin_routes import admin_bp
from routes.alumno_routes import alumno_bp


def create_app():
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

    uri = os.getenv("SQLALCHEMY_DATABASE_URI")
    print("📦 URI desde .env:", uri)

    app = Flask(__name__)
    frontend_url = os.getenv("FRONTEND_URL", "https://proyecto-academia.vercel.app")

    CORS(app, origins=[
        "https://proyecto-academia.duckdns.org",
        "https://proyecto-academia.vercel.app"
    ], supports_credentials=True)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
    app.secret_key = "supersecreto"
    app.config.update(
        SESSION_COOKIE_SAMESITE="None",
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=False
    )

    init_db(app)


    # Registro de blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(alumno_bp)

    # Crear superadmin automáticamente si no existe
    usuario = os.getenv("SUPERADMIN_USUARIO")
    contrasena = os.getenv("SUPERADMIN_CONTRASENA")

    if not usuario or not contrasena:
        raise Exception("Debes definir SUPERADMIN_USUARIO y SUPERADMIN_CONTRASENA en tu archivo .env")

    with app.app_context():
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

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
