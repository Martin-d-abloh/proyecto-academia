# 1. Flask y extensiones 
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    send_file,  
    session, 
    jsonify
)

from werkzeug.utils import secure_filename

# 2. Utilidades estándar de Python 
import os
import re
import unicodedata 

# 3. Variables de entorno
from dotenv import load_dotenv
# 4. Base de datos y modelos 
from database import init_db
from models import (
    db,
    Administrador,
    Alumno,
    Tabla,
    Documento,
)
# 5. helpers
from helpers import obtener_admin_actual
import hashlib
from datetime import datetime

from flask_cors import CORS


# Cargar variables de entorno
load_dotenv()
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}

def normalizar(texto):
    texto = texto.lower().replace(" ", "")
    texto = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn' or c == 'ñ')

def generar_hash_credencial(nombre: str, apellidos: str) -> str:
    completo = normalizar(nombre + apellidos)
    return hashlib.sha256(completo.encode()).hexdigest()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    init_db(app)
    app.secret_key = "supersecreto"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # ✅ Leemos las variables de entorno
    usuario = os.getenv("SUPERADMIN_USUARIO")
    contrasena = os.getenv("SUPERADMIN_CONTRASENA")

    if not usuario or not contrasena:
        raise Exception("Debes definir SUPERADMIN_USUARIO y SUPERADMIN_CONTRASENA en tu archivo .env")

    # ✅ Creamos el superadmin solo si no existe en la base de datos
    with app.app_context():
        admin_existente = Administrador.query.filter_by(usuario=usuario).first()
        if not admin_existente:
            superadmin = Administrador(
                nombre="Super Admin",
                usuario=usuario,
                es_superadmin=True
            )
            superadmin.password = contrasena  # esto guarda el hash
            db.session.add(superadmin)
            db.session.commit()
            print("✅ Superadmin creado correctamente:", usuario)
        else:
            print("ℹ️ Superadmin ya existe:", usuario)




    @app.route("/", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            if request.is_json:
                # Petición desde React
                data = request.get_json()
                usuario = data.get("usuario", "").lower().strip()
                contrasena = data.get("contrasena", "").strip()
            else:
                # Petición desde formulario HTML
                usuario = request.form.get("usuario", "").lower().strip()
                contrasena = request.form.get("contrasena", "").strip()

            admin = Administrador.query.filter_by(usuario=usuario).first()

            if admin and admin.check_password(contrasena):
                session["usuario_admin"] = usuario

                if request.is_json:
                    return jsonify({
                        "mensaje": "Login exitoso",
                        "usuario": usuario,
                        "es_superadmin": admin.es_superadmin
                    }), 200
                else:
                    flash(f"Bienvenido, {admin.nombre}", "success")
                    if admin.es_superadmin:
                        return redirect(url_for("superadmin_home"))
                    else:
                        return redirect(url_for("admin_home"))

            else:
                if request.is_json:
                    return jsonify({"error": "Credenciales incorrectas"}), 401
                else:
                    flash("Credenciales incorrectas", "error")

        return render_template("login.html", admin_actual=obtener_admin_actual())







    @app.route("/logout_admin")
    def logout_admin():
        session.pop('usuario_admin', None)
        flash("Sesión cerrada correctamente", "info")
        return redirect(url_for("login"))

    @app.route("/logout_superadmin")
    def logout_superadmin():
        session.pop('usuario_admin', None)
        flash("Sesión cerrada correctamente", "info")
        return redirect(url_for("login"))
    @app.route("/logout_alumno")
    def logout_alumno():
        session.pop('usuario_alumno', None)
        flash("Sesión cerrada correctamente", "info")
        return redirect(url_for("login_alumno"))


    @app.route("/crear_admin", methods=["GET", "POST"])
    def crear_admin():
        if not session.get("usuario_admin"):
            return redirect(url_for("login"))
        
        admin_actual = obtener_admin_actual()

        if not admin_actual or not admin_actual.es_superadmin:
            flash("Acceso restringido al superadministrador", "error")
            return redirect(url_for("superadmin_home"))

        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            usuario_nuevo = request.form.get("usuario", "").strip()
            contrasena = request.form.get("contrasena", "").strip()

            if not all([nombre, usuario_nuevo, contrasena]):
                flash("Todos los campos son obligatorios", "error")
                return redirect(url_for("crear_admin"))

            usuario_nuevo = normalizar(usuario_nuevo)

            if Administrador.query.filter_by(usuario=usuario_nuevo).first():
                flash("Ya existe un administrador con ese usuario", "error")
                return redirect(url_for("crear_admin"))

            try:
                nuevo_admin = Administrador(
                    nombre=nombre,
                    usuario=usuario_nuevo,
                    es_superadmin=False
                )
                nuevo_admin.password = contrasena
                db.session.add(nuevo_admin)
                db.session.commit()

                flash(f"Administrador '{nombre}' creado correctamente", "success")
                return redirect(url_for("superadmin_home"))

            except Exception as e:
                db.session.rollback()
                flash("Error al crear el administrador", "error")
                app.logger.error(f"Error en crear_admin: {str(e)}")

        return render_template("superadmin/crear_admin.html", admin_actual=admin_actual)



    # Actualizar eliminar_admin() - reemplaza tu versión actual con:
    @app.route("/eliminar_admin/<usuario>", methods=["POST"])
    def eliminar_admin(usuario):
        if not session.get('usuario_admin'):
            return redirect(url_for('login'))
        
        admin_actual = Administrador.query.filter_by(usuario=session['usuario_admin']).first()
        
        if not admin_actual or not admin_actual.es_superadmin:
            flash("Acceso restringido", "error")
            return redirect(url_for('login'))

        admin = Administrador.query.filter_by(usuario=usuario).first()
        if admin:
            db.session.delete(admin)
            db.session.commit()
            flash("Administrador eliminado", "success")
        else:
            flash("Administrador no encontrado", "error")
        
        return redirect(url_for('superadmin_home'))



    @app.route("/crear_tabla", methods=["GET", "POST"])
    def crear_tabla():
        if not session.get('usuario_admin'):
            return redirect(url_for('login'))

        admin_actual = obtener_admin_actual()
        if not admin_actual:
            flash("Administrador no encontrado", "error")
            return redirect(url_for('login'))

        if request.method == "POST":
            nombre_tabla = request.form.get("nombre_tabla", "").strip()
            num_docs = int(request.form.get("num_documentos", 0))
            
            documentos = [
                request.form.get(f"documento_{i}", "").strip() 
                for i in range(1, num_docs + 1)
                if request.form.get(f"documento_{i}", "").strip()
            ]

            if not nombre_tabla or not documentos:
                flash("Nombre y documentos son obligatorios", "error")
                return redirect(url_for('crear_tabla'))

            try:
                nueva_tabla = Tabla(
                        nombre=nombre_tabla,
                        admin_id=admin_actual.id,
                        documentos=[Documento(nombre=doc) for doc in documentos]
                    )

                
                db.session.add(nueva_tabla)
                db.session.commit()

                flash(f"Tabla '{nombre_tabla}' creada", "success")
                return redirect(url_for('admin_home'))

            except Exception as e:
                db.session.rollback()
                flash("Error al crear tabla", "error")
                app.logger.error(f"Error en crear_tabla: {str(e)}")

        return render_template("tablas/crear_tabla.html", admin_actual=admin_actual)



    @app.route("/tablas/<int:id_tabla>")
    def ver_tabla(id_tabla):
        if not session.get('usuario_admin'):
            return redirect(url_for('login'))

        tabla = Tabla.query.options(
            db.joinedload(Tabla.alumnos).joinedload(Alumno.documentos),
            db.joinedload(Tabla.documentos)
        ).get_or_404(id_tabla)

        admin_actual = obtener_admin_actual()
        if not admin_actual or (admin_actual.id != tabla.admin_id and not admin_actual.es_superadmin):
            flash("Acceso denegado", "error")
            return redirect(url_for('admin_home'))

        documentos_requeridos = [doc for doc in tabla.documentos if doc.es_requerido()]

        alumnos_con_docs = []
        for alumno in tabla.alumnos:
            alumnos_con_docs.append({
                'alumno': alumno,
                'documentos': {doc.nombre: doc for doc in alumno.documentos}
            })

        return render_template("tablas/ver_tabla.html", 
                            tabla=tabla,
                            documentos_requeridos=documentos_requeridos,
                            alumnos=alumnos_con_docs,
                            admin_actual=admin_actual)


        

    @app.route("/eliminar_tabla/<int:id_tabla>", methods=["POST"])
    def eliminar_tabla(id_tabla):
        if not session.get('usuario_admin'):
            return redirect(url_for('login'))
        
        tabla = Tabla.query.get_or_404(id_tabla)
        admin = Administrador.query.filter_by(usuario=session['usuario_admin']).first()
        
        if not admin or (admin.id != tabla.admin_id and not admin.es_superadmin):
            flash("No tienes permisos", "error")
            return redirect(url_for('admin_home'))

        try:
            db.session.delete(tabla)
            db.session.commit()
            flash("Tabla eliminada", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error crítico al eliminar", "error")
            app.logger.error(f"Error eliminando tabla {id_tabla}: {str(e)}")
        
        return redirect(url_for('admin_home'))

   
    @app.route("/tablas/<int:id_tabla>/crear_alumno", methods=["GET", "POST"])
    def crear_alumno(id_tabla):
        if not session.get('usuario_admin'):
            return redirect(url_for('login'))

        admin_actual = obtener_admin_actual()

        tabla = Tabla.query.get(id_tabla)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for('admin_home'))

        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            apellidos = request.form.get("apellidos", "").strip()
            
            if not nombre or not apellidos:
                flash("Nombre y apellidos son obligatorios", "error")
                return redirect(url_for('crear_alumno', id_tabla=id_tabla))

            try:
                # Generar un ID único en base al contenido
                alumno_id = hashlib.sha256(f"{nombre}{apellidos}{id_tabla}".encode()).hexdigest()[:32]
                print(f"ID generado para el alumno: {alumno_id}")  # Ver el ID generado

                # Crear el nuevo alumno
                nuevo_alumno = Alumno(
                    id=alumno_id,
                    nombre=nombre,
                    email=f"{nombre.lower()}.{apellidos.lower()}@fakemail.com",
                    apellidos=apellidos,
                    tabla_id=id_tabla
                )
                # Contraseña: genera la contraseña como el nombre + apellidos
                password = f"{nombre}{apellidos}"
                print(f"Contraseña generada: {password}")  # Ver la contraseña generada
                nuevo_alumno.set_password(password)

                # Agregar a la base de datos
                db.session.add(nuevo_alumno)
                db.session.commit()

                flash(f"Alumno {nombre} {apellidos} creado", "success")
                return redirect(url_for('ver_tabla', id_tabla=id_tabla))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Error al crear alumno: {e}", "error")
                app.logger.error(f"Error en crear_alumno: {str(e)}")

        return render_template("alumnos/crear_alumno.html", tabla=tabla, admin_actual=admin_actual)



    @app.route("/alumno/<alumno_id>", methods=["GET", "POST"])
    def ver_alumno(alumno_id):
        
        if not session.get('usuario_alumno') or str(session['usuario_alumno']) != str(alumno_id):
            flash("Debes iniciar sesión primero", "error")
            return redirect(url_for('login_alumno'))
        
        alumno = Alumno.query.options(
            db.joinedload(Alumno.tabla).joinedload(Tabla.documentos)
        ).get(alumno_id)

        if not alumno:
            flash("Alumno no encontrado", "error")
            return redirect(url_for("login"))

        documentos_requeridos = [
            doc for doc in alumno.tabla.documentos 
            if doc.es_requerido()
        ]

        if request.method == "POST":
            if 'password' in request.form:
                input_pwd = request.form.get("password", "")
                if not alumno.check_password(input_pwd):
                    flash("Contraseña incorrecta", "error")
                    return render_template("alumnos/login_alumno.html", alumno=alumno)

            se_subio_algo = False
            for doc_requerido in documentos_requeridos:
                archivo = request.files.get(doc_requerido.nombre)
                if archivo and archivo.filename:
                    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                    filename = f"{alumno.id}_{doc_requerido.nombre}_{timestamp}{os.path.splitext(archivo.filename)[1]}"
                    filename = secure_filename(filename)

                    # 🧱 Estructura: /uploads/<tabla_id>/<alumno_id>/
                    directorio_alumno = os.path.join(
                        app.config['UPLOAD_FOLDER'],
                        str(alumno.tabla_id),
                        alumno.id
                    )
                    os.makedirs(directorio_alumno, exist_ok=True)

                    ruta = os.path.join(directorio_alumno, filename)

                    # 🧹 Eliminar documentos anteriores con el mismo nombre
                    anteriores = Documento.query.filter_by(
                        alumno_id=alumno.id,
                        nombre=doc_requerido.nombre
                    ).all()
                    for doc in anteriores:
                        if os.path.exists(doc.ruta):
                            os.remove(doc.ruta)
                        db.session.delete(doc)

                    archivo.save(ruta)

                    documento = Documento(
                        nombre=doc_requerido.nombre,
                        nombre_archivo=filename,
                        ruta=ruta,
                        alumno_id=alumno.id,
                        tabla_id=alumno.tabla_id,
                        estado='pendiente'
                    )
                    db.session.add(documento)
                    se_subio_algo = True

            if se_subio_algo:
                db.session.commit()
                flash("Documentos subidos correctamente", "success")
            else:
                flash("No se subió ningún archivo", "error")

            return render_template("alumnos/subir_documentos.html", 
                                alumno=alumno,
                                documentos_requeridos=documentos_requeridos)

        if 'password' not in request.form:
            return render_template("alumnos/login_alumno.html", alumno=alumno)

        return render_template("alumnos/subir_documentos.html",
                            alumno=alumno,
                            documentos_requeridos=documentos_requeridos)


    @app.route("/tablas/<int:id_tabla>/eliminar_alumno/<alumno_id>", methods=["POST"])
    def eliminar_alumno(id_tabla, alumno_id):
        if not session.get('usuario_admin'):
            flash("Acceso no autorizado", "error")
            return redirect(url_for('login'))

        tabla = Tabla.query.get(id_tabla)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for('admin_home'))

        admin = Administrador.query.filter_by(usuario=session['usuario_admin']).first()
        if not admin or (admin.id != tabla.admin_id and not admin.es_superadmin):
            flash("No tienes permisos para esta acción", "error")
            return redirect(url_for('admin_home'))

        alumno = Alumno.query.get(alumno_id)
        if not alumno:
            flash("Alumno no encontrado", "error")
            return redirect(url_for('ver_tabla', id_tabla=id_tabla))

        try:
            # 💾 Guardamos el nombre antes de borrar
            nombre_alumno = alumno.nombre

            # 🧨 Eliminar de la base de datos
            db.session.delete(alumno)
            db.session.commit()

            # 🧼 Eliminar carpeta física: /uploads/<tabla_id>/<alumno_id>/
            carpeta_alumno = os.path.join(
                app.config['UPLOAD_FOLDER'],
                str(id_tabla),
                alumno_id
            )
            if os.path.exists(carpeta_alumno):
                import shutil
                shutil.rmtree(carpeta_alumno)
                app.logger.info(f"Carpeta eliminada: {carpeta_alumno}")
            else:
                app.logger.info(f"No existe carpeta para borrar: {carpeta_alumno}")

            flash(f"Alumno {nombre_alumno} eliminado correctamente", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error al eliminar el alumno", "error")
            app.logger.error(f"Error en eliminar_alumno: {str(e)}")

        return redirect(url_for('ver_tabla', id_tabla=id_tabla))


    

    @app.route("/login_alumno", methods=["GET", "POST"])
    def login_alumno():
        # Limpiar sesiones previas
        if request.method == "GET":
            session.pop("usuario_admin", None)
            session.pop("usuario_alumno", None)

        if request.method == "POST":
            credencial = request.form.get("credencial", "").strip().lower()
            print(f"Credencial ingresada: {credencial}")  # Ver la credencial ingresada

            if not credencial:
                flash("Ingrese sus credenciales", "error")
                return redirect(url_for("login_alumno"))

            # Buscar alumno por credencial normalizada
            credencial_hash = generar_hash_credencial(credencial, "")
            print(f"Hash generado: {credencial_hash}")  # Ver el hash generado

            alumno = Alumno.query.filter_by(password_hash=credencial_hash).first()

            if alumno:
                print(f"Alumno encontrado: {alumno.id}")  # Ver si encontramos al alumno
                session['usuario_alumno'] = alumno.id  # <- ESTABLECER SESIÓN CLAVE
                session['alumno_nombre'] = f"{alumno.nombre} {alumno.apellidos}"
                flash(f"Bienvenido, {alumno.nombre}", "success")
                return redirect(url_for("subir_documentos", alumno_id=alumno.id))  # Redirige a la página de subir documentos


            flash("Credencial no válida", "error")

        return render_template("alumnos/login_alumno.html")



    # Actualizar superadmin_home() - reemplaza con:
    @app.route("/superadmin_home")
    def superadmin_home():
        if not session.get('usuario_admin'):
            return redirect(url_for('login'))
        
        admin_actual = Administrador.query.filter_by(usuario=session['usuario_admin']).first()
        if not admin_actual or not admin_actual.es_superadmin:
            flash("Acceso restringido", "error")
            return redirect(url_for('login'))

        lista_admins = Administrador.query.order_by(Administrador.usuario).all()
        return render_template("superadmin/superadmin_home.html", 
                       admin_actual=admin_actual,
                       lista_admins=lista_admins)




    @app.route("/admin_home")
    def admin_home():
        if not session.get('usuario_admin'):
            flash("Acceso no autorizado", "error")
            return redirect(url_for("login"))
        
        admin_actual = obtener_admin_actual()
        if not admin_actual:
            flash("Administrador no encontrado", "error")
            return redirect(url_for("login"))
        
        if admin_actual.es_superadmin:
            tablas = Tabla.query.all()
        else:
            tablas = Tabla.query.filter_by(admin_id=admin_actual.id).all()
        
        return render_template("admin/home.html", 
                            tablas=tablas, 
                            admin_actual=admin_actual)


    @app.route("/ver_admin_home/<admin_nombre>")
    def ver_admin_home(admin_nombre):
        # 1. Verificar autenticación y permisos
        if not session.get('usuario_admin'):
            return redirect(url_for('login'))

        admin_actual = Administrador.query.filter_by(usuario=session['usuario_admin']).first()
        
        # 2. Solo superadmin puede acceder
        if not admin_actual or not admin_actual.es_superadmin:
            flash("Acceso restringido: Se requiere superadmin", "error")
            return redirect(url_for('login'))

        # 3. Buscar admin objetivo
        admin = Administrador.query.filter_by(usuario=normalizar(admin_nombre)).first()
        if not admin:
            flash("Administrador no encontrado", "error")
            return redirect(url_for('superadmin_home'))

        # 4. Obtener tablas del admin
        tablas = Tabla.query.filter_by(admin_id=admin.id).all()

        # 5. Renderizar vista
        return render_template("admin/home.html",
                       tablas=tablas,
                       admin_actual=admin, 
                       es_vista_externa=True)


    @app.route("/descargar/<int:doc_id>")
    def descargar_documento(doc_id):

        # 1. Buscar documento por ID único
        documento = Documento.query.get_or_404(doc_id)

        # 2. Verificar archivo físico
        if not documento.ruta or not os.path.exists(documento.ruta):
            flash("El archivo no está disponible", "error")
            app.logger.error(f"Archivo faltante: {documento.ruta}")
            return redirect(url_for("login"))

        # 3. Descargar archivo con nombre original (usa el nombre + extensión del archivo subido)
        extension = os.path.splitext(documento.ruta)[1]  # Ej: .pdf, .jpg
        return send_file(
            documento.ruta,
            as_attachment=True,
            download_name=f"{documento.nombre}{extension}"
        )

        


    @app.route("/eliminar_documento/<int:doc_id>", methods=["POST"])
    def eliminar_documento(doc_id):
        documento = Documento.query.get_or_404(doc_id)

        # Comprobar que el documento pertenece a un alumno
        if not documento.alumno_id:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return "No autorizado", 403
            flash("Este documento no puede ser eliminado por alumnos", "error")
            return redirect(url_for("login_alumno"))
        
        alumno = Alumno.query.get_or_404(documento.alumno_id)

        # Verificar sesión activa del alumno correcto
        if session.get("usuario_alumno") != documento.alumno_id:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return "Permiso denegado", 403
            flash("No tienes permiso para eliminar este documento", "error")
            return redirect(url_for("login_alumno"))

        try:
            # Borrar archivo físico si existe
            if documento.ruta and os.path.exists(documento.ruta):
                os.remove(documento.ruta)
                app.logger.info(f"Archivo eliminado: {documento.ruta}")

            db.session.delete(documento)
            db.session.commit()

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return "", 204  # OK sin contenido

            flash(f"Documento '{documento.nombre}' eliminado correctamente", "success")

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error eliminando documento: {str(e)}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return "Error en el servidor", 500
            flash("Error al eliminar el documento", "error")

        return redirect(url_for("subir_documentos", alumno_id=alumno.id))

    




    @app.route("/tabla/<int:id_tabla>/añadir_documento", methods=["POST"])
    def añadir_documento(id_tabla):

        if not session.get('usuario_admin'):
            return redirect(url_for('login'))

        tabla = Tabla.query.get_or_404(id_tabla)

        nuevo_doc = request.form.get("nuevo_documento", "").strip()
        nuevo_doc = re.sub(r"[^a-zA-Z0-9_ñÑáéíóúÁÉÍÓÚ\s]", "", nuevo_doc).strip()

        if not nuevo_doc:
            flash("Nombre del documento inválido", "error")
            return redirect(url_for("ver_tabla", id_tabla=id_tabla))

        # Verificar si el documento ya existe
        existe = Documento.query.filter_by(tabla_id=tabla.id, nombre=nuevo_doc, alumno_id=None).first()
        if existe:
            flash("Ese documento ya existe", "error")
            return redirect(url_for("ver_tabla", id_tabla=id_tabla))

        # Crear el documento
        doc = Documento(
            nombre=nuevo_doc,
            tabla_id=tabla.id,
            alumno_id=None,  
            estado='requerido'
        )
        db.session.add(doc)
        db.session.commit()

        flash(f"Documento '{nuevo_doc}' añadido correctamente", "success")
        # Redirigir a la vista de la tabla para que se vea el cambio
        return redirect(url_for("ver_tabla", id_tabla=tabla.id))  # Redirige al admin a la tabla actualizada




    @app.route("/tabla/<int:id_tabla>/eliminar_documento_id/<int:doc_id>", methods=["POST"])
    def eliminar_documento_tabla_id(id_tabla, doc_id):
        if not session.get('usuario_admin'):
            return redirect(url_for('login'))

        documento = Documento.query.get_or_404(doc_id)

        if documento.tabla_id != id_tabla or documento.alumno_id is not None:
            flash("Documento inválido o no autorizado", "error")
            return redirect(url_for('admin_home'))

        admin = Administrador.query.filter_by(usuario=session['usuario_admin']).first()
        if not admin or (admin.id != documento.tabla.admin_id and not admin.es_superadmin):
            flash("No tienes permisos para esta acción", "error")
            return redirect(url_for('admin_home'))

        try:

            db.session.delete(documento)
            db.session.commit()
            flash(f"Documento '{documento.nombre}' eliminado correctamente", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error al eliminar el documento", "error")
            app.logger.error(f"Error en eliminar_documento_tabla_id: {str(e)}")

        return redirect(url_for("ver_tabla", id_tabla=id_tabla))

    @app.route("/alumno/<alumno_id>/subir_documentos", methods=["GET", "POST"])
    def subir_documentos(alumno_id):
        # Verificación robusta de sesión
        if not session.get('usuario_alumno') or str(session['usuario_alumno']) != str(alumno_id):
            flash("Acceso no autorizado", "error")
            return redirect(url_for('login_alumno'))
        
        alumno = Alumno.query.get_or_404(alumno_id)
        tabla = alumno.tabla

        # Documentos requeridos por la tabla (aún no subidos)
        documentos_requeridos = Documento.query.filter_by(
            tabla_id=tabla.id, 
            alumno_id=None
        ).all()

        # Documentos ya subidos por el alumno
        documentos_subidos = Documento.query.filter_by(
            tabla_id=tabla.id,
            alumno_id=alumno.id
        ).all()

        if request.method == "POST":
            try:
                for doc in documentos_requeridos:
                    archivo = request.files.get(f'documento_{doc.id}')
                    if archivo and archivo.filename:
                        # Nombre y ruta del nuevo archivo
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        filename = f"{alumno.id}_{doc.id}_{timestamp}_{secure_filename(archivo.filename)}"
                        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(alumno.tabla_id))
                        os.makedirs(upload_dir, exist_ok=True)
                        path = os.path.join(upload_dir, filename)

                        # Borrar si ya había uno anterior
                        doc_existente = Documento.query.filter_by(
                            tabla_id=tabla.id,
                            alumno_id=alumno.id,
                            nombre=doc.nombre
                        ).first()

                        if doc_existente:
                            if doc_existente.ruta and os.path.exists(doc_existente.ruta):
                                os.remove(doc_existente.ruta)
                            db.session.delete(doc_existente)

                        # Guardar nuevo documento
                        archivo.save(path)

                        nuevo_doc = Documento(
                            nombre=doc.nombre,
                            tabla_id=tabla.id,
                            alumno_id=alumno.id,
                            nombre_archivo=filename,
                            ruta=path,
                            estado='subido'
                        )
                        db.session.add(nuevo_doc)

                db.session.commit()
                flash("Documentos subidos correctamente", "success")

                # Recargar documentos subidos actualizados
                documentos_subidos = Documento.query.filter_by(
                    tabla_id=tabla.id,
                    alumno_id=alumno.id
                ).all()

            except Exception as e:
                db.session.rollback()
                flash(f"Error al subir documentos: {str(e)}", "error")
                app.logger.error(f"Error en subir_documentos: {str(e)}")

        # Mensaje si ya subió todos los requeridos
        documentos_subidos_nombres = [d.nombre for d in documentos_subidos]
        faltan = [d.nombre for d in documentos_requeridos if d.nombre not in documentos_subidos_nombres]

        if not faltan:
            flash("¡Ya lo tienes todo subido de momento! Pero puedes cambiarlo si lo necesitas 😊", "info")

        return render_template(
            "alumnos/subir_documentos.html",
            alumno=alumno,
            documentos_requeridos=documentos_requeridos,
            documentos_subidos=documentos_subidos
        )




        
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
