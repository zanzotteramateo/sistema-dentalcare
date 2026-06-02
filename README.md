# Sistema de Gestión DentalCare 🦷

Sistema integral para la gestión de turnos, pacientes y profesionales de un consultorio odontológico. 

*Nota: Este proyecto documenta mi evolución tecnológica y está estructurado en un formato de monorepo. Actualmente contiene la V1 (Arquitectura Monolítica de Escritorio) y la V2 (Aplicación Web).*

---

## 🚀 Características (V1 - Desktop)
- **Control de Acceso (RBAC):** Sistema de login con perfiles diferenciados (Admin, Médico, Paciente).
- **Gestión de Turnos:** Creación, visualización y cancelación de citas médicas con validación de reglas de negocio (horarios, disponibilidad de médicos, especialidades).
- **Gestión de Personal:** Alta y baja de profesionales médicos (Exclusivo Admin).
- **Persistencia de Datos:** Almacenamiento local mediante archivos JSON estructurados de forma relacional.
- **Interfaz Gráfica:** Desarrollada íntegramente con `Tkinter` (CustomTkinter/ttk).

### 🛠️ Tecnologías Utilizadas (V1)
- **Lenguaje:** Python 3.x
- **Librerías:** Tkinter, JSON, Datetime
- **Arquitectura:** Monolítica (Estado interno basado en clases y objetos)

---

## 🌐 Características (V2 - Web) - *[En Desarrollo]*
Migración del sistema de escritorio a un entorno web accesible mediante navegador.
- **Enrutamiento:** Manejo de rutas web y sesiones de usuario seguras.
- **Vistas Dinámicas:** Renderización de templates HTML interactivos.
- **Arquitectura Web:** Separación lógica entre el frontend renderizado y el backend en Python.

### 🛠️ Tecnologías Utilizadas (V2)
- **Backend:** Python con framework **Flask**
- **Frontend:** HTML, CSS, motor de plantillas **Jinja2**
- **Persistencia:** Archivos JSON (Transición)

---


## 💻 Cómo ejecutar los proyectos

### Para ejecutar la V1 (Desktop)
1. Clonar este repositorio.
2. Navegar a la carpeta `desktop-app`.
3. Ejecutar el script principal: `python DentalCare.py`
4. Cuentas de prueba incluidas en la base de datos mockeada:
   - **Admin:** Usuario: `dentalCare` | Clave: `123456`
   - **Paciente:** Usuario: `federico@gmail.com` | Clave: `9999`
   - **Médico:** Usuario: `gomezl@dentalcare.com` | Clave: `8888`

### Para ejecutar la V2 (Web)
1. Navegar a la carpeta `web-app`.
2. Crear y activar un entorno virtual: `python -m venv venv`
3. Instalar las dependencias: `pip install -r requirements.txt`
4. Iniciar el servidor de Flask: `flask run` (o `python app.py`)
