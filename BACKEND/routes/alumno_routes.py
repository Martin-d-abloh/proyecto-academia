import os
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g, send_file, current_app as app
from models import Alumno, Documento, Tabla
from decoradores import alumno_token_required
from utils import generar_hash_credencial, normalizar
from models import db
import mimetypes

alumno_bp = Blueprint("alumno_bp", __name__)

@alumno_bp.route("/api/alumno/<uuid:alumno_id>/subir", methods=["POST"])
@alumno_token_required
def api_subir_documentos(alumno_id):
    try:
        archivo = request.files.get('archivo')
        doc_nombre = request.form.get('nombre_documento')

        if not archivo or not archivo.filename or not doc_nombre:
            return jsonify({"error": "Faltan datos"}), 400

        alumno = Alumno.query.get_or_404(str(alumno_id))
        tabla = alumno.tabla

        if not Documento.query.filter_by(tabla_id=tabla.id, nombre=doc_nombre, alumno_id=None).first():
            return jsonify({"error": "Documento no requerido para esta tabla"}), 400

        doc_existente = Documento.query.filter_by(
            tabla_id=tabla.id,
            alumno_id=alumno.id,
            nombre=doc_nombre
        ).first()

        extension = os.path.splitext(archivo.filename)[1].lower()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{alumno.id}_{doc_nombre}_{timestamp}{extension}"
        path_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(tabla.id), str(alumno.id))
        os.makedirs(path_dir, exist_ok=True)
        ruta = os.path.join(path_dir, filename)

        if doc_existente:
            if doc_existente.ruta and os.path.exists(doc_existente.ruta):
                os.remove(doc_existente.ruta)
            db.session.delete(doc_existente)

        archivo.save(ruta)

        nuevo_doc = Documento(
            nombre=doc_nombre,
            tabla_id=tabla.id,
            alumno_id=alumno.id,
            nombre_archivo=filename,
            ruta=ruta,
            estado='subido'
        )
        db.session.add(nuevo_doc)
        db.session.commit()

        return jsonify({
            "mensaje": "Documento subido correctamente",
            "documento": {
                "id": nuevo_doc.id,
                "nombre": nuevo_doc.nombre,
                "estado": nuevo_doc.estado
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error en subida API: {str(e)}")
        return jsonify({"error": "Error interno al subir"}), 500


@alumno_bp.route("/api/alumno/<uuid:alumno_id>/documentos", methods=["GET"])
@alumno_token_required
def api_documentos_alumno(alumno_id):
    alumno = Alumno.query.get_or_404(str(alumno_id))
    tabla = alumno.tabla

    documentos_requeridos = Documento.query.filter_by(
        tabla_id=tabla.id, 
        alumno_id=None
    ).all()

    documentos_subidos = Documento.query.filter_by(
        tabla_id=tabla.id, 
        alumno_id=alumno.id
    ).all()

    subidos_dict = {doc.nombre: doc for doc in documentos_subidos}

    documentos = []
    for doc in documentos_requeridos:
        doc_info = {
            "nombre": doc.nombre,
            "estado": "no_subido",
            "subido": False,
            "id": None
        }

        if doc.nombre in subidos_dict:
            subido = subidos_dict[doc.nombre]
            doc_info["estado"] = subido.estado
            doc_info["subido"] = True
            doc_info["id"] = subido.id

        documentos.append(doc_info)

    return jsonify({"documentos": documentos}), 200


@alumno_bp.route("/api/alumno/<uuid:alumno_id>/documentos/<int:doc_id>/eliminar", methods=["DELETE"])
@alumno_token_required
def api_eliminar_documento(alumno_id, doc_id):
    doc = Documento.query.get_or_404(doc_id)

    if str(doc.alumno_id) != str(alumno_id):
        return jsonify({"error": "Este documento no te pertenece"}), 403

    try:
        if doc.ruta and os.path.exists(doc.ruta):
            os.remove(doc.ruta)

        db.session.delete(doc)
        db.session.commit()
        return jsonify({"mensaje": "Documento eliminado"}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al eliminar documento: {str(e)}")
        return jsonify({"error": "Error al eliminar el documento"}), 500


@alumno_bp.route("/api/alumno/<int:id>", methods=["GET"])
@alumno_token_required
def api_ver_alumno(id):
    alumno = Alumno.query.get_or_404(id)
    return jsonify({
        "id": alumno.id,
        "nombre": alumno.nombre,
        "apellidos": alumno.apellidos,
        "tabla_id": alumno.tabla_id
    }), 200


@alumno_bp.route("/api/login_alumno", methods=["POST"])
def api_login_alumno():
    data = request.get_json()
    print("📦 DATA RECIBIDA:", data)

    credencial_raw = data.get("credencial", "").strip()

    if not credencial_raw:
        return jsonify({"error": "Credencial requerida"}), 400

    partes = credencial_raw.split()
    if len(partes) < 2:
        return jsonify({"error": "Introduce nombre y apellidos"}), 400

    nombre = normalizar(partes[0])
    apellidos = normalizar(" ".join(partes[1:]))
    credencial_hash = generar_hash_credencial(nombre, apellidos)

    print("---- DEBUG LOGIN ALUMNO API ----")
    print(f"Credencial raw: {credencial_raw}")
    print(f"Nombre normalizado: {nombre}")
    print(f"Apellidos normalizados: {apellidos}")
    print(f"Hash generado: {credencial_hash}")

    alumno = Alumno.query.filter_by(credencial=credencial_hash).first()
    if alumno:

        token = jwt.encode({
            "alumno_id": str(alumno.id),
            "exp": datetime.utcnow() + timedelta(hours=12)
        }, os.getenv("JWT_SECRET_KEY"), algorithm="HS256")

        return jsonify({"token": token, "alumno_id": str(alumno.id)})


    return jsonify({"error": "Credenciales incorrectas"}), 401

@alumno_bp.route("/api/alumno/ver/<int:doc_id>")
def ver_documento_alumno(doc_id):
    token = request.args.get("token")

    if not token:
        return jsonify({"error": "Token requerido"}), 401

    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        alumno_id = payload.get("alumno_id")
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expirado"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token inválido"}), 403

    doc = Documento.query.get_or_404(doc_id)
    if str(doc.alumno_id) != str(alumno_id):
        return jsonify({"error": "No tienes permiso para ver este documento"}), 403

    if not os.path.exists(doc.ruta):
        return jsonify({"error": "Archivo no encontrado"}), 404

    mimetype, _ = mimetypes.guess_type(doc.ruta)
    return send_file(doc.ruta, mimetype=mimetype or "application/octet-stream")

@alumno_bp.route("/api/public/alumno/<uuid:id>", methods=["GET"])
def api_public_ver_alumno(id):
    alumno = Alumno.query.get_or_404(str(id))
    return jsonify({
        "id": alumno.id,
        "nombre": alumno.nombre,
        "apellidos": alumno.apellidos
    }), 200
