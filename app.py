# Importación de dependencias principales
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os

# Modelos y gestión de almacenamiento
from models import Tabla, Alumno, Administrador
from storage import guardar_tablas, cargar_tablas, guardar_administradores, cargar_administradores


# Configuración de archivos subidos
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}

def create_app():
    """Factory principal para crear y configurar la aplicación Flask"""
    app = Flask(__name__)
    app.secret_key = "supersecreto"  # Clave para sesiones seguras
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['TABLAS'] = cargar_tablas()  # Cargar datos persistentes

    # Asegurar directorio de uploads
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # --------------------------
    # Rutas principales
    # --------------------------
    
    @app.route("/")
    def home():
        """Endpoint principal: Muestra listado de todas las tablas"""
        return render_template("home.html", tablas=app.config['TABLAS'])

    @app.route("/crear_tabla", methods=["GET", "POST"])
    def crear_tabla():
        """Handle para creación de nuevas tablas con documentos requeridos"""
        if request.method == "POST":
            # Procesamiento de formulario de creación
            nombre = request.form.get("nombre_tabla", "").strip()
            num_docs = int(request.form.get("num_documentos", 0))

            # Recoger nombres de documentos personalizados
            documentos = []
            for i in range(1, num_docs + 1):
                doc = request.form.get(f"documento_{i}", "").strip()
                if doc:
                    documentos.append(doc)

            # Validación de datos requeridos
            if not nombre or not documentos:
                flash("Nombre de la tabla y documentos requeridos", "error")
                return redirect(url_for("crear_tabla"))

            # Creación y almacenamiento de nueva tabla
            nueva_tabla = Tabla(nombre=nombre, num_documentos=0)
            nueva_tabla.documentos = documentos
            app.config['TABLAS'][nueva_tabla.id] = nueva_tabla
            guardar_tablas(app.config['TABLAS'])

            # Buscar administrador logeado
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

            return redirect(url_for("home"))

        return render_template("tablas/crear_tabla.html")


    @app.route("/tablas/<id>")
    def ver_tabla(id):
        """Muestra detalle de una tabla específica con sus alumnos"""
        tabla = app.config['TABLAS'].get(id)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for("home"))
        return render_template("tablas/ver_tabla.html", tabla=tabla)

    @app.route("/tablas/<id>/eliminar", methods=["POST"])
    def eliminar_tabla(id):
        """Elimina una tabla y persiste los cambios"""
        if id in app.config['TABLAS']:
            del app.config['TABLAS'][id]
            guardar_tablas(app.config['TABLAS'])
            flash("Tabla eliminada correctamente", "success")
        else:
            flash("Tabla no encontrada", "error")
        return redirect(url_for("home"))

    # --------------------------
    # Gestión de alumnos
    # --------------------------
    
    @app.route("/tablas/<id_tabla>/crear_alumno", methods=["GET", "POST"])
    def crear_alumno(id_tabla):
        """Crea nuevos alumnos dentro de una tabla específica"""
        tabla = app.config['TABLAS'].get(id_tabla)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for("home"))

        if request.method == "POST":
            # Validación de datos del alumno
            nombre = request.form.get("nombre", "").strip()
            apellidos = request.form.get("apellidos", "").strip()

            if not nombre:
                flash("El nombre es obligatorio", "error")
                return redirect(url_for("crear_alumno", id_tabla=id_tabla))

            # Creación y persistencia del alumno
            nuevo_alumno = tabla.crear_alumno(nombre, apellidos)
            guardar_tablas(app.config['TABLAS'])

            flash(f"Alumno {nombre} {apellidos} creado en {tabla.nombre}", "success")
            return redirect(url_for("ver_tabla", id=id_tabla))

        return render_template("alumnos/crear_alumno.html", tabla=tabla)

    @app.route("/tablas/<id_tabla>/alumnos/<alumno_id>/eliminar", methods=["POST"])
    def eliminar_alumno(id_tabla, alumno_id):
        """Elimina un alumno de una tabla específica"""
        tabla = app.config['TABLAS'].get(id_tabla)
        if not tabla:
            flash("Tabla no encontrada", "error")
            return redirect(url_for("home"))

        # Búsqueda del alumno por ID
        alumno = next((a for a in tabla.alumnos if a.id == alumno_id), None)
        if not alumno:
            flash("Alumno no encontrado", "error")
            return redirect(url_for("ver_tabla", id=id_tabla))

        # Eliminación y persistencia
        tabla.alumnos.remove(alumno)
        guardar_tablas(app.config['TABLAS'])

        flash(f"Alumno '{alumno.nombre} {alumno.apellidos}' eliminado correctamente", "success")
        return redirect(url_for("ver_tabla", id=id_tabla))

    # --------------------------
    # Gestión de documentos
    # --------------------------
    
    import unicodedata

    def normalizar(texto):
        texto = texto.lower().replace(" ", "")
        texto = unicodedata.normalize('NFD', texto)
        return ''.join(c for c in texto if unicodedata.category(c) != 'Mn' or c == 'ñ')

    @app.route('/alumno/<alumno_id>', methods=['GET', 'POST'])
    def vista_subir_documentos(alumno_id):
        """Login de alumno + subida de documentos"""
        alumno = next(
            (a for tabla in app.config['TABLAS'].values()
            for a in tabla.alumnos
            if a.id == alumno_id),
            None
        )
        if not alumno:
            flash("Alumno no encontrado", "error")
            return redirect(url_for("home"))

        # LOGIN de alumno
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

        # SUBIDA de documentos
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

    @app.route('/descargar/<alumno_id>/<documento>')
    def descargar_documento(alumno_id, documento):
        # Obtener la tabla activa desde app.config
        for tabla in app.config['TABLAS'].values():
            for alumno in tabla.alumnos:
                if alumno.id == alumno_id:
                    archivo_info = alumno.documentos.get(documento)
                    if archivo_info and archivo_info['estado'] and archivo_info['ruta']:
                        ruta_archivo = archivo_info['ruta']
                        carpeta, nombre_archivo = os.path.split(ruta_archivo)
                        return send_from_directory(carpeta, nombre_archivo, as_attachment=True)

        return "Archivo no encontrado o acceso no autorizado", 404
    
    # --------------------------
    # Gestión de administradores
    # --------------------------    

    from flask import session

    @app.route("/login_admin", methods=["GET", "POST"])
    def login_admin():
        """Permite a los administradores ingresar con sus credenciales"""
        if request.method == "POST":
            usuario = request.form.get("usuario", "").lower().strip()
            contrasena = request.form.get("contrasena", "").strip()

            admin = app.config['ADMINISTRADORES'].get(usuario)

            if admin and admin.contrasena == contrasena:
                session['usuario_admin'] = usuario
                flash(f"Bienvenido, {admin.nombre}", "success")
                return redirect(url_for("home"))
            else:
                flash("Credenciales incorrectas", "error")
                return redirect(url_for("login_admin"))

        return render_template("admin/login_admin.html")
    
    @app.route("/logout")
    def logout():
        session.pop('usuario_admin', None)
        flash("Sesión cerrada", "info")
        return redirect(url_for("login_admin"))
    
    @app.route("/crear_admin", methods=["GET", "POST"])
    def crear_admin():
        """Permite al superadmin crear nuevos administradores"""
        if session.get("usuario_admin") != "superadmin":
            flash("Acceso restringido al superadministrador", "error")
            return redirect(url_for("home"))

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

            # Guardar administradores en disco
            guardar_administradores(app.config['ADMINISTRADORES'])

            flash(f"Administrador '{nombre}' creado correctamente", "success")
            return redirect(url_for("home"))

        return render_template("admin/crear_admin.html")



    return app



if __name__ == "__main__":
    # Inicialización del servidor de desarrollo
    app = create_app()
    app.run(debug=True, port=5001)