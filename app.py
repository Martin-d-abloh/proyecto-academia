from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file, session
from werkzeug.utils import secure_filename
import os
import unicodedata
import hashlib
import unicodedata
import re



from models import Tabla, Alumno, Administrador
from storage import (
    guardar_tablas, cargar_tablas,
    guardar_administradores, cargar_administradores
)

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
    app.secret_key = "supersecreto"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    app.config['TABLAS'] = cargar_tablas()
    app.config['ADMINISTRADORES'] = cargar_administradores()

    if "superadmin" not in app.config['ADMINISTRADORES']:
        superadmin = Administrador("Super Admin", "superadmin", "admin123")
        app.config['ADMINISTRADORES']["superadmin"] = superadmin
        guardar_administradores(app.config['ADMINISTRADORES'])

    @app.route("/", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            usuario = request.form.get("usuario", "").lower().strip()
            contrasena = request.form.get("contrasena", "").strip()
            admin = app.config['ADMINISTRADORES'].get(usuario)

            if admin and admin.contrasena == contrasena:
                session['usuario_admin'] = usuario
                flash(f"Bienvenido, {admin.nombre}", "success")
                if usuario == "superadmin":
                    return redirect(url_for("superadmin_home"))
                else:
                    return redirect(url_for("admin_home"))
            else:
                flash("Credenciales incorrectas", "error")
        return render_template("login.html")

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
        if session.get("usuario_admin") != "superadmin":
            flash("Acceso restringido al superadministrador", "error")
            return redirect(url_for("superadmin_home"))

        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            usuario = request.form.get("usuario", "").strip()
            contrasena = request.form.get("contrasena", "").strip()

            if not nombre or not usuario or not contrasena:
                flash("Todos los campos son obligatorios", "error")
                return redirect(url_for("crear_admin"))

            usuario = normalizar(usuario)

            if usuario in app.config['ADMINISTRADORES']:
                flash("Ya existe un administrador con ese usuario", "error")
                return redirect(url_for("crear_admin"))

            nuevo_admin = Administrador(nombre, usuario, contrasena)
            app.config['ADMINISTRADORES'][usuario] = nuevo_admin
            guardar_administradores(app.config['ADMINISTRADORES'])

            flash(f"Administrador '{nombre}' creado correctamente", "success")
            return redirect(url_for("superadmin_home"))

        return render_template("superadmin/crear_admin.html")

    @app.route("/eliminar_admin/<usuario>", methods=["POST"])
    def eliminar_admin(usuario):
        if session.get("usuario_admin") != "superadmin":
            flash("Acceso no autorizado", "error")
            return redirect(url_for("login"))

        usuario = normalizar(usuario)

        if usuario in app.config['ADMINISTRADORES']:
            tablas_a_eliminar = [
                id_tabla for id_tabla, tabla in app.config['TABLAS'].items()
                if hasattr(tabla, 'creador') and tabla.creador == usuario
            ]

            for id_tabla in tablas_a_eliminar:
                del app.config['TABLAS'][id_tabla]
            guardar_tablas(app.config['TABLAS'])

            del app.config['ADMINISTRADORES'][usuario]
            guardar_administradores(app.config['ADMINISTRADORES'])

            flash("Administrador y sus datos asociados eliminados", "success")
        else:
            flash("Administrador no encontrado", "error")

        return redirect(url_for("superadmin_home"))

    @app.route("/crear_tabla", methods=["GET", "POST"])
    def crear_tabla():
        if not session.get("usuario_admin"):
            flash("Por favor, inicia sesión primero.", "error")
            return redirect(url_for("login"))

        usuario_actual = session['usuario_admin']
        admin = app.config['ADMINISTRADORES'].get(usuario_actual)

        if request.method == "POST":
            nombre_tabla = request.form.get("nombre_tabla").strip()
            num_docs = int(request.form.get("num_documentos"))
            documentos = [request.form.get(f"documento_{i}") for i in range(1, num_docs + 1)]

            if not nombre_tabla or not documentos:
                flash("Faltan datos para crear la tabla.", "error")
                return redirect(url_for("crear_tabla"))

            nueva_tabla = Tabla(nombre=nombre_tabla, num_documentos=num_docs, creador=usuario_actual)
            nueva_tabla.documentos = documentos

            admin.agregar_tabla(nueva_tabla.id)
            app.config['TABLAS'][nueva_tabla.id] = nueva_tabla

            guardar_tablas(app.config['TABLAS'])
            guardar_administradores(app.config['ADMINISTRADORES'])

            flash(f"Tabla '{nueva_tabla.nombre}' creada y asignada a {admin.nombre}", "success")
            return redirect(url_for("admin_home"))

        return render_template("tablas/crear_tabla.html")

    @app.route("/tablas/<id_tabla>")
    def ver_tabla(id_tabla):
        tabla = app.config['TABLAS'].get(id_tabla)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for("admin_home"))
        return render_template("tablas/ver_tabla.html", tabla=tabla)

    @app.route("/eliminar_tabla/<id_tabla>", methods=["POST"])
    def eliminar_tabla(id_tabla):
        if id_tabla in app.config['TABLAS']:
            del app.config['TABLAS'][id_tabla]
            guardar_tablas(app.config['TABLAS'])
            flash("Tabla eliminada correctamente", "success")
        else:
            flash("Tabla no encontrada", "error")
        return redirect(url_for("admin_home"))

    @app.route("/tablas/<id_tabla>/crear_alumno", methods=["GET", "POST"])
    def crear_alumno(id_tabla):
        tabla = app.config['TABLAS'].get(id_tabla)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for("admin_home"))

        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            apellidos = request.form.get("apellidos", "").strip()

            if not nombre:
                flash("El nombre es obligatorio", "error")
                return redirect(url_for("crear_alumno", id_tabla=id_tabla))

            # Crear el alumno normalmente
            nuevo_alumno = tabla.crear_alumno(nombre, apellidos)

            # Asignar la contraseña hasheada
            nuevo_alumno.password = generar_hash_credencial(nombre, apellidos)

            guardar_tablas(app.config['TABLAS'])
            flash(f"Alumno {nombre} {apellidos} creado en {tabla.nombre}", "success")
            return redirect(url_for("ver_tabla", id_tabla=id_tabla))

        return render_template("alumnos/crear_alumno.html", tabla=tabla)


    @app.route("/alumno/<alumno_id>", methods=["GET", "POST"])
    def ver_alumno(alumno_id):
        session.pop("usuario_admin", None)  # Limpia la sesión de administrador

        for tabla in app.config['TABLAS'].values():
            for alumno in tabla.alumnos:
                if alumno.id == alumno_id:
                    if request.method == "POST" and 'password' in request.form:
                        input_pwd = request.form.get("password", "")
                        hash_input = generar_hash_credencial(alumno.nombre, alumno.apellidos)
                        if input_pwd and hashlib.sha256(input_pwd.encode()).hexdigest() == hash_input:
                            return render_template("alumnos/subir_documentos.html", alumno=alumno)
                        else:
                            flash("Contraseña incorrecta", "error")
                            return render_template("alumnos/login_alumno.html", alumno=alumno)

                    if request.method == "POST":
                        se_subio_algo = False
                        for nombre_doc in alumno.documentos:
                            archivo = request.files.get(nombre_doc)
                            if archivo and archivo.filename:
                                filename = secure_filename(archivo.filename)
                                ruta = os.path.join(app.config['UPLOAD_FOLDER'], alumno.id)
                                os.makedirs(ruta, exist_ok=True)
                                archivo.save(os.path.join(ruta, filename))
                                ruta_relativa = os.path.join(ruta, filename)
                                alumno.subir_documento(nombre_doc, ruta_relativa)
                                se_subio_algo = True

                        if se_subio_algo:
                            guardar_tablas(app.config['TABLAS'])
                            flash("Documentos subidos correctamente", "success")
                        else:
                            flash("No se subió ningún archivo", "error")

                        return render_template("alumnos/subir_documentos.html", alumno=alumno)

                    return render_template("alumnos/login_alumno.html", alumno=alumno)

        flash("Alumno no encontrado", "error")
        return redirect(url_for("login"))





    @app.route("/tablas/<id_tabla>/eliminar_alumno/<alumno_id>", methods=["POST"])
    def eliminar_alumno(id_tabla, alumno_id):
        tabla = app.config['TABLAS'].get(id_tabla)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for("admin_home"))

        tabla.alumnos = [a for a in tabla.alumnos if a.id != alumno_id]
        guardar_tablas(app.config['TABLAS'])

        flash("Alumno eliminado correctamente", "success")
        return redirect(url_for("ver_tabla", id_tabla=id_tabla))
    
    @app.route("/login_alumno", methods=["GET", "POST"])
    def login_alumno():
        session.pop("usuario_admin", None)  # Limpiar sesión del admin SIEMPRE

        if request.method == "POST":
            credencial = request.form.get("credencial", "").strip().lower()
            credencial = normalizar(credencial)

            for tabla in app.config['TABLAS'].values():
                for alumno in tabla.alumnos:
                    credencial_alumno = normalizar(alumno.nombre + alumno.apellidos)
                    if credencial == credencial_alumno:
                        flash("Login exitoso", "success")
                        return redirect(url_for("ver_alumno", alumno_id=alumno.id))
            
            flash("Credencial no válida", "error")
            return redirect(url_for("login_alumno"))

        return render_template("alumnos/login_alumno.html")



    @app.route("/superadmin_home")
    def superadmin_home():
        if session.get("usuario_admin") != "superadmin":
            flash("Acceso restringido al superadministrador", "error")
            return redirect(url_for("login"))

        admins = list(app.config['ADMINISTRADORES'].values())
        return render_template("superadmin/superadmin_home.html", lista_admins=admins)

    @app.route("/admin_home")
    def admin_home():
        usuario = session.get('usuario_admin')
        if not usuario:
            flash("Acceso no autorizado", "error")
            return redirect(url_for("login"))

        admin = app.config['ADMINISTRADORES'].get(usuario)
        if not admin:
            flash("Administrador no encontrado", "error")
            return redirect(url_for("login"))

        tablas = [app.config['TABLAS'][tid] for tid in admin.tablas if tid in app.config['TABLAS']]
        return render_template("admin/home.html", tablas=tablas, admin=admin)

    @app.route("/ver_admin_home/<admin_nombre>")
    def ver_admin_home(admin_nombre):
        if session.get("usuario_admin") != "superadmin":
            flash("Acceso restringido", "error")
            return redirect(url_for("login"))

        admin = app.config['ADMINISTRADORES'].get(normalizar(admin_nombre))
        if not admin:
            flash("Administrador no encontrado", "error")
            return redirect(url_for("superadmin_home"))

        session['usuario_admin'] = admin.usuario
        flash(f"Bienvenido, {admin.nombre}", "success")

        tablas = [
            tabla for tabla in app.config['TABLAS'].values()
            if hasattr(tabla, 'creador') and tabla.creador == admin.usuario
        ]
        admin.tablas = [tabla.id for tabla in tablas]

        return render_template("admin/home.html", tablas=tablas, admin=admin)

    @app.route("/descargar/<alumno_id>/<documento>")
    def descargar_documento(alumno_id, documento):
        for tabla in app.config['TABLAS'].values():
            for alumno in tabla.alumnos:
                if alumno.id == alumno_id:
                    if documento in alumno.documentos:
                        ruta = alumno.documentos[documento]["ruta"]
                        if ruta and os.path.exists(ruta):
                            print(f"Enviando archivo desde: {ruta}")
                            return send_file(ruta, as_attachment=True)

        flash("Documento no encontrado", "error")
        return redirect(url_for("login"))
    
    @app.route("/eliminar_documento/<alumno_id>/<documento>", methods=["POST"])
    def eliminar_documento(alumno_id, documento):
        for tabla in app.config['TABLAS'].values():
            for alumno in tabla.alumnos:
                if alumno.id == alumno_id:
                    doc_info = alumno.documentos.get(documento)
                    if doc_info and doc_info["ruta"]:
                        ruta = doc_info["ruta"]
                        if os.path.exists(ruta):
                            os.remove(ruta)
                        alumno.eliminar_documento(documento)  # ✅ Cambia estado a False y elimina ruta
                        guardar_tablas(app.config['TABLAS'])
                        flash(f"Documento '{documento}' eliminado", "success")
                    else:
                        flash("Documento no encontrado o no subido", "error")

                    # ⚠️ IMPORTANTE: siempre renderiza la vista del alumno
                    return render_template("alumnos/subir_documentos.html", alumno=alumno)

        # Si no se encuentra el alumno
        flash("Alumno no encontrado", "error")
        return redirect(url_for("login_alumno"))


    @app.route("/tabla/<id_tabla>/añadir_documento", methods=["POST"])
    def añadir_documento(id_tabla):
        tabla = app.config['TABLAS'].get(id_tabla)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for("admin_home"))
        nuevo_doc = request.form.get("nuevo_documento", "").strip()
        nuevo_doc = re.sub(r"[^a-zA-Z0-9_ñÑáéíóúÁÉÍÓÚ\s]", "", nuevo_doc).strip()
        if not nuevo_doc:
            flash("Nombre del documento vacío o inválido", "error")
            return redirect(url_for("ver_tabla", id_tabla=id_tabla))
        if nuevo_doc in tabla.documentos:
            flash("Ese documento ya existe en esta tabla", "error")
            return redirect(url_for("ver_tabla", id_tabla=id_tabla))
        tabla.documentos.append(nuevo_doc)
        for alumno in tabla.alumnos:
            if nuevo_doc not in alumno._documentos:
                alumno._documentos[nuevo_doc] = {"estado": False, "ruta": None}
        guardar_tablas(app.config['TABLAS'])
        flash(f"Documento '{nuevo_doc}' añadido a la tabla", "success")
        return redirect(url_for("ver_tabla", id_tabla=id_tabla))

    @app.route("/tabla/<id_tabla>/eliminar_documento/<documento>", methods=["POST"])
    def eliminar_documento_tabla(id_tabla, documento):
        tabla = app.config['TABLAS'].get(id_tabla)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for("admin_home"))

        if documento not in tabla.documentos:
            flash("Documento no encontrado en la tabla", "error")
            return redirect(url_for("ver_tabla", id_tabla=id_tabla))

        # Eliminar documento del listado general de la tabla
        tabla.documentos.remove(documento)

        # Eliminar documento de cada alumno y borrar archivo si existe
        for alumno in tabla.alumnos:
            if documento in alumno.documentos:
                doc_info = alumno.documentos[documento]
                if doc_info.get("ruta") and os.path.exists(doc_info["ruta"]):
                    try:
                        os.remove(doc_info["ruta"])
                    except Exception as e:
                        print(f"[ERROR] No se pudo eliminar el archivo: {e}")
                del alumno.documentos[documento]

        guardar_tablas(app.config['TABLAS'])
        flash(f"Documento '{documento}' eliminado correctamente", "success")
        return redirect(url_for("ver_tabla", id_tabla=id_tabla))




    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
