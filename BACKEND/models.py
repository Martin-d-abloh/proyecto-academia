from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from sqlalchemy.dialects.postgresql import UUID, ENUM

# ENUM preexistente en PostgreSQL
estado_enum = ENUM('pendiente', 'subido', name='estado_enum', create_type=True)


class Administrador(db.Model):
    __tablename__ = 'administradores'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    es_superadmin = db.Column(db.Boolean, default=False)

    tablas = db.relationship('Tabla', backref='administrador', cascade='all, delete-orphan')

    @property
    def password(self):
        raise AttributeError("La contraseña no se puede leer directamente")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Tabla(db.Model):
    __tablename__ = 'tablas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('administradores.id'), nullable=False)

    alumnos = db.relationship('Alumno', backref='tabla', cascade='all, delete-orphan')
    documentos = db.relationship("Documento", backref="tabla", cascade="all, delete-orphan")


class Alumno(db.Model):
    __tablename__ = 'alumnos'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    apellidos = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    tabla_id = db.Column(db.Integer, db.ForeignKey('tablas.id'), nullable=False)
    credencial = db.Column(db.String(64), unique=True)

    documentos = db.relationship('Documento', backref='alumno', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Documento(db.Model):
    __tablename__ = 'documentos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    nombre_archivo = db.Column(db.String(255), unique=True)
    ruta = db.Column(db.String(512))
    estado = db.Column(estado_enum, default='pendiente')

    tabla_id = db.Column(db.Integer, db.ForeignKey('tablas.id'), nullable=False)
    alumno_id = db.Column(UUID(as_uuid=True), db.ForeignKey('alumnos.id'))

    def es_requerido(self):
        return self.alumno_id is None
