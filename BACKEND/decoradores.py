from functools import wraps
from flask import request, jsonify
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
        if not token:
            return jsonify({'error': 'Token requerido'}), 403

        try:
            data = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
            alumno = Alumno.query.get_or_404(kwargs.get("alumno_id"))
            if str(alumno.id) != str(data.get("alumno_id")):
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
