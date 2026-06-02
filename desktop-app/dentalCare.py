import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import traceback
from datetime import datetime

USUARIOS_JSON = "usuarios.json"
TRATAMIENTOS = ['Control', 'Arreglo de caries', 'Ortodoncia', 'Extracción']
TURNOS_MAXIMOS = 23
APERTURA = 8
CIERRE = 20

class DentalCareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema DentalCare - Login")
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        
        # Configuración de estilos modernos (ttk)
        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
            
        self.style.configure('TButton', padding=6, font=('Helvetica', 10))
        self.style.configure('TLabel', font=('Helvetica', 10))
        self.style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))

        # Estado interno de datos
        self.usuarios = {}  
        self.doctores = []  
        self.turnos = []    
        
        # Sesión actual
        self.usuario_actual = None
        self.perfil_actual = None

        self.cargar_datos()
        self.construir_ui_login()

    # --- MANEJO DE DATOS ---
    def cargar_datos(self):
        # Usuario admin por defecto
        self.usuarios["dentalCare"] = {"clave": "123456", "perfil": "admin", "id_socio": None}
        
        if os.path.exists(USUARIOS_JSON):
            try:
                with open(USUARIOS_JSON, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                
                # Protección: Si detecta la estructura vieja (diccionario de listas), no la carga
                if isinstance(datos.get("doctores", []), dict):
                    print("Estructura JSON antigua detectada. Se omitirá su carga para evitar errores.")
                    return 

                self.usuarios.update(datos.get("usuarios", {}))
                self.doctores = datos.get("doctores", [])
                self.turnos = datos.get("turnos", [])
            except Exception as e:
                print(f"Error al leer el archivo JSON: {e}")

    def guardar_datos(self):
        datos = {
            "usuarios": self.usuarios,
            "doctores": self.doctores,
            "turnos": self.turnos
        }
        with open(USUARIOS_JSON, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)

    def generar_id(self, coleccion):
        if not coleccion: return 1
        return max(item["id"] for item in coleccion) + 1

    # --- INTERFAZ DE LOGIN ---
    def construir_ui_login(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title("Sistema DentalCare - Login")
        self.root.geometry("450x300")

        main_frame = ttk.Frame(self.root, padding="40")
        main_frame.pack(expand=True, fill="both")

        ttk.Label(main_frame, text="Bienvenido a DentalCare", style='Title.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(main_frame, text="Usuario:").grid(row=1, column=0, sticky="e", padx=(0, 10), pady=5)
        self.entry_usuario = ttk.Entry(main_frame, width=30)
        self.entry_usuario.grid(row=1, column=1, pady=5)

        ttk.Label(main_frame, text="Contraseña:").grid(row=2, column=0, sticky="e", padx=(0, 10), pady=5)
        self.entry_clave = ttk.Entry(main_frame, show="*", width=30)
        self.entry_clave.grid(row=2, column=1, pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(btn_frame, text="Ingresar", command=self.verificar_login).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Registrarse", command=self.ui_registro).pack(side="right", padx=10)

    def verificar_login(self):
        try:
            usuario = self.entry_usuario.get().strip()
            clave = self.entry_clave.get().strip()

            if usuario in self.usuarios and self.usuarios[usuario]["clave"] == clave:
                self.usuario_actual = usuario
                self.perfil_actual = self.usuarios[usuario]["perfil"]
                self.construir_ui_principal()
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
        except Exception as e:
            error_trace = traceback.format_exc()
            messagebox.showerror("Error de Ejecución", f"Se produjo un error:\n\n{error_trace}")
            print(error_trace)

    def ui_registro(self):
        reg_win = tk.Toplevel(self.root)
        reg_win.title("Registro de Paciente")
        reg_win.geometry("300x250")
        reg_win.resizable(False, False)
        reg_win.grab_set()

        frame = ttk.Frame(reg_win, padding="20")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="Nuevo Correo (@gmail.com):").pack(anchor="w")
        entry_usu = ttk.Entry(frame, width=25)
        entry_usu.pack(pady=5)

        ttk.Label(frame, text="Contraseña:").pack(anchor="w")
        entry_cla = ttk.Entry(frame, show="*", width=25)
        entry_cla.pack(pady=5)

        def guardar_registro():
            nuevo_usu = entry_usu.get().strip()
            nueva_cla = entry_cla.get().strip()

            if not nuevo_usu or not nueva_cla:
                messagebox.showwarning("Error", "Complete todos los campos.")
                return
            if nuevo_usu in self.usuarios:
                messagebox.showerror("Error", "El usuario ya existe.")
                return
            if not nuevo_usu.endswith("@gmail.com"):
                messagebox.showerror("Error", "Los pacientes deben registrarse con @gmail.com")
                return

            ids_socios = [u["id_socio"] for u in self.usuarios.values() if u.get("id_socio")]
            nuevo_id_socio = max(ids_socios) + 1 if ids_socios else 1

            self.usuarios[nuevo_usu] = {"clave": nueva_cla, "perfil": "paciente", "id_socio": nuevo_id_socio}
            self.guardar_datos()
            messagebox.showinfo("Éxito", f"Registrado con éxito.\nTu número de socio es: {nuevo_id_socio}")
            reg_win.destroy()

        ttk.Button(frame, text="Registrar", command=guardar_registro).pack(pady=15)

    # --- INTERFAZ PRINCIPAL ---
    def construir_ui_principal(self):
        self.root.geometry("850x500")
        self.root.title(f"Sistema DentalCare - Panel {self.perfil_actual.capitalize()}")
        
        for widget in self.root.winfo_children():
            widget.destroy()

        self.sidebar = ttk.Frame(self.root, width=200, relief="sunken", padding=10)
        self.sidebar.pack(side="left", fill="y")
        
        self.main_area = ttk.Frame(self.root, padding=10)
        self.main_area.pack(side="right", expand=True, fill="both")

        ttk.Label(self.sidebar, text=f"Hola,\n{self.usuario_actual}", font=('Helvetica', 10, 'bold')).pack(pady=(0, 20))

        # Ahora todos (admin, medico, paciente) pueden ver estos botones
        ttk.Button(self.sidebar, text="Ingresar Turno", command=self.ui_ingresar_turno).pack(fill="x", pady=5)
        ttk.Button(self.sidebar, text="Ver Turnos", command=self.ui_ver_turnos).pack(fill="x", pady=5)
        ttk.Button(self.sidebar, text="Eliminar Turno", command=self.ui_eliminar_turno).pack(fill="x", pady=5)

        if self.perfil_actual == "admin":
            ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)
            ttk.Button(self.sidebar, text="Agregar Doctor", command=self.ui_agregar_doctor).pack(fill="x", pady=5)
            ttk.Button(self.sidebar, text="Eliminar Doctor", command=self.ui_eliminar_doctor).pack(fill="x", pady=5)
            ttk.Button(self.sidebar, text="Ver Doctores", command=self.ui_ver_doctores).pack(fill="x", pady=5)

        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', pady=10)
        ttk.Button(self.sidebar, text="Cerrar Sesión", command=self.construir_ui_login).pack(fill="x", side="bottom")

        ttk.Label(self.main_area, text="Bienvenido al Panel de Control", style='Title.TLabel').pack(pady=50)
        ttk.Label(self.main_area, text="Seleccione una opción del menú lateral.").pack()

    # --- LOGICA DE TURNOS ---
    def ui_ingresar_turno(self):
        if len(self.turnos) >= TURNOS_MAXIMOS:
            messagebox.showerror("Aviso", "La agenda está llena.")
            return

        win = tk.Toplevel(self.root)
        win.title("Nuevo Turno")
        win.geometry("400x450")
        win.grab_set()

        frame = ttk.Frame(win, padding="20")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="Nombre del Paciente:").pack(anchor="w")
        entry_nom = ttk.Entry(frame)
        entry_nom.pack(fill="x", pady=2)

        ttk.Label(frame, text="Apellido del Paciente:").pack(anchor="w")
        entry_ape = ttk.Entry(frame)
        entry_ape.pack(fill="x", pady=2)

        entry_socio = None
        # Admin y Médico necesitan ingresar el número de socio del paciente manualmente
        if self.perfil_actual in ["admin", "medico"]:
            ttk.Label(frame, text="Número de Socio:").pack(anchor="w")
            entry_socio = ttk.Entry(frame)
            entry_socio.pack(fill="x", pady=2)

        ttk.Label(frame, text="Fecha (DD-MM-AAAA):").pack(anchor="w")
        entry_fec = ttk.Entry(frame)
        entry_fec.pack(fill="x", pady=2)

        ttk.Label(frame, text="Hora (Ej: 09:00 o 14:30):").pack(anchor="w")
        entry_hor = ttk.Entry(frame)
        entry_hor.pack(fill="x", pady=2)

        ttk.Label(frame, text="Tratamiento:").pack(anchor="w")
        combo_trat = ttk.Combobox(frame, values=TRATAMIENTOS, state="readonly")
        combo_trat.pack(fill="x", pady=2)
        
        # Bloquea el tratamiento si entra el médico
        mi_doc = None
        if self.perfil_actual == "medico":
            mi_doc = next((d for d in self.doctores if d["usuario"] == self.usuario_actual), None)
            if mi_doc:
                combo_trat.set(mi_doc["tratamiento"])
                combo_trat.configure(state="disabled")

        def guardar_turno():
            if not (entry_nom.get() and entry_ape.get() and entry_fec.get() and entry_hor.get() and combo_trat.get()):
                messagebox.showerror("Error", "Todos los campos son obligatorios.")
                return

            socio_id = self.usuarios[self.usuario_actual]["id_socio"] if self.perfil_actual == "paciente" else entry_socio.get()
            try:
                socio_id = int(socio_id)
                socios_validos = [u["id_socio"] for u in self.usuarios.values() if u.get("id_socio") is not None]
                if socio_id not in socios_validos:
                    raise ValueError("Socio no registrado.")
            except ValueError:
                messagebox.showerror("Error", "Número de socio inválido o no registrado.")
                return

            try:
                fecha_hora_str = f"{entry_fec.get()} {entry_hor.get()}"
                fecha_turno = datetime.strptime(fecha_hora_str, "%d-%m-%Y %H:%M")
                
                if fecha_turno < datetime.now():
                    messagebox.showerror("Error", "No puede agendar en el pasado.")
                    return
                if not (APERTURA <= fecha_turno.hour < CIERRE):
                    messagebox.showerror("Error", f"Horario de atención: {APERTURA}:00 a {CIERRE}:00")
                    return
                if fecha_turno.minute not in [0, 30]:
                    messagebox.showerror("Error", "Los turnos se dan cada media hora (Ej: 10:00 o 10:30).")
                    return
                
                fecha_str_db = fecha_turno.strftime("%Y-%m-%d %H:%M")
                if any(t["horario"] == fecha_str_db for t in self.turnos):
                    messagebox.showerror("Error", "Ese horario ya está ocupado.")
                    return

            except ValueError:
                messagebox.showerror("Error", "Formato de fecha/hora incorrecto.")
                return

            # Asignar doctor según perfil
            if self.perfil_actual == "medico":
                doc_asignado = mi_doc
                tratamiento = mi_doc["tratamiento"]
            else:
                tratamiento = combo_trat.get()
                docs_disponibles = [d for d in self.doctores if d["tratamiento"] == tratamiento]
                
                if not docs_disponibles:
                    messagebox.showerror("Error", f"No hay doctores para {tratamiento}.")
                    return
                doc_asignado = docs_disponibles[0]

            nombre_doc = f"{doc_asignado['nombre']} {doc_asignado['apellido']} (ID: {doc_asignado['id']})"

            nuevo_turno = {
                "id": self.generar_id(self.turnos),
                "nombre": entry_nom.get().strip(),
                "apellido": entry_ape.get().strip(),
                "socio": socio_id,
                "horario": fecha_str_db,
                "tratamiento": tratamiento,
                "doctor_asignado": nombre_doc
            }

            self.turnos.append(nuevo_turno)
            self.guardar_datos()
            messagebox.showinfo("Éxito", f"Turno agendado con el Dr/a. {doc_asignado['apellido']}")
            win.destroy()
            self.ui_ver_turnos() # Refresca la tabla 

        ttk.Button(frame, text="Guardar Turno", command=guardar_turno).pack(pady=20)

    def ui_ver_turnos(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

        ttk.Label(self.main_area, text="Agenda de Turnos", style='Title.TLabel').pack(pady=(0,10))

        columnas = ("ID", "Paciente", "Socio", "Fecha y Hora", "Tratamiento", "Doctor")
        tabla = ttk.Treeview(self.main_area, columns=columnas, show="headings", height=15)
        
        anchos = [30, 120, 50, 120, 100, 150]
        for col, ancho in zip(columnas, anchos):
            tabla.heading(col, text=col)
            tabla.column(col, width=ancho, anchor="center")
        
        scrollbar = ttk.Scrollbar(self.main_area, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        tabla.pack(fill="both", expand=True)

        turnos_mostrar = []
        if self.perfil_actual == "admin":
            turnos_mostrar = self.turnos
        elif self.perfil_actual == "paciente":
            mi_socio = self.usuarios[self.usuario_actual]["id_socio"]
            turnos_mostrar = [t for t in self.turnos if t["socio"] == mi_socio]
        elif self.perfil_actual == "medico":
            mi_doc = next((d for d in self.doctores if d["usuario"] == self.usuario_actual), None)
            if mi_doc:
                str_id = f"(ID: {mi_doc['id']})"
                turnos_mostrar = [t for t in self.turnos if str_id in t["doctor_asignado"]]

        turnos_mostrar.sort(key=lambda x: datetime.strptime(x["horario"], "%Y-%m-%d %H:%M"))
        for t in turnos_mostrar:
            fecha_f = datetime.strptime(t["horario"], "%Y-%m-%d %H:%M").strftime("%d-%m-%Y %H:%M")
            tabla.insert("", "end", values=(t["id"], f"{t['apellido']} {t['nombre']}", t["socio"], fecha_f, t["tratamiento"], t["doctor_asignado"]))

    def ui_eliminar_turno(self):
        win = tk.Toplevel(self.root)
        win.title("Eliminar Turno")
        win.geometry("250x150")
        win.grab_set()

        frame = ttk.Frame(win, padding="20")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="ID del Turno a eliminar:").pack(anchor="center", pady=5)
        entry_id = ttk.Entry(frame, justify="center")
        entry_id.pack(pady=5)

        def confirmar_eliminacion():
            try:
                id_eliminar = int(entry_id.get())
            except ValueError:
                messagebox.showerror("Error", "El ID debe ser numérico.")
                return

            turno_encontrado = next((t for t in self.turnos if t["id"] == id_eliminar), None)
            
            if not turno_encontrado:
                messagebox.showerror("Error", "Turno no encontrado.")
                return

            if self.perfil_actual == "paciente":
                mi_socio = self.usuarios[self.usuario_actual]["id_socio"]
                if turno_encontrado["socio"] != mi_socio:
                    messagebox.showerror("Acceso Denegado", "Este turno no te pertenece.")
                    return
            elif self.perfil_actual == "medico":
                mi_doc = next((d for d in self.doctores if d["usuario"] == self.usuario_actual), None)
                if mi_doc and f"(ID: {mi_doc['id']})" not in turno_encontrado["doctor_asignado"]:
                    messagebox.showerror("Acceso Denegado", "No podés eliminar turnos asignados a otro médico.")
                    return

            if messagebox.askyesno("Confirmar", "¿Seguro que desea eliminar el turno?"):
                self.turnos.remove(turno_encontrado)
                self.guardar_datos()
                messagebox.showinfo("Éxito", "Turno eliminado.")
                self.ui_ver_turnos() 
                win.destroy()

        ttk.Button(frame, text="Eliminar", command=confirmar_eliminacion).pack(pady=10)

    # --- LOGICA DE DOCTORES (SOLO ADMIN) ---
    def ui_agregar_doctor(self):
        win = tk.Toplevel(self.root)
        win.title("Registrar Doctor")
        win.geometry("350x350")
        win.grab_set()

        frame = ttk.Frame(win, padding="20")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="Nombre:").pack(anchor="w")
        entry_nom = ttk.Entry(frame)
        entry_nom.pack(fill="x", pady=2)

        ttk.Label(frame, text="Apellido:").pack(anchor="w")
        entry_ape = ttk.Entry(frame)
        entry_ape.pack(fill="x", pady=2)

        ttk.Label(frame, text="Contraseña:").pack(anchor="w")
        entry_cla = ttk.Entry(frame)
        entry_cla.pack(fill="x", pady=2)

        ttk.Label(frame, text="Especialidad:").pack(anchor="w")
        combo_trat = ttk.Combobox(frame, values=TRATAMIENTOS, state="readonly")
        combo_trat.pack(fill="x", pady=2)

        def guardar_doc():
            nom = entry_nom.get().strip()
            ape = entry_ape.get().strip()
            cla = entry_cla.get().strip()
            trat = combo_trat.get()

            if not (nom and ape and cla and trat):
                messagebox.showerror("Error", "Complete todos los campos.")
                return

            email_doc = f"{ape.lower()}{nom[0].lower()}@dentalcare.com"
            if email_doc in self.usuarios:
                messagebox.showerror("Error", "El usuario del doctor ya existe.")
                return

            nuevo_doc = {
                "id": self.generar_id(self.doctores),
                "nombre": nom,
                "apellido": ape,
                "tratamiento": trat,
                "usuario": email_doc
            }

            self.usuarios[email_doc] = {"clave": cla, "perfil": "medico", "id_socio": None}
            self.doctores.append(nuevo_doc)
            self.guardar_datos()
            messagebox.showinfo("Éxito", f"Doctor registrado.\nUsuario: {email_doc}")
            win.destroy()

        ttk.Button(frame, text="Guardar Doctor", command=guardar_doc).pack(pady=20)

    def ui_eliminar_doctor(self):
        win = tk.Toplevel(self.root)
        win.title("Eliminar Doctor")
        win.geometry("250x150")
        win.grab_set()

        frame = ttk.Frame(win, padding="20")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="ID del Doctor a eliminar:").pack(anchor="center", pady=5)
        entry_id = ttk.Entry(frame, justify="center")
        entry_id.pack(pady=5)

        def confirmar_elim_doc():
            try:
                id_eliminar = int(entry_id.get())
            except ValueError:
                messagebox.showerror("Error", "El ID debe ser numérico.")
                return

            doc_encontrado = next((d for d in self.doctores if d["id"] == id_eliminar), None)
            if not doc_encontrado:
                messagebox.showerror("Error", "Doctor no encontrado.")
                return

            str_id = f"(ID: {doc_encontrado['id']})"
            turnos_afectados = [t for t in self.turnos if str_id in t["doctor_asignado"]]

            if messagebox.askyesno("Confirmar", f"Se eliminará al Dr. {doc_encontrado['apellido']}. ¿Continuar?"):
                for t in turnos_afectados:
                    self.turnos.remove(t)
                
                del self.usuarios[doc_encontrado["usuario"]]
                self.doctores.remove(doc_encontrado)
                
                self.guardar_datos()
                mensaje = "Doctor eliminado."
                if turnos_afectados:
                    mensaje += f"\nSe cancelaron {len(turnos_afectados)} turno(s) asignados a este médico."
                messagebox.showinfo("Éxito", mensaje)
                win.destroy()

        ttk.Button(frame, text="Eliminar", command=confirmar_elim_doc).pack(pady=10)

    def ui_ver_doctores(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

        ttk.Label(self.main_area, text="Plantel Médico", style='Title.TLabel').pack(pady=(0,10))

        columnas = ("ID", "Nombre y Apellido", "Especialidad", "Usuario")
        tabla = ttk.Treeview(self.main_area, columns=columnas, show="headings", height=15)
        
        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=150, anchor="center")
            
        tabla.pack(fill="both", expand=True)

        for d in self.doctores:
            tabla.insert("", "end", values=(d["id"], f"Dr/a. {d['nombre']} {d['apellido']}", d["tratamiento"], d["usuario"]))

if __name__ == "__main__":
    root = tk.Tk()
    app = DentalCareApp(root)
    root.mainloop()