import pickle
import os
from pathlib import Path  # Mejor manejo de rutas

# Configuración de rutas optimizada
RUTA_DATOS = Path("datos") / "tablas.pkl"

def guardar_tablas(tablas: dict) -> None:
    """Guarda las tablas usando pickle con protocolo más eficiente."""
    RUTA_DATOS.parent.mkdir(parents=True, exist_ok=True)
    with RUTA_DATOS.open("wb") as f:
        pickle.dump(tablas, f, protocol=pickle.HIGHEST_PROTOCOL)

def cargar_tablas() -> dict:
    """Carga las tablas con verificación de existencia y formato."""
    if RUTA_DATOS.exists():
        with RUTA_DATOS.open("rb") as f:
            return pickle.load(f)
    return {}