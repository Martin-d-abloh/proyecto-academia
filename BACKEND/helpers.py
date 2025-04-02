
from flask import session
from models import Administrador

def obtener_admin_actual():
    """
    Devuelve el objeto Administrador actual si hay un usuario en sesión.
    Si no hay sesión activa, devuelve None.
    """
    usuario = session.get("usuario_admin")
    if usuario:
        return Administrador.query.filter_by(usuario=usuario).first()
    return None
