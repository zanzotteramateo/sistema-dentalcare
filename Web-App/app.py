import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Nosenada123*@localhost/dentalcare_db'
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
    if 'usuario_actual' not in session:
        return redirect(url_for('login'))
        
    usuario_email = session['usuario_actual']
    perfil = session['perfil_actual']
    usuario_actual = Usuario.query.filter_by(email=usuario_email).first()
    
    # 1. Filtramos las consultas en MySQL directamente
    if perfil == 'admin':
        turnos_db = Turno.query.all()
    elif perfil == 'paciente':
        turnos_db = Turno.query.filter_by(paciente_id=usuario_actual.id).all()
    elif perfil == 'medico':
        doctor_actual = Doctor.query.filter_by(usuario_id=usuario_actual.id).first()
        if doctor_actual:
            turnos_db = Turno.query.filter_by(doctor_id=doctor_actual.id).all()
        else:
            turnos_db = []
    
    turnos_filtrados = []
    
    # 2. Preparamos los datos para mandarlos a la vista (HTML)
    for t in turnos_db:
        # Buscamos al doctor dueño del turno
        doctor = Doctor.query.get(t.doctor_id)
        doctor_str = f"Dr/a. {doctor.nombre} {doctor.apellido}" if doctor else "Doctor Eliminado"
        
        turnos_filtrados.append({
            "id": t.id,
            "nombre": t.nombre_paciente,
            "apellido": t.apellido_paciente,
            "socio": t.paciente_id,
            "horario": t.fecha_hora.strftime("%Y-%m-%d %H:%M"),
            "tratamiento": t.tratamiento,
            "doctor": doctor_str
        })
        
    return render_template('turnos.html', turnos=turnos_filtrados, perfil=perfil)

@app.route('/ingresar_turno', methods=['GET', 'POST'])
def ingresar_turno():
    if 'usuario_actual' not in session:
        return redirect(url_for('login'))
        
    perfil = session['perfil_actual']
    usuario_email = session['usuario_actual']
    
    if perfil == 'medico':
        flash('Los médicos no pueden ingresar turnos.')
        return redirect(url_for('dashboard'))

    # 1. Traemos doctores de la base de datos para armar el selector
    doctores_db = Doctor.query.all()
    doctores_lista = [f"{d.nombre} {d.apellido} ( ID: {d.id})" for d in doctores_db]

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        socio_id = request.form.get('socio', type=int)
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        tratamiento = request.form.get('tratamiento')
        doctor_sel = request.form.get('doctor') 

        # Extraemos el ID del doctor del string "Nombre Apellido ( ID: X)"
        doctor_id_str = doctor_sel.split('ID: ')[1].replace(')', '').strip()
        doctor_id = int(doctor_id_str)

        # Seguridad: Si es un paciente logueado, forzamos que se guarde con su propio ID
        if perfil == 'paciente':
            paciente_actual = Usuario.query.filter_by(email=usuario_email).first()
            socio_id = paciente_actual.id
        else:
            # Si es admin, validamos que el número de socio exista en MySQL
            paciente_existente = Usuario.query.get(socio_id)
            if not paciente_existente or paciente_existente.perfil != 'paciente':
                flash('Error: El número de socio no existe o no pertenece a un paciente.')
                return redirect(url_for('ingresar_turno'))

        # Convertimos los textos de fecha y hora a un objeto DateTime real
        fecha_hora_str = f"{fecha} {hora}"
        fecha_hora_obj = datetime.strptime(fecha_hora_str, "%Y-%m-%d %H:%M")

        # Creamos el turno y lo vinculamos a las claves foráneas
        nuevo_turno = Turno(
            nombre_paciente=nombre,
            apellido_paciente=apellido,
            fecha_hora=fecha_hora_obj,
            tratamiento=tratamiento,
            paciente_id=socio_id,
            doctor_id=doctor_id
        )
        
        db.session.add(nuevo_turno)
        db.session.commit()

        flash('¡Turno guardado con éxito en MySQL!')
        return redirect(url_for('ver_turnos'))

    return render_template('ingresar_turno.html', perfil=perfil, doctores=doctores_lista)


@app.route('/eliminar_turno/<int:id_turno>', methods=['POST'])
def eliminar_turno(id_turno):
    if 'usuario_actual' not in session:
        return redirect(url_for('login'))
        
    usuario_email = session['usuario_actual']
    perfil = session['perfil_actual']
    
    # Buscamos el turno por su ID Principal
    turno = Turno.query.get(id_turno)
    if not turno:
        flash("Error: Turno no encontrado en la Base de Datos.")
        return redirect(url_for('ver_turnos'))
        
    usuario_actual = Usuario.query.filter_by(email=usuario_email).first()
        
    # Validaciones de seguridad para que nadie borre turnos ajenos
    if perfil == 'paciente':
        if turno.paciente_id != usuario_actual.id:
            flash("Acceso denegado: Ese turno no te pertenece.")
            return redirect(url_for('ver_turnos'))
            
    elif perfil == 'medico':
        doctor_actual = Doctor.query.filter_by(usuario_id=usuario_actual.id).first()
        if not doctor_actual or turno.doctor_id != doctor_actual.id:
            flash("Acceso denegado: Ese turno no está asignado a usted.")
            return redirect(url_for('ver_turnos'))

    # Si todo está correcto, lo eliminamos de MySQL
    db.session.delete(turno)
    db.session.commit()
        
    flash("Turno eliminado con éxito de MySQL.")
    return redirect(url_for('ver_turnos'))

@app.route('/agregar_doctor', methods=['GET', 'POST'])
def agregar_doctor():
    if 'usuario_actual' not in session or session.get('perfil_actual') != 'admin':
        flash("Acceso denegado: Solo los administradores pueden agregar doctores.")
        return redirect(url_for('dashboard'))

    tratamientos_disponibles = ['Control', 'Arreglo de caries', 'Ortodoncia', 'Extracción']

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        clave = request.form.get('clave')
        tratamiento = request.form.get('tratamiento')

        # Autogeneramos el email
        nuevo_email = f"{apellido.lower()}{nombre[0].lower()}@dentalcare.com"

        # 1. Verificamos en MySQL si el usuario ya existe
        usuario_existente = Usuario.query.filter_by(email=nuevo_email).first()
        if usuario_existente:
            flash(f"Error: El usuario {nuevo_email} ya existe.")
            return redirect(url_for('agregar_doctor'))

        # 2. Creamos la cuenta de Usuario en la BD
        nuevo_usuario = Usuario(email=nuevo_email, clave=clave, perfil='medico')
        db.session.add(nuevo_usuario)
        db.session.commit() # Hacemos commit acá para que MySQL le asigne un ID (nuevo_usuario.id)

        # 3. Creamos el perfil de Doctor vinculado a ese Usuario
        nuevo_doctor = Doctor(nombre=nombre, apellido=apellido, tratamiento=tratamiento, usuario_id=nuevo_usuario.id)
        db.session.add(nuevo_doctor)
        db.session.commit()

        flash(f"Doctor agregado exitosamente a la BD con el usuario: {nuevo_email}")
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

    # Traemos todos los doctores de la tabla de MySQL
    doctores_db = Doctor.query.all()
    
    lista_doctores = []
    
    # Armamos la lista para enviarla al HTML
    for doc in doctores_db:
        # Buscamos en la tabla de Usuarios el email que le corresponde a este doctor
        usuario_doc = Usuario.query.get(doc.usuario_id)
        
        lista_doctores.append({
            "id": doc.id,
            "nombre": doc.nombre,
            "apellido": doc.apellido,
            "tratamiento": doc.tratamiento,
            "usuario": usuario_doc.email if usuario_doc else "Desconocido"
        })
        
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