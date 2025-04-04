from functools import wraps
from flask import request, jsonify, g 
import jwt
from models import Administrador, Alumno
import os

# JWT para ADMIN
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({'error': 'Token requerido'}), 403

        try:
            data = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
            admin_id = data.get("id")
            if not admin_id:
                return jsonify({'error': 'ID no presente en token'}), 403

            current_admin = Administrador.query.get(admin_id)
            if not current_admin:
                return jsonify({'error': 'Admin no encontrado'}), 403

        except Exception as e:
            return jsonify({'error': f'Token inválido: {str(e)}'}), 403

        return f(current_admin, *args, **kwargs)
    return decorated


# JWT para SUPERADMIN

def superadmin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
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
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({'error': 'Token requerido'}), 403

        try:
            data = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
            alumno_id_token = str(data.get("alumno_id"))
            alumno_id_url = str(kwargs.get("alumno_id"))

            if alumno_id_token != alumno_id_url:
                raise Exception("Token no válido para este alumno")

        except Exception as e:
            return jsonify({'error': f'Token inválido: {str(e)}'}), 403

        return f(*args, **kwargs)
    return decorated

# Función auxiliar
def extraer_token():
    if 'Authorization' in request.headers:
        return request.headers['Authorization'].split(" ")[1]
    return None
