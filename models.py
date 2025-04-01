from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from werkzeug.utils import secure_filename
import uuid
import hashlib
import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

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
        raise AttributeError("La contraseña no se puede leer directamente")  # <- esta línea estaba mal indentada

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Tabla(db.Model):
    """Hoja de cálculo con requisitos (columnas) y alumnos (filas)"""
    __tablename__ = 'tablas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('administradores.id'), nullable=False)
    
    # Componentes de la tabla
    alumnos = db.relationship('Alumno', backref='tabla', cascade='all, delete-orphan')
    documentos = db.relationship("Documento", backref="tabla", cascade="all, delete-orphan")



class Alumno(db.Model):
    """Usuario que sube documentos para cumplir requisitos (fila en la tabla)"""
    __tablename__ = 'alumnos'
    
    id = db.Column(db.String(32), primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False) 
    apellidos = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    tabla_id = db.Column(db.Integer, db.ForeignKey('tablas.id'), nullable=False)
    
    # Documentos subidos por este alumno
    documentos = db.relationship('Documento', backref='alumno', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    
    def check_password(self, password):
        """Verifica si la contraseña introducida es correcta."""
        return check_password_hash(self.password_hash, password)


class Documento(db.Model):
    """Modelo unificado para TODOS los documentos: requeridos y subidos por alumnos"""
    __tablename__ = 'documentos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Metadatos comunes
    nombre = db.Column(db.String(255), nullable=False)  # Ej: "Certificado médico"
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Para documentos subidos por alumnos:
    nombre_archivo = db.Column(db.String(255), unique=True)  # Ej: "alumno1_certificado.pdf"
    ruta = db.Column(db.String(512))  # Ruta física en el servidor
    estado = db.Column(db.String(20), default='pendiente')  # pendiente/aceptado/rechazado
    
    # Relaciones
    tabla_id = db.Column(db.Integer, db.ForeignKey('tablas.id'), nullable=False)  # A qué tabla pertenece
    alumno_id = db.Column(db.Integer, db.ForeignKey('alumnos.id'))  # NULL si es solo un requisito
    
    # Métodos
    def es_requerido(self):
        return self.alumno_id is None