import unicodedata
import hashlib



def normalizar(texto):
    texto = texto.lower().replace(" ", "")
    texto = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn' or c == 'ñ')

def generar_hash_credencial(nombre: str, apellidos: str) -> str:
    completo = f"{nombre} {apellidos}".strip()
    completo_normalizado = normalizar(completo)
    return hashlib.sha256(completo_normalizado.encode()).hexdigest()