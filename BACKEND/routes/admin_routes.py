import os
import jwt
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, g, current_app as app
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Tabla, Documento, Administrador, Alumno
from decoradores import token_required, superadmin_token_required
from utils import generar_hash_credencial, normalizar
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError


admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/api/login", methods=["POST"])
def api_login_admin():
    data = request.get_json()
    usuario = data.get("usuario", "").strip().lower()
    contrasena = data.get("contrasena", "").strip()

    admin = Administrador.query.filter_by(usuario=usuario).first()
    if admin and admin.check_password(contrasena):
        payload = {
            "usuario": admin.usuario,
            "id": admin.id,
            "es_superadmin": admin.es_superadmin,
            "exp": datetime.now(timezone.utc) + timedelta(hours=12)
        }
        token = jwt.encode(payload, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")
        return jsonify({
            "token": token,
            "es_superadmin": admin.es_superadmin,
            "usuario": admin.usuario
        }), 200

    return jsonify({"error": "Credenciales incorrectas"}), 401


@admin_bp.route("/api/admin/tabla/<int:id_tabla>/alumnos", methods=["POST"])
@token_required
def api_crear_alumno(current_admin, id_tabla):
    data = request.get_json()
    nombre = data.get("nombre")
    apellidos = data.get("apellidos")

    if not nombre or not apellidos:
        return jsonify({"error": "Faltan datos del alumno"}), 400

    tabla = Tabla.query.get_or_404(id_tabla)

    if current_admin.id != tabla.admin_id and not current_admin.es_superadmin:
        return jsonify({"error": "Acceso denegado"}), 403

    credencial = generar_hash_credencial(normalizar(nombre), normalizar(apellidos))
    password_claro = f"{nombre} {apellidos}".strip()

    nuevo = Alumno(
        nombre=nombre,
        apellidos=apellidos,
        tabla_id=id_tabla,
        credencial=credencial
    )
    nuevo.set_password(password_claro)

    db.session.add(nuevo)
    db.session.commit()

    return jsonify({"mensaje": "Alumno creado", "id": nuevo.id}), 201

@admin_bp.route("/api/admin/tabla/<int:id>", methods=["DELETE"])
@token_required
def api_eliminar_tabla(current_admin, id):
    tabla = Tabla.query.get_or_404(id)

    if current_admin.id != tabla.admin_id and not current_admin.es_superadmin:
        return jsonify({"error": "Acceso denegado"}), 403

    db.session.delete(tabla)
    db.session.commit()
    return jsonify({"mensaje": "Tabla eliminada"}), 200

@admin_bp.route("/api/admin/tablas", methods=["POST"])
@token_required
def api_crear_tabla(current_admin):
    data = request.get_json()
    nombre = data.get("nombre")

    if not nombre:
        return jsonify({"error": "Nombre requerido"}), 400

    nueva = Tabla(nombre=nombre, admin_id=current_admin.id)
    db.session.add(nueva)
    db.session.commit()

    return jsonify({"mensaje": "Tabla creada"}), 201



@admin_bp.route("/api/superadmin/admins", methods=["POST"])
@superadmin_token_required
def api_crear_admin():
    data = request.get_json()
    nombre = data.get("nombre")
    usuario = data.get("usuario")  # Campo requerido por el modelo
    contraseña = data.get("contraseña")

    # Validar campos obligatorios
    if not nombre or not contraseña or not usuario:
        return jsonify({"error": "Faltan datos: nombre, usuario o contraseña"}), 400

    # Verificar si ya existe el nombre o usuario
    if Administrador.query.filter(
        (Administrador.nombre == nombre) | (Administrador.usuario == usuario)
    ).first():
        return jsonify({"error": "Nombre de admin o usuario ya registrado"}), 400

    try:
        admin = Administrador(nombre=nombre, usuario=usuario)
        admin.password = contraseña  
        db.session.add(admin)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "El nombre o usuario ya existen"}), 400

    return jsonify({"mensaje": "Admin creado"}), 201


@admin_bp.route("/api/superadmin/admins", methods=["GET"])
@superadmin_token_required
def api_listar_admins():
    admins = Administrador.query.all()
    datos = [{"id": a.id, "nombre": a.nombre} for a in admins]
    return jsonify({"admins": datos}), 200

@admin_bp.route("/api/superadmin/admins/<int:id>", methods=["DELETE"])
@superadmin_token_required
def api_eliminar_admin(id):
    admin = Administrador.query.get_or_404(id)
    db.session.delete(admin)
    db.session.commit()
    return jsonify({"mensaje": "Admin eliminado"}), 200

@admin_bp.route("/api/admin/tabla/<int:tabla_id>/documento/<int:doc_id>", methods=["DELETE"])
@token_required
def api_eliminar_documento_tabla(current_admin, tabla_id, doc_id):
    tabla = Tabla.query.get_or_404(tabla_id)
    documento = Documento.query.get_or_404(doc_id)

    if current_admin.id != tabla.admin_id and not current_admin.es_superadmin:
        return jsonify({"error": "Acceso denegado"}), 403

    try:
        if documento.ruta and os.path.exists(documento.ruta):
            os.remove(documento.ruta)

        db.session.delete(documento)
        db.session.commit()
        return jsonify({"mensaje": "Documento eliminado"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al eliminar documento: {str(e)}")
        return jsonify({"error": "Error al eliminar documento"}), 500

@admin_bp.route("/api/admin/tabla/<int:id>/documento", methods=["POST"])
@token_required
def api_añadir_documento(current_admin, id):
    data = request.get_json()
    nombre_doc = data.get("nombre")

    if not nombre_doc:
        return jsonify({"error": "Nombre del documento requerido"}), 400

    tabla = Tabla.query.get_or_404(id)

    if current_admin.id != tabla.admin_id and not current_admin.es_superadmin:
        return jsonify({"error": "Acceso denegado"}), 403

    nuevo = Documento(
        nombre=nombre_doc,
        tabla_id=tabla.id,
        alumno_id=None,
        estado="requerido"
    )

    db.session.add(nuevo)
    db.session.commit()

    return jsonify({"mensaje": "Documento creado"}), 201

@admin_bp.route("/api/admin/tabla/<int:id>", methods=["GET"])
@token_required
def api_ver_tabla(current_admin, id):
    tabla = Tabla.query.get_or_404(id)
    print("TABLA:", tabla.id, "ADMIN DE TABLA:", tabla.admin_id, "ADMIN LOGUEADO:", current_admin.id)

    if current_admin.id != tabla.admin_id and not current_admin.es_superadmin:
        print("❌ ACCESO DENEGADO")
        return jsonify({"error": "Acceso denegado"}), 403

    alumnos = [
        {"id": a.id, "nombre": a.nombre, "apellidos": a.apellidos}
        for a in tabla.alumnos
    ]
    print("📚 Alumnos encontrados:", alumnos)

    documentos = [
        {"id": d.id, "nombre": d.nombre}
        for d in tabla.documentos if d.alumno_id is None
    ]
    print("📄 Documentos requeridos:", documentos)

    documentos_subidos = Documento.query.filter_by(tabla_id=tabla.id).filter(Documento.alumno_id.isnot(None)).all()
    print("📥 Subidos encontrados:", len(documentos_subidos))

    subidos = []
    for d in documentos_subidos:
        subidos.append({
            "id": d.id,
            "nombre": d.nombre,
            "alumno_id": d.alumno.id,
            "alumno_nombre": f"{d.alumno.nombre} {d.alumno.apellidos}",
            "estado": d.estado
        })

    return jsonify({
        "id": tabla.id,
        "nombre": tabla.nombre,
        "alumnos": alumnos,
        "documentos": documentos,
        "subidos": subidos
    }), 200



@admin_bp.route("/api/admin/tablas", methods=["GET"])
@token_required
def api_listar_tablas(current_admin):
    admin_id_param = request.args.get("admin_id")

    if current_admin.es_superadmin and admin_id_param:
        try:
            admin_id = int(admin_id_param)
        except ValueError:
            return jsonify({"error": "ID inválido"}), 400
    else:
        admin_id = current_admin.id

    tablas = Tabla.query.filter_by(admin_id=admin_id).all()

    resultado = []
    for tabla in tablas:
        resultado.append({
            "id": tabla.id,
            "nombre": tabla.nombre,
            "alumnos": len(tabla.alumnos)
        })

    return jsonify({"tablas": resultado}), 200



@admin_bp.route("/api/superadmin/tabla/<int:id>", methods=["GET"])
@superadmin_token_required
def api_ver_tabla_superadmin(id):
    tabla = Tabla.query.get_or_404(id)

    alumnos = [
        {"id": a.id, "nombre": a.nombre, "apellidos": a.apellidos}
        for a in tabla.alumnos
    ]
    print("📚 Alumnos encontrados (superadmin):", alumnos)

    documentos = [
        {"id": d.id, "nombre": d.nombre}
        for d in tabla.documentos if d.alumno_id is None
    ]
    print("📄 Documentos requeridos (superadmin):", documentos)

    documentos_subidos = Documento.query.filter_by(tabla_id=tabla.id).filter(Documento.alumno_id.isnot(None)).all()
    print("📥 Subidos encontrados (superadmin):", len(documentos_subidos))

    subidos = []
    for d in documentos_subidos:
        subidos.append({
            "id": d.id,
            "nombre": d.nombre,
            "alumno_id": d.alumno.id,
            "alumno_nombre": f"{d.alumno.nombre} {d.alumno.apellidos}",
            "estado": d.estado
        })

    return jsonify({
        "id": tabla.id,
        "nombre": tabla.nombre,
        "alumnos": alumnos,
        "documentos": documentos,
        "subidos": subidos
    }), 200




@admin_bp.route("/api/superadmin/panel_admin/<int:admin_id>", methods=["GET"])
@superadmin_token_required
def api_panel_admin_completo(admin_id):
    admin = Administrador.query.get_or_404(admin_id)
    tablas = Tabla.query.filter_by(admin_id=admin.id).all()

    resultado = []
    for tabla in tablas:
        alumnos = [{
            "id": a.id,
            "nombre": a.nombre,
            "apellidos": a.apellidos
        } for a in tabla.alumnos]

        documentos = [{
            "id": d.id,
            "nombre": d.nombre
        } for d in tabla.documentos if d.alumno_id is None]

        subidos = [{
            "id": d.id,
            "nombre": d.nombre,
            "alumno_id": d.alumno.id,
            "alumno_nombre": f"{d.alumno.nombre} {d.alumno.apellidos}",
            "estado": d.estado
        } for d in tabla.documentos if d.alumno_id is not None]

        resultado.append({
            "id": tabla.id,
            "nombre": tabla.nombre,
            "alumnos": alumnos,
            "documentos": documentos,
            "subidos": subidos
        })

    return jsonify({
        "admin_id": admin.id,
        "admin_nombre": admin.nombre,
        "tablas": resultado
    }), 200







