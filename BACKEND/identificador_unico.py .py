import os
from datetime import datetime
import uuid

def generar_nombre_archivo(alumno_id, doc_nombre, extension=None):
    """
    Genera un nombre de archivo único usando UUID, nombre del documento y extensión.
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:8]  # fragmento corto para evitar colisiones

    if extension and not extension.startswith('.'):
        extension = f'.{extension}'

    return f"{alumno_id}_{doc_nombre}_{uid}_{timestamp}{extension or ''}"
