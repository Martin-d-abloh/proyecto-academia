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
    session
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


# Cargar variables de entorno
load_dotenv()
UPLOAD_FOLDER = 'uploads'
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
            usuario = request.form.get("usuario", "").lower().strip()
            contrasena = request.form.get("contrasena", "").strip()

            # Usamos SQLAlchemy para buscar al admin en la base de datos
            admin = Administrador.query.filter_by(usuario=usuario).first()

            if admin and admin.check_password(contrasena):
                session['usuario_admin'] = usuario
                flash(f"Bienvenido, {admin.nombre}", "success")

                if admin.es_superadmin:
                    return redirect(url_for("superadmin_home"))
                else:
                    return redirect(url_for("admin_home"))
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


        return render_template("tablas/ver_tabla.html", 
                            tabla=tabla,
                            documentos_requeridos=documentos_requeridos,
                            alumnos=alumnos_con_docs)  # <-- Nueva estructura

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
                # Generar un ID único en base al contenido (puedes usar uuid también)
                alumno_id = hashlib.sha256(f"{nombre}{apellidos}{id_tabla}".encode()).hexdigest()[:32]

                # Crear email temporal/falso si no estás usando uno real
                email = f"{nombre.lower()}.{apellidos.lower()}@fakemail.com"

                nuevo_alumno = Alumno(
                    id=alumno_id,
                    nombre=nombre,
                    apellidos=apellidos,
                    email=email,
                    tabla_id=id_tabla
                )

                # Contraseña: puedes personalizar esto
                nuevo_alumno.set_password(f"{nombre}{apellidos}")

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
        session.pop("usuario_admin", None)

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
        # Limpiar sesión de admin si existe (para evitar conflictos)
        if request.method == "GET" and session.get("usuario_admin"):
            session.pop("usuario_admin")
        
        if request.method == "POST":
            credencial = request.form.get("credencial", "").strip().lower()
            if not credencial:
                flash("Ingrese sus credenciales", "error")
                return redirect(url_for("login_alumno"))
            
            # Generar hash de la credencial (mismo método usado al crear alumnos)
            credencial_hash = generar_hash_credencial(credencial, "")
            
            # Buscar alumno en la base de datos
            alumno = Alumno.query.filter_by(password_hash=credencial_hash).first()
            
            if alumno:
                flash("Login exitoso", "success")
                return redirect(url_for("ver_alumno", alumno_id=alumno.id))
            
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
        documento = Documento.query.get(doc_id)
        if not documento:
            flash("Documento no encontrado", "error")
            return redirect(url_for("login"))

        # 2. Verificar archivo físico
        if not documento.ruta or not os.path.exists(documento.ruta):
            flash("El archivo no está disponible", "error")
            app.logger.error(f"Archivo faltante: {documento.ruta}")
            return redirect(url_for("login"))

        # 3. Descargar archivo con nombre original
        extension = os.path.splitext(documento.nombre_archivo)[1]
        return send_file(
            documento.ruta,
            as_attachment=True,
            download_name=f"{documento.nombre}{extension}"  # Ej: "Certificado Médico.pdf"
        )
    


    @app.route("/eliminar_documento/<int:doc_id>", methods=["POST"])
    def eliminar_documento(doc_id):
        # 1. Buscar documento por ID (más seguro que por nombre)
        documento = Documento.query.get(doc_id)
        if not documento:
            flash("Documento no encontrado", "error")
            return redirect(url_for("login_alumno"))

        # 2. Obtener alumno asociado
        alumno = Alumno.query.get(documento.alumno_id)
        if not alumno:
            flash("Alumno no encontrado", "error")
            return redirect(url_for("login_alumno"))

        try:
            # 3. Eliminar archivo físico si existe
            if documento.ruta and os.path.exists(documento.ruta):
                os.remove(documento.ruta)
                app.logger.info(f"Archivo eliminado: {documento.ruta}")

            # 4. Eliminar registro de la base de datos
            db.session.delete(documento)
            db.session.commit()

            flash(f"Documento '{documento.nombre}' eliminado correctamente", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error al eliminar el documento", "error")
            app.logger.error(f"Error eliminando documento: {str(e)}")

        # 5. Obtener documentos requeridos actualizados
        documentos_requeridos = Documento.query.filter_by(
            tabla_id=alumno.tabla_id,
            alumno_id=None
        ).all()

        # 6. Redirigir a la vista de subida
        return render_template("alumnos/subir_documentos.html",
                            alumno=alumno,
                            documentos_requeridos=documentos_requeridos)

    @app.route("/tabla/<int:id_tabla>/añadir_documento", methods=["POST"])
    def añadir_documento(id_tabla):
        # 1. Authentication and permissions
        if not session.get('usuario_admin'):
            return redirect(url_for('login'))
        
        # 2. Get table with optimized query
        tabla = Tabla.query.options(
            db.joinedload(Tabla.documentos)
        ).get_or_404(id_tabla)
        
        # 3. Verify admin permissions
        admin = Administrador.query.filter_by(usuario=session['usuario_admin']).first()
        if not admin or (admin.id != tabla.admin_id and not admin.es_superadmin):
            flash("No tienes permisos para modificar esta tabla", "error")
            return redirect(url_for('admin_home'))

        # 4. Process and validate document name
        nuevo_doc = request.form.get("nuevo_documento", "").strip()
        nuevo_doc = re.sub(r"[^a-zA-Z0-9_ñÑáéíóúÁÉÍÓÚ\s]", "", nuevo_doc).strip()
        
        if not nuevo_doc:
            flash("Nombre del documento inválido", "error")
            return redirect(url_for("ver_tabla", id_tabla=id_tabla))
            
        # 5. Check if document already exists (now using Documento model)
        if Documento.query.filter_by(
            tabla_id=id_tabla,
            nombre=nuevo_doc,
            alumno_id=None  # Only check required docs (not student uploads)
        ).first():
            flash("Este documento ya existe en la tabla", "error")
            return redirect(url_for("ver_tabla", id_tabla=id_tabla))

        try:
            # 6. Create new required document (alumno_id=None marks it as required)
            documento = Documento(
                nombre=nuevo_doc,
                tabla_id=id_tabla,
                alumno_id=None,  # This makes it a required document
                estado='requerido'  # Optional: add status for required docs
            )
            
            db.session.add(documento)
            db.session.commit()
            
            flash(f"Documento '{nuevo_doc}' añadido correctamente", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error al añadir el documento", "error")
            app.logger.error(f"Error en añadir_documento: {str(e)}")
        
        return redirect(url_for("ver_tabla", id_tabla=id_tabla))

    @app.route("/tabla/<int:id_tabla>/eliminar_documento/<string:nombre_doc>", methods=["POST"])
    def eliminar_documento_tabla(id_tabla, nombre_doc):
        # 1. Authentication check
        if not session.get('usuario_admin'):
            return redirect(url_for('login'))
        
        # 2. Get the required document (where alumno_id is NULL)
        documento = Documento.query.filter_by(
            tabla_id=id_tabla,
            nombre=nombre_doc,
            alumno_id=None  # This ensures we only get required docs
        ).first_or_404()
        
        # 3. Verify admin permissions
        admin = Administrador.query.filter_by(usuario=session['usuario_admin']).first()
        if not admin or (admin.id != documento.tabla.admin_id and not admin.es_superadmin):
            flash("No tienes permisos para esta acción", "error")
            return redirect(url_for('admin_home'))

        try:
            # 4. Delete the document and related student uploads (cascade)
            db.session.delete(documento)
            db.session.commit()
            
            flash(f"Documento '{nombre_doc}' eliminado correctamente", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error al eliminar el documento", "error")
            app.logger.error(f"Error en eliminar_documento_tabla: {str(e)}")
        
        return redirect(url_for("ver_tabla", id_tabla=id_tabla))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
