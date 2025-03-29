# Importación de dependencias principales
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os

# Modelos y gestión de almacenamiento
from models import Tabla, Alumno
from storage import guardar_tablas, cargar_tablas

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

            flash(f"Tabla '{nombre}' creada con {len(documentos)} documentos", "success")
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
    
    @app.route('/alumno/<alumno_id>', methods=['GET', 'POST'])
    def vista_subir_documentos(alumno_id):
        """Handle para subida de documentos de alumnos"""
        # Búsqueda cross-tablas del alumno
        alumno = next(
            (a for tabla in app.config['TABLAS'].values()
             for a in tabla.alumnos
             if a.id == alumno_id),
            None
        )
        if not alumno:
            flash("Alumno no encontrado", "error")
            return redirect(url_for('home'))

        if request.method == 'POST':
            # Procesamiento de archivos subidos
            for nombre_doc in alumno.documentos:
                archivo = request.files.get(nombre_doc)
                if archivo and archivo.filename:
                    # Sanitización y guardado seguro
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
    return app


if __name__ == "__main__":
    # Inicialización del servidor de desarrollo
    app = create_app()
    app.run(debug=True, port=5001)