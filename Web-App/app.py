import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/dentalcare_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS DE LA BASE DE DATOS ---

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    clave = db.Column(db.String(100), nullable=False)
    perfil = db.Column(db.String(20), nullable=False) # 'admin', 'medico', 'paciente'

class Doctor(db.Model):
    __tablename__ = 'doctores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    tratamiento = db.Column(db.String(50), nullable=False)
    # Relacionamos al doctor con su cuenta de usuario
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

class Turno(db.Model):
    __tablename__ = 'turnos'
    id = db.Column(db.Integer, primary_key=True)
    nombre_paciente = db.Column(db.String(50), nullable=False)
    apellido_paciente = db.Column(db.String(50), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    tratamiento = db.Column(db.String(50), nullable=False)
    
    # Claves foráneas: un turno pertenece a un paciente y a un doctor
    paciente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctores.id'), nullable=False)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_ingresado = request.form.get('usuario')
        clave_ingresada = request.form.get('clave')
        
        # Le pedimos a MySQL que busque si existe un usuario con ese email
        usuario_db = Usuario.query.filter_by(email=usuario_ingresado).first()
        
        # Verificamos si lo encontró y si la clave coincide
        if usuario_db and usuario_db.clave == clave_ingresada:
            session['usuario_actual'] = usuario_db.email
            session['perfil_actual'] = usuario_db.perfil
            return redirect(url_for('dashboard'))
        
        # Hardcodeamos tu admin temporalmente para que no pierdas acceso
        elif usuario_ingresado == "dentalCare" and clave_ingresada == "123456":
            session['usuario_actual'] = "dentalCare"
            session['perfil_actual'] = "admin"
            return redirect(url_for('dashboard'))
            
        else:
            flash('Usuario o contraseña incorrecta') 
            
    return render_template('login.html')

# Creamos la ruta para la pantalla principal
@app.route('/dashboard')
def dashboard():
    # Si alguien intenta entrar acá copiando el link pero no inició sesión, lo pateamos al login
    if 'usuario_actual' not in session:
        return redirect(url_for('login'))
        
    return render_template('dashboard.html', 
                           usuario=session['usuario_actual'], 
                           perfil=session['perfil_actual'])

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear() # Borra las cookies del usuario
    return redirect(url_for('login'))

@app.route('/turnos')
def ver_turnos():
    # Protegemos la ruta: si no hay sesión, al login
    if 'usuario_actual' not in session:
        return redirect(url_for('login'))
        
    usuario = session['usuario_actual']
    perfil = session['perfil_actual']
    
    # Leemos el JSON completo
    with open("usuarios.json", "r") as f:
        datos = json.load(f)
        
    turnos_data = datos.get("turnos", {})
    turnos_filtrados = []
    
    # Recorremos la cantidad total de turnos (basado en la longitud de la lista 'nombres')
    cantidad_turnos = len(turnos_data.get("nombres", []))
    
    for i in range(cantidad_turnos):
        # Armamos un diccionario temporal por cada turno
        turno = {
            "id": i + 1,
            "nombre": turnos_data["nombres"][i],
            "apellido": turnos_data["apellidos"][i],
            "socio": turnos_data["numeros_socios"][i],
            "horario": turnos_data["horarios"][i],
            "tratamiento": turnos_data["tratamientos"][i],
            "doctor": turnos_data["doctor_asignado"][i]
        }
        
        # Filtramos igual que en tu Tkinter
        if perfil == 'admin':
            turnos_filtrados.append(turno)
            
        elif perfil == 'paciente':
            pacientes = datos.get("paciente", {})
            if usuario in pacientes.get("Usuario_socio", []):
                idx_paciente = pacientes["Usuario_socio"].index(usuario)
                id_socio = pacientes["ids_socio"][idx_paciente]
                if turno["socio"] == id_socio:
                    turnos_filtrados.append(turno)
                    
        elif perfil == 'medico':
            doctores = datos.get("doctores", {})
            if usuario in doctores.get("Usuario", []):
                idx_doc = doctores["Usuario"].index(usuario)
                # Recreamos el formato exacto de tu JSON: "Nombre Apellido ( ID: X)"
                nombre_doc = f"{doctores['nombres'][idx_doc]} {doctores['apellidos'][idx_doc]} ( ID: {doctores['id'][idx_doc]})"
                if turno["doctor"] == nombre_doc:
                    turnos_filtrados.append(turno)
                    
    # Mandamos los turnos filtrados a una nueva plantilla HTML
    return render_template('turnos.html', turnos=turnos_filtrados, perfil=perfil)

@app.route('/ingresar_turno', methods=['GET', 'POST'])
def ingresar_turno():
    if 'usuario_actual' not in session:
        return redirect(url_for('login'))
        
    perfil = session['perfil_actual']
    
    # Los médicos no pueden ingresar turnos, tal como en tu lógica original
    if perfil == 'medico':
        flash('Los médicos no pueden ingresar turnos.')
        return redirect(url_for('dashboard'))

    # Abrimos el JSON para leer los doctores y para actualizar los turnos
    with open("usuarios.json", "r") as f:
        datos = json.load(f)

    # Preparamos la lista de doctores para el formulario
    doctores_data = datos.get("doctores", {})
    doctores_lista = []
    for i in range(len(doctores_data.get("id", []))):
        doc_str = f"{doctores_data['nombres'][i]} {doctores_data['apellidos'][i]} ( ID: {doctores_data['id'][i]})"
        doctores_lista.append(doc_str)

    if request.method == 'POST':
        # Capturamos lo que el usuario escribió en el HTML
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        socio = request.form.get('socio', type=int)
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        tratamiento = request.form.get('tratamiento')
        doctor_sel = request.form.get('doctor')

        # Formateamos la fecha y hora para que coincida con tu JSON
        nuevo_horario = f"{fecha} {hora}"

        # Actualizamos las listas paralelas dentro de la clave "turnos"
        turnos = datos.setdefault("turnos", {})
        turnos.setdefault("nombres", []).append(nombre)
        turnos.setdefault("apellidos", []).append(apellido)
        turnos.setdefault("numeros_socios", []).append(socio)
        turnos.setdefault("horarios", []).append(nuevo_horario)
        turnos.setdefault("tratamientos", []).append(tratamiento)
        turnos.setdefault("doctor_asignado", []).append(doctor_sel)

        # Sobreescribimos el archivo JSON con los nuevos datos
        with open("usuarios.json", "w") as f:
            json.dump(datos, f, indent=4)

        flash('¡Turno guardado con éxito!')
        return redirect(url_for('ver_turnos')) # Lo mandamos a ver la tabla

    return render_template('ingresar_turno.html', perfil=perfil, doctores=doctores_lista)


@app.route('/eliminar_turno/<int:id_turno>', methods=['POST'])
def eliminar_turno(id_turno):
    if 'usuario_actual' not in session:
        return redirect(url_for('login'))
        
    usuario = session['usuario_actual']
    perfil = session['perfil_actual']
    
    with open("usuarios.json", "r") as f:
        datos = json.load(f)
        
    turnos = datos.get("turnos", {})
    
    # En nuestra tabla HTML, el ID mostrado es el índice de la lista + 1
    idx = id_turno - 1
    
    # Validamos que el índice exista en las listas
    if idx < 0 or idx >= len(turnos.get("nombres", [])):
        flash("Error: Turno no encontrado.")
        return redirect(url_for('ver_turnos'))
        
    # Validaciones de seguridad copiadas de tu lógica original
    if perfil == 'paciente':
        pacientes = datos.get("paciente", {})
        idx_paciente = pacientes["Usuario_socio"].index(usuario)
        id_socio_paciente = pacientes["ids_socio"][idx_paciente]
        
        if turnos["numeros_socios"][idx] != id_socio_paciente:
            flash("Acceso denegado: Ese turno no te pertenece.")
            return redirect(url_for('ver_turnos'))
            
    elif perfil == 'medico':
        doctores = datos.get("doctores", {})
        idx_doc = doctores["Usuario"].index(usuario)
        nombre_mi_doc = f"{doctores['nombres'][idx_doc]} {doctores['apellidos'][idx_doc]} ( ID: {doctores['id'][idx_doc]})"
        
        if turnos["doctor_asignado"][idx] != nombre_mi_doc:
            flash("Acceso denegado: Ese turno no está asignado a usted.")
            return redirect(url_for('ver_turnos'))

    # Si todo está correcto, eliminamos el elemento de todas las listas paralelas
    turnos["nombres"].pop(idx)
    turnos["apellidos"].pop(idx)
    turnos["numeros_socios"].pop(idx)
    turnos["horarios"].pop(idx)
    turnos["tratamientos"].pop(idx)
    turnos["doctor_asignado"].pop(idx)
    
    # Sobreescribimos el JSON
    with open("usuarios.json", "w") as f:
        json.dump(datos, f, indent=4)
        
    flash("Turno eliminado con éxito.")
    return redirect(url_for('ver_turnos'))

@app.route('/agregar_doctor', methods=['GET', 'POST'])
def agregar_doctor():
    # Protección doble: tiene que estar logueado Y ser admin
    if 'usuario_actual' not in session or session.get('perfil_actual') != 'admin':
        flash("Acceso denegado: Solo los administradores pueden agregar doctores.")
        return redirect(url_for('dashboard'))

    # Los tratamientos disponibles según tu código original
    tratamientos_disponibles = ['Control', 'Arreglo de caries', 'Ortodoncia', 'Extracción']

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        clave = request.form.get('clave')
        tratamiento = request.form.get('tratamiento')

        # Autogeneramos el usuario como hacías en Tkinter
        nuevo_usuario = f"{apellido.lower()}{nombre[0].lower()}@dentalcare.com"

        with open("usuarios.json", "r") as f:
            datos = json.load(f)

        doctores = datos.setdefault("doctores", {})
        usuarios_existentes = doctores.get("Usuario", [])

        if nuevo_usuario in usuarios_existentes:
            flash(f"Error: El usuario {nuevo_usuario} ya existe.")
            return redirect(url_for('agregar_doctor'))

        # Buscamos el nuevo ID con un bucle while, igual que en tu base
        ids_existentes = doctores.get("id", [])
        nuevo_id = 1
        while nuevo_id in ids_existentes:
            nuevo_id += 1

        # Agregamos los datos a las listas paralelas
        doctores.setdefault("id", []).append(nuevo_id)
        doctores.setdefault("nombres", []).append(nombre)
        doctores.setdefault("apellidos", []).append(apellido)
        doctores.setdefault("tratamientos", []).append(tratamiento)
        doctores.setdefault("Usuario", []).append(nuevo_usuario)
        doctores.setdefault("Contraseña", []).append(clave)

        with open("usuarios.json", "w") as f:
            json.dump(datos, f, indent=4)

        flash(f"Doctor agregado exitosamente con el usuario: {nuevo_usuario}")
        return redirect(url_for('dashboard'))

    return render_template('agregar_doctor.html', tratamientos=tratamientos_disponibles)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nuevo_usuario = request.form.get('usuario')
        nueva_clave = request.form.get('clave')

        # 1. Validar que el correo no esté en uso buscando en MySQL
        usuario_existente = Usuario.query.filter_by(email=nuevo_usuario).first()
        if usuario_existente or nuevo_usuario == "dentalCare":
            flash("Error: El usuario ya existe.")
            return redirect(url_for('registro'))

        # 2. Restringir el dominio a pacientes
        if "@gmail.com" in nuevo_usuario:
            # Creamos un "objeto" Usuario con los datos del formulario
            nuevo_paciente = Usuario(email=nuevo_usuario, clave=nueva_clave, perfil='paciente')
            
            # Lo preparamos y lo guardamos en MySQL
            db.session.add(nuevo_paciente)
            db.session.commit()

            flash(f"¡Registro exitoso en la Base de Datos! Ya puedes iniciar sesión.")
            return redirect(url_for('login'))
        else:
            flash("Error: Solo se permiten correos @gmail.com para registrar pacientes.")
            return redirect(url_for('registro'))

    return render_template('registro.html')

@app.route('/doctores')
def ver_doctores():
    if 'usuario_actual' not in session or session.get('perfil_actual') != 'admin':
        flash("Acceso denegado.")
        return redirect(url_for('dashboard'))

    with open("usuarios.json", "r") as f:
        datos = json.load(f)
        
    doctores_data = datos.get("doctores", {})
    lista_doctores = []
    
    # Armamos la lista para enviarla al HTML
    for i in range(len(doctores_data.get("id", []))):
        doc = {
            "id": doctores_data["id"][i],
            "nombre": doctores_data["nombres"][i],
            "apellido": doctores_data["apellidos"][i],
            "tratamiento": doctores_data["tratamientos"][i],
            "usuario": doctores_data["Usuario"][i]
        }
        lista_doctores.append(doc)
        
    return render_template('doctores.html', doctores=lista_doctores)

@app.route('/eliminar_doctor/<int:id_doc>', methods=['POST'])
def eliminar_doctor(id_doc):
    if 'usuario_actual' not in session or session.get('perfil_actual') != 'admin':
        return redirect(url_for('dashboard'))
        
    with open("usuarios.json", "r") as f:
        datos = json.load(f)
        
    doctores = datos.get("doctores", {})
    turnos = datos.get("turnos", {})
    
    if id_doc not in doctores.get("id", []):
        flash("Error: Doctor no encontrado.")
        return redirect(url_for('ver_doctores'))
        
    # Encontramos la posición exacta del doctor a borrar en las listas
    idx_doc = doctores["id"].index(id_doc)
    tratamiento_elim = doctores["tratamientos"][idx_doc]
    
    # IMPORTANTE: Recreamos cómo figura escrito en los turnos
    nombre_doc_elim = f"{doctores['nombres'][idx_doc]} {doctores['apellidos'][idx_doc]} ( ID: {id_doc})"
    
    # 1. Buscamos si existe OTRO doctor que haga el mismo tratamiento
    otros_doctores_idx = [i for i, trat in enumerate(doctores["tratamientos"]) 
                          if trat == tratamiento_elim and doctores["id"][i] != id_doc]
                          
    # 2. Buscamos los índices de los turnos que tenía asignado el doctor despedido
    turnos_asignados_idx = [i for i, doc_asig in enumerate(turnos.get("doctor_asignado", [])) 
                            if doc_asig == nombre_doc_elim]
                            
    mensaje = f"Doctor/a {doctores['apellidos'][idx_doc]} eliminado/a exitosamente."
    
    # Si el doctor tenía turnos pendientes, entra a la lógica de rescate
    if turnos_asignados_idx:
        if otros_doctores_idx:
            # Hay reemplazo: le pasamos los turnos al primer doctor alternativo
            nuevo_idx = otros_doctores_idx[0]
            nuevo_doc_str = f"{doctores['nombres'][nuevo_idx]} {doctores['apellidos'][nuevo_idx]} ( ID: {doctores['id'][nuevo_idx]})"
            
            for i in turnos_asignados_idx:
                turnos["doctor_asignado"][i] = nuevo_doc_str
            mensaje += f" Se reasignaron {len(turnos_asignados_idx)} turno(s) automáticamente al Dr/a. {doctores['apellidos'][nuevo_idx]}."
        else:
            # No hay reemplazo: borramos los turnos afectados (de atrás hacia adelante para no romper los índices)
            for i in sorted(turnos_asignados_idx, reverse=True):
                turnos["nombres"].pop(i)
                turnos["apellidos"].pop(i)
                turnos["numeros_socios"].pop(i)
                turnos["horarios"].pop(i)
                turnos["tratamientos"].pop(i)
                turnos["doctor_asignado"].pop(i)
            mensaje += f" Se cancelaron {len(turnos_asignados_idx)} turno(s) porque no hay médicos disponibles para ese tratamiento."
            
    # Finalmente, borramos al doctor de todas las listas paralelas
    doctores["id"].pop(idx_doc)
    doctores["nombres"].pop(idx_doc)
    doctores["apellidos"].pop(idx_doc)
    doctores["tratamientos"].pop(idx_doc)
    doctores["Usuario"].pop(idx_doc)
    doctores["Contraseña"].pop(idx_doc)
    
    with open("usuarios.json", "w") as f:
        json.dump(datos, f, indent=4)
        
    flash(mensaje)
    return redirect(url_for('ver_doctores'))



if __name__ == '__main__':
    # Esto le dice a Flask que cree las tablas en MySQL si no existen
    with app.app_context():
        db.create_all()
        print("Tablas creadas en MySQL exitosamente.")
        
    app.run(debug=True, port=5000)  