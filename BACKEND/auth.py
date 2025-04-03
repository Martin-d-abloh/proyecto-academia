import jwt
from flask import request, jsonify
from functools import wraps
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

def token_requerido(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token:
            return jsonify({'error': 'Token requerido'}), 401

        try:
            datos = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.usuario_jwt = datos['usuario']
            request.es_superadmin = datos.get('es_superadmin', False)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401

        return f(*args, **kwargs)

    return decorada
