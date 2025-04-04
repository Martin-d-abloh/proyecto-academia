# 🗂️ Sistema de Gestión de Documentos para Alumnos

Este proyecto es una plataforma web diseñada para que administradores y alumnos gestionen documentos requeridos de forma segura, sencilla y visual. Cada administrador puede gestionar sus propias tablas, documentos y alumnos, mientras que los alumnos pueden subir y visualizar sus documentos requeridos.

---

## 🚀 Tecnologías utilizadas

- **Backend**: Python (Flask), SQLAlchemy, JWT, SQLite
- **Frontend**: React + Vite, TailwindCSS
- **Base de datos**: SQLite (modo desarrollo)
- **Control de versiones**: Git

---

## 🏗️ Estructura del sistema

### 👤 Roles

- **Administrador**
  - Crea y gestiona tablas con alumnos y documentos.
  - Añade o elimina documentos requeridos y alumnos.
  - Visualiza y descarga documentos subidos por los alumnos.

- **Superadministrador**
  - Accede al panel de todos los administradores.
  - Visualiza todas sus tablas y la información relacionada.

- **Alumno**
  - Accede mediante un link generado.
  - Sube y elimina sus propios documentos.
  - Ve el estado de cada documento.

---

## ⚙️ Instrucciones de uso

### 1. Backend (Flask)

```bash
cd backend/
python -m venv venv
source venv/bin/activate  # en Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run
