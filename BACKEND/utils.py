import unicodedata
import hashlib



def normalizar(texto):
    # Paso 1: Minúsculas y normalización Unicode (sin eliminar espacios)
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFD', texto)
    
    # Paso 2: Eliminar tildes pero conservar ñ y espacios
    texto_normalizado = []
    for c in texto:
        if unicodedata.category(c) == 'Mn' and c != 'ñ':  # Elimina tildes pero no ñ
            continue
        texto_normalizado.append(c)
    
    return ''.join(texto_normalizado)
def generar_hash_credencial(nombre: str, apellidos: str) -> str:
    completo = f"{nombre} {apellidos}".strip()
    completo_normalizado = normalizar(completo)
    return hashlib.sha256(completo_normalizado.encode()).hexdigest()