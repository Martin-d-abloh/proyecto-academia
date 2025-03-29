# -*- coding: utf-8 -*-
"""
Módulo optimizado para gestión de tablas y alumnos con documentos académicos.
"""

from uuid import uuid4
from typing import List, Dict, Optional

#-------------------------------------------------------------------------------
# CLASE TABLA (Optimizaciones: 1. Eliminada redundancia, 2. Validación temprana)
#-------------------------------------------------------------------------------

class Tabla:
    """
    Gestiona grupos de alumnos y sus documentos requeridos.
    
    Optimizaciones clave:
    - Eliminada redundancia en deduplicación de documentos
    - Validación de nombre en constructor
    - Mejor gestión de memoria con __slots__
    """
    __slots__ = ('nombre', 'id', 'documentos', 'alumnos')

    def __init__(self, nombre: str, num_documentos: int = 0, documentos: Optional[List[str]] = None) -> None:
        if not nombre.strip():
            raise ValueError("El nombre de la tabla no puede estar vacío")
            
        self.nombre = nombre.strip()
        self.id = uuid4().hex
        self.documentos = documentos if documentos else [f"Documento {i+1}" for i in range(max(num_documentos, 0))]
        self.alumnos: List['Alumno'] = []


    def crear_alumno(self, nombre: str, apellidos: str) -> 'Alumno':
        """Crea alumno asegurando datos válidos y documentos únicos."""
        nombre = nombre.strip()
        apellidos = apellidos.strip()
        
        if not nombre:
            raise ValueError("Nombre del alumno requerido")
        
        nuevo_alumno = Alumno(
            nombre=nombre,
            apellidos=apellidos,
            documentos=list(dict.fromkeys(self.documentos))  # Deduplicación eficiente
        )
        
        self.alumnos.append(nuevo_alumno)
        return nuevo_alumno

    def __repr__(self) -> str:
        return f"<Tabla {self.nombre} | Docs: {len(self.documentos)} | Alumnos: {len(self.alumnos)}>"

#-------------------------------------------------------------------------------
# CLASE ALUMNO (Optimizaciones: 1. Cálculos lazy, 2. Métodos vectorizados)
#-------------------------------------------------------------------------------

class Alumno:
    """
    Representa un alumno y su estado de documentación.
    
    Optimizaciones clave:
    - Caché para propiedades calculadas
    - Métodos de acceso rápido a estados
    """
    __slots__ = ('_id', 'nombre', 'apellidos', '_documentos', '_estado_general')
    
    def __init__(self, nombre: str, apellidos: str, documentos: List[str]):
        self.nombre = nombre.strip()
        self.apellidos = apellidos.strip()
        self._id = uuid4().hex
        self._documentos = {doc: {'estado': False, 'ruta': None} for doc in documentos}
        self._estado_general = False  # Cache para estado general

    @property
    def id(self) -> str:
        return self._id
    
    @property
    def link(self) -> str:
        return f"/alumno/{self._id}"

    @property
    def todo_bien(self) -> bool:
        """Estado calculado con caché para mejor performance"""
        if not self._estado_general:
            self._estado_general = all(doc['estado'] for doc in self._documentos.values())
        return self._estado_general

    def subir_documento(self, nombre_doc: str, ruta: str) -> bool:
        """Actualización eficiente con invalidación de caché"""
        if nombre_doc in self._documentos:
            self._documentos[nombre_doc] = {'estado': True, 'ruta': ruta}
            self._estado_general = False  # Invalida caché
            return True
        return False

    @property
    def documentos(self) -> Dict[str, Dict]:
        """Acceso seguro a documentos inmutables"""
        return self._documentos.copy()

    def __repr__(self) -> str:
        estado = 'OK' if self.todo_bien else 'Pendiente'
        return f"<Alumno {self.nombre} | Docs: {self._documentos.keys()} | {estado}>"