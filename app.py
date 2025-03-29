from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename
import os
import unicodedata

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

    @app.route("/logout")
    def logout():
        session.pop('usuario_admin', None)
        flash("Sesión cerrada", "info")
        return redirect(url_for("login"))

    @app.route("/crear_admin", methods=["GET", "POST"])
    def crear_admin():
        if session.get("usuario_admin") != "superadmin":
            flash("Acceso restringido al superadministrador", "error")
            return redirect(url_for("superadmin_home"))
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            usuario = request.form.get("usuario", "").lower().strip()
            contrasena = request.form.get("contrasena", "").strip()
            if not nombre or not usuario or not contrasena:
                flash("Todos los campos son obligatorios", "error")
                return redirect(url_for("crear_admin"))
            if usuario in app.config['ADMINISTRADORES']:
                flash("Ya existe un administrador con ese usuario", "error")
                return redirect(url_for("crear_admin"))
            nuevo_admin = Administrador(nombre, usuario, contrasena)
            app.config['ADMINISTRADORES'][usuario] = nuevo_admin
            guardar_administradores(app.config['ADMINISTRADORES'])
            flash(f"Administrador '{nombre}' creado correctamente", "success")
            return redirect(url_for("superadmin_home"))
        return render_template("superadmin/crear_admin.html")  # Aseguramos la ruta correcta

    @app.route("/crear_tabla", methods=["GET", "POST"])
    def crear_tabla():
        if request.method == "POST":
            nombre = request.form.get("nombre_tabla", "").strip()
            num_docs = int(request.form.get("num_documentos", 0))
            documentos = [request.form.get(f"documento_{i}", "").strip() for i in range(1, num_docs + 1) if request.form.get(f"documento_{i}", "").strip()]
            if not nombre or not documentos:
                flash("Nombre de la tabla y documentos requeridos", "error")
                return redirect(url_for("crear_tabla"))
            nueva_tabla = Tabla(nombre=nombre, num_documentos=0)
            nueva_tabla.documentos = documentos
            app.config['TABLAS'][nueva_tabla.id] = nueva_tabla
            guardar_tablas(app.config['TABLAS'])
            usuario_actual = session.get('usuario_admin')
            admin = app.config['ADMINISTRADORES'].get(usuario_actual)
            if admin:
                try:
                    admin.agregar_tabla(nueva_tabla.id)
                    flash(f"Tabla '{nombre}' creada y asignada a {admin.nombre}", "success")
                except ValueError as e:
                    flash(str(e), "error")
            else:
                flash("No se encontró un administrador activo para asignar esta tabla.", "error")
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
            nuevo_alumno = tabla.crear_alumno(nombre, apellidos)
            guardar_tablas(app.config['TABLAS'])
            flash(f"Alumno {nombre} {apellidos} creado en {tabla.nombre}", "success")
            return redirect(url_for("ver_tabla", id_tabla=id_tabla))
        return render_template("alumnos/crear_alumno.html", tabla=tabla)

    @app.route('/alumno/<alumno_id>', methods=['GET', 'POST'])
    def vista_subir_documentos(alumno_id):
        alumno = next((a for tabla in app.config['TABLAS'].values() for a in tabla.alumnos if a.id == alumno_id), None)
        if not alumno:
            flash("Alumno no encontrado", "error")
            return redirect(url_for("login"))
        if session.get(f'alumno_logeado_{alumno_id}') != True:
            if request.method == 'POST':
                contrasena_ingresada = normalizar(request.form.get("contrasena", ""))
                contrasena_correcta = normalizar(f"{alumno.nombre}{alumno.apellidos}")
                if contrasena_ingresada == contrasena_correcta:
                    session[f'alumno_logeado_{alumno_id}'] = True
                    flash("Bienvenido/a. Puedes subir tus documentos.", "success")
                    return redirect(url_for("vista_subir_documentos", alumno_id=alumno_id))
                else:
                    flash("Contraseña incorrecta", "error")
            return render_template("alumnos/login_alumno.html", alumno=alumno)
        if request.method == 'POST':
            for nombre_doc in alumno.documentos:
                archivo = request.files.get(nombre_doc)
                if archivo and archivo.filename:
                    nombre_seguro = secure_filename(archivo.filename)
                    ruta = os.path.join(app.config['UPLOAD_FOLDER'], f"{alumno.id}_{nombre_doc}_{nombre_seguro}")
                    archivo.save(ruta)
                    alumno.subir_documento(nombre_doc, ruta)
            guardar_tablas(app.config['TABLAS'])
            flash("Documentos subidos correctamente", "success")
            return redirect(url_for('vista_subir_documentos', alumno_id=alumno_id))
        return render_template("alumnos/subir_documentos.html", alumno=alumno)

    @app.route("/tablas/<id_tabla>/eliminar_alumno/<alumno_id>", methods=["POST"])
    def eliminar_alumno(id_tabla, alumno_id):
        tabla = app.config['TABLAS'].get(id_tabla)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for("admin_home"))
        alumno_encontrado = next((a for a in tabla.alumnos if a.id == alumno_id), None)
        if alumno_encontrado:
            tabla.alumnos.remove(alumno_encontrado)
            guardar_tablas(app.config['TABLAS'])
            flash("Alumno eliminado correctamente", "success")
        else:
            flash("Alumno no encontrado", "error")
        return redirect(url_for("ver_tabla", id_tabla=id_tabla))

    @app.route('/descargar/<alumno_id>/<documento>')
    def descargar_documento(alumno_id, documento):
        for tabla in app.config['TABLAS'].values():
            for alumno in tabla.alumnos:
                if alumno.id == alumno_id:
                    archivo_info = alumno.documentos.get(documento)
                    if archivo_info and archivo_info['estado'] and archivo_info['ruta']:
                        carpeta, nombre_archivo = os.path.split(archivo_info['ruta'])
                        return send_from_directory(carpeta, nombre_archivo, as_attachment=True)
        return "Archivo no encontrado o acceso no autorizado", 404

    @app.route("/superadmin_home")
    def superadmin_home():
        if session.get("usuario_admin") != "superadmin":
            flash("Acceso restringido al superadministrador", "error")
            return redirect(url_for("login"))
        admins = list(app.config['ADMINISTRADORES'].values())
        return render_template("superadmin/superadmin_home.html", lista_admins=admins)

    @app.route("/admin/<admin_nombre>")
    def ver_tablas_admin(admin_nombre):
        if session.get("usuario_admin") != "superadmin":
            flash("Acceso restringido", "error")
            return redirect(url_for("login"))
        admin = app.config['ADMINISTRADORES'].get(admin_nombre)
        if not admin:
            flash("Administrador no encontrado", "error")
            return redirect(url_for("superadmin_home"))
        tablas = [app.config['TABLAS'][tid] for tid in admin.tablas if tid in app.config['TABLAS']]
        return render_template("admin/home.html", tablas=tablas, admin=admin)

    @app.route("/admin_home")
    def admin_home():
        usuario = session.get('usuario_admin')
        if not usuario or usuario == "superadmin":
            flash("Acceso no autorizado", "error")
            return redirect(url_for("login"))
        admin = app.config['ADMINISTRADORES'].get(usuario)
        if not admin:
            flash("Administrador no encontrado", "error")
            return redirect(url_for("login"))
        tablas = [app.config['TABLAS'][tid] for tid in admin.tablas if tid in app.config['TABLAS']]
        return render_template("admin/home.html", tablas=tablas, admin=admin)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
