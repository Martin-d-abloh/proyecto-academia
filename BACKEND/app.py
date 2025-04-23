from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
import os
from database import db
from models import db, Administrador, Alumno, Tabla, Documento
from routes.admin_routes import admin_bp
from routes.alumno_routes import alumno_bp

def create_app():
    load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

    uri = os.getenv("SQLALCHEMY_DATABASE_URI")
    print("📦 URI desde .env:", uri)

    app = Flask(__name__)
    frontend_url = os.getenv("FRONTEND_URL", "https://proyecto-academia.vercel.app")

    #CORS(app, origins=[
     #   "https://proyecto-academia.duckdns.org",
      #  "https://proyecto-academia.vercel.app"
    #], supports_credentials=True)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
    app.secret_key = "supersecreto"
    app.config.update(
        SESSION_COOKIE_SAMESITE="None",
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=False
    )

    db.init_app(app)

    # Registro de blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(alumno_bp)

    # Validación simple de entorno
    if not os.getenv("SUPERADMIN_USUARIO") or not os.getenv("SUPERADMIN_CONTRASENA"):
        raise Exception("Debes definir SUPERADMIN_USUARIO y SUPERADMIN_CONTRASENA en tu archivo .env")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5001)

