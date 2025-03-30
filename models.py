# -*- coding: utf-8 -*-
"""
Módulo optimizado para gestión de tablas y alumnos con documentos académicos.
"""

from uuid import uuid4
from typing import List, Dict, Optional

#-------------------------------------------------------------------------------
# CLASE TABLA 
#-------------------------------------------------------------------------------

class Tabla:
    """
    Gestiona grupos de alumnos y sus documentos requeridos.

    Optimizaciones clave:
    - Añadido campo 'creador' para asociar la tabla a un administrador
    - Validación de nombre en constructor
    - Mejor gestión de memoria con __slots__
    """
    __slots__ = ('nombre', 'id', 'documentos', 'alumnos', 'creador')

    def __init__(self, nombre: str, num_documentos: int = 0, documentos: Optional[List[str]] = None, creador: str = "") -> None:
        if not nombre.strip():
            raise ValueError("El nombre de la tabla no puede estar vacío")

        self.nombre = nombre.strip()
        self.id = uuid4().hex
        self.documentos = documentos if documentos else [f"Documento {i+1}" for i in range(max(num_documentos, 0))]
        self.alumnos: List['Alumno'] = []
        self.creador = creador

    def crear_alumno(self, nombre: str, apellidos: str) -> 'Alumno':
        """Crea alumno asegurando datos válidos y documentos únicos."""
        nombre = nombre.strip()
        apellidos = apellidos.strip()

        if not nombre:
            raise ValueError("Nombre del alumno requerido")

        nuevo_alumno = Alumno(
            nombre=nombre,
            apellidos=apellidos,
            documentos=list(dict.fromkeys(self.documentos))
        )

        self.alumnos.append(nuevo_alumno)
        return nuevo_alumno

    def __repr__(self) -> str:
        return f"<Tabla {self.nombre} | Docs: {len(self.documentos)} | Alumnos: {len(self.alumnos)}>"

#-------------------------------------------------------------------------------
# CLASE ALUMNO 
#-------------------------------------------------------------------------------

class Alumno:
    
    __slots__ = ('_id', 'nombre', 'apellidos', '_documentos', '_estado_general')

    def __init__(self, nombre: str, apellidos: str, documentos: List[str]):
        self.nombre = nombre.strip()
        self.apellidos = apellidos.strip()
        self._id = uuid4().hex
        self._documentos = {doc: {'estado': False, 'ruta': None} for doc in documentos}
        self._estado_general = False

    @property
    def id(self) -> str:
        return self._id

    @property
    def link(self) -> str:
        return f"/alumno/{self._id}"

    @property
    def todo_bien(self) -> bool:
        return all(doc['estado'] for doc in self._documentos.values())


    def subir_documento(self, nombre_doc: str, ruta: str) -> bool:
        if nombre_doc in self._documentos:
            self._documentos[nombre_doc] = {'estado': True, 'ruta': ruta}
            self._estado_general = False
            return True
        return False

    @property
    def documentos(self) -> Dict[str, Dict]:
        return self._documentos.copy()

    def __repr__(self) -> str:
        estado = 'OK' if self.todo_bien else 'Pendiente'
        return f"<Alumno {self.nombre} | Docs: {self._documentos.keys()} | {estado}>"

    def eliminar_documento(self, nombre_doc: str) -> bool:
        if nombre_doc in self._documentos:
            self._documentos[nombre_doc]["estado"] = False
            self._documentos[nombre_doc]["ruta"] = None
            self._estado_general = False  # Forzar recalculado
            return True
        return False
    
    def eliminar_documento(self, nombre_doc: str) -> bool:
        if nombre_doc in self._documentos:
            self._documentos[nombre_doc]["estado"] = False
            self._documentos[nombre_doc]["ruta"] = None
            self._estado_general = False  # ⚠️ Invalida la caché
            return True
        return False



#-------------------------------------------------------------------------------
# CLASE ADMINISTRADOR 
# -------------------------------------------------------------------------------

class Administrador:
    def __init__(self, nombre, usuario, contrasena):
        self.nombre = nombre
        self.usuario = usuario
        self.contrasena = contrasena
        self.tablas = []  # Aquí se guardan los IDs de las tablas

    def crear_tabla(self, nombre_tabla, documentos):
        nueva_tabla = Tabla(nombre=nombre_tabla, documentos=documentos, creador=self.usuario)
        self.tablas.append(nueva_tabla.id)  # Guardamos el ID, no la instancia completa
        return nueva_tabla

    def agregar_tabla(self, id_tabla):
        """Asigna una tabla al administrador (por ID)."""
        self.tablas.append(id_tabla)


#-------------------------------------------------------------------------------
# CLASE SuperAdmin
# -------------------------------------------------------------------------------

class SuperAdmin(Administrador):
    def __init__(self, nombre, usuario, contrasena):
        super().__init__(nombre, usuario, contrasena)
        self.is_superadmin = True
