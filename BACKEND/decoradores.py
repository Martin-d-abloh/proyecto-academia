from functools import wraps
from flask import request, jsonify, g 
import jwt
from models import Administrador, Alumno
import os

# JWT para ADMIN
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extraer_token()
        if not token:
            return jsonify({'error': 'Token requerido'}), 403

        try:
            data = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
            current_admin = Administrador.query.filter_by(usuario=data['usuario']).first()
            if not current_admin:
                raise Exception("Admin no encontrado")
        except Exception as e:
            return jsonify({'error': f'Token inválido: {str(e)}'}), 403

        return f(current_admin, *args, **kwargs)
    return decorated

# JWT para SUPERADMIN
def superadmin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extraer_token()
        if not token:
            return jsonify({'error': 'Token requerido'}), 403

        try:
            data = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
            if not data.get("es_superadmin"):
                raise Exception("No eres superadmin")
        except Exception as e:
            return jsonify({'error': f'Token inválido: {str(e)}'}), 403

        return f(*args, **kwargs)
    return decorated

# JWT para ALUMNO
def alumno_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extraer_token()
        print("🧪 TOKEN EXTRAÍDO:", token)

        if not token:
            print("❌ No se encontró token en headers.")
            return jsonify({'error': 'Token requerido'}), 403

        try:
            data = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
            print("📦 DATA DEL TOKEN:", data)

            alumno_id_token = str(data.get("alumno_id"))
            alumno_id_url = str(kwargs.get("alumno_id"))
            print(f"🔐 Comparando token-alumno: token={alumno_id_token} vs url={alumno_id_url}")

            if alumno_id_token != alumno_id_url:
                raise Exception("Token no válido para este alumno")

        except Exception as e:
            print("💥 EXCEPCIÓN EN DECORADOR:", str(e))
            return jsonify({'error': f'Token inválido: {str(e)}'}), 403

        return f(*args, **kwargs)
    return decorated
#TOKEN MIXTO
def token_admin_o_superadmin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({'error': 'Token requerido'}), 403

        try:
            data = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
            rol = data.get("rol")
            if rol == "admin":
                current_admin = Administrador.query.filter_by(usuario=data['usuario']).first()
                if not current_admin:
                    raise Exception("Admin no encontrado")
                g.usuario_id = current_admin.id
                g.rol = "admin"
            elif rol == "superadmin":
                g.usuario_id = data["id"]
                g.rol = "superadmin"
            else:
                return jsonify({'error': 'Rol no autorizado'}), 403

        except Exception as e:
            return jsonify({'error': f'Token inválido: {str(e)}'}), 403

        return f(*args, **kwargs)
    return decorated



# Función auxiliar
def extraer_token():
    if 'Authorization' in request.headers:
        return request.headers['Authorization'].split(" ")[1]
    return None
