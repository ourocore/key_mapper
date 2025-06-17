import random
from pynput import mouse, keyboard
import tkinter as tk
from tkinter import ttk, messagebox

class KeyMapperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Key Mapper")

        self.opciones = [str(i) for i in range(1, 10)]
        self.probabilidades = {opcion: 0 for opcion in self.opciones}
        self.selected_keys = []
        self.standby = False

        self.create_widgets()
        self.setup_listeners()

    def create_widgets(self):
        # Frame para la selección de teclas
        key_selection_frame = ttk.LabelFrame(self.root, text="Selección de Teclas")
        key_selection_frame.pack(padx=10, pady=10, fill="x")

        self.key_vars = {}
        for i, opcion in enumerate(self.opciones):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(key_selection_frame, text=opcion, variable=var, command=self.update_key_selection)
            chk.grid(row=0, column=i, padx=5, pady=5) # Using grid here is fine as it's within key_selection_frame
            self.key_vars[opcion] = var

        # Frame para la asignación de porcentajes
        self.percentage_frame = ttk.LabelFrame(self.root, text="Asignación de Porcentajes")
        self.percentage_frame.pack(padx=10, pady=10, fill="x")

        # **CHANGE STARTS HERE**
        # Initialize total_percentage_label with grid, at a fixed row/column
        self.total_percentage_label = ttk.Label(self.percentage_frame, text="Total: 0%")
        self.total_percentage_label.grid(row=0, column=0, columnspan=2, pady=5) # Placed at row 0, spans 2 columns
        # **CHANGE ENDS HERE**

        self.percentage_entries = {}
        
        # Botones de control
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10)

        self.start_button = ttk.Button(control_frame, text="Iniciar Mapeo", command=self.start_mapping)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(control_frame, text="Detener Mapeo", command=self.stop_mapping, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        self.standby_button = ttk.Button(control_frame, text="Activar Stand By (Ctrl Derecho)", command=self.toggle_standby_gui)
        self.standby_button.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(self.root, text="Estado: Listo")
        self.status_label.pack(pady=5)

    def update_key_selection(self):
        self.selected_keys = [opcion for opcion, var in self.key_vars.items() if var.get()]
        self.render_percentage_entries()

    def render_percentage_entries(self):
        # Limpiar entradas de porcentaje anteriores, pero OJO: no borrar el total_percentage_label
        # Modificamos para borrar solo los widgets de entradas y etiquetas de porcentaje.
        # Iteramos sobre una copia de los children para evitar problemas al modificar la lista durante la iteración
        for widget in list(self.percentage_frame.winfo_children()):
            if widget != self.total_percentage_label: # AHORA SÍ: no borrar el label de total
                widget.destroy()
        
        self.percentage_entries = {}
        
        # Start placing new entries from row 1, as row 0 is for total_percentage_label
        start_row = 1 
        
        if not self.selected_keys:
            self.total_percentage_label.config(text="Total: 0%")
            return

        for i, key in enumerate(self.selected_keys):
            # The row for these labels and entries will be start_row + i
            label = ttk.Label(self.percentage_frame, text=f"Porcentaje para {key}:")
            label.grid(row=start_row + i, column=0, padx=5, pady=2, sticky="w")
            
            entry_var = tk.StringVar(value=str(int(self.probabilidades.get(key, 0) * 100)))
            entry_var.trace_add("write", self.calculate_total_percentage)
            entry = ttk.Entry(self.percentage_frame, textvariable=entry_var, width=5)
            entry.grid(row=start_row + i, column=1, padx=5, pady=2, sticky="ew")
            
            self.percentage_entries[key] = entry_var

        self.calculate_total_percentage()

    def calculate_total_percentage(self, *args):
        total = 0
        for key, entry_var in self.percentage_entries.items():
            try:
                percentage = int(entry_var.get())
                total += percentage
            except ValueError:
                pass
        self.total_percentage_label.config(text=f"Total: {total}%")
        if total != 100:
            self.total_percentage_label.config(foreground="red")
        else:
            self.total_percentage_label.config(foreground="green")

    def start_mapping(self):
        total = 0
        current_prob = {}
        for key, entry_var in self.percentage_entries.items():
            try:
                percentage = int(entry_var.get())
                total += percentage
                current_prob[key] = percentage / 100.0
            except ValueError:
                messagebox.showerror("Error de entrada", "Por favor, ingresa solo números enteros para los porcentajes.")
                return

        if total != 100:
            messagebox.showerror("Error de Porcentaje", "La suma de los porcentajes debe ser exactamente 100%.")
            return
        
        if not self.selected_keys:
            messagebox.showerror("Error de Selección", "Debes seleccionar al menos una tecla para mapear.")
            return

        self.probabilidades = current_prob
        self.active_opciones = self.selected_keys
        self.active_probabilidades = [self.probabilidades[key] for key in self.active_opciones]

        self.status_label.config(text="Estado: Mapeo Activo")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        # Iniciar los listeners si no están ya activos
        if not hasattr(self, 'mouse_listener') or not self.mouse_listener.running:
            self.mouse_listener = mouse.Listener(on_click=self.on_click)
            self.mouse_listener.start()
        
        if not hasattr(self, 'keyboard_listener') or not self.keyboard_listener.running:
            self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
            self.keyboard_listener.start()
            
        print("Mapeo iniciado con las siguientes probabilidades:")
        for key, prob in self.probabilidades.items():
            if key in self.selected_keys:
                print(f"  {key}: {prob*100}%")

    def stop_mapping(self):
        self.status_label.config(text="Estado: Detenido")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        if hasattr(self, 'mouse_listener') and self.mouse_listener.running:
            self.mouse_listener.stop()
        if hasattr(self, 'keyboard_listener') and self.keyboard_listener.running:
            self.keyboard_listener.stop()
        print("Mapeo detenido.")

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.right and pressed and not self.standby:
            if self.active_opciones and self.active_probabilidades:
                opcion_elegida = random.choices(self.active_opciones, self.active_probabilidades)[0]
                print(f"Opción elegida: {opcion_elegida}") 
                self.simular_pulsacion(opcion_elegida)
            return True

    def simular_pulsacion(self, opcion):
        controller = keyboard.Controller()
        controller.press(str(opcion))
        controller.release(str(opcion))

    def toggle_standby(self):
        self.standby = not self.standby
        if self.standby:
            print("Modo de stand by activado")
            self.status_label.config(text="Estado: Stand By Activado")
            self.standby_button.config(text="Desactivar Stand By")
        else:
            print("Modo de stand by desactivado")
            self.status_label.config(text="Estado: Mapeo Activo" if self.start_button['state'] == 'disabled' else "Estado: Listo")
            self.standby_button.config(text="Activar Stand By (Ctrl Derecho)")

    def toggle_standby_gui(self):
        # Esta función es para el botón de la GUI, el listener de teclado usa toggle_standby directamente
        self.toggle_standby()

    def on_press(self, key):
        try:
            if key == keyboard.Key.ctrl_r:
                self.root.after(0, self.toggle_standby)
                return True
            elif key == keyboard.Key.shift_r:
                return False
        except AttributeError:
            pass

    def setup_listeners(self):
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)
        

if __name__ == "__main__":
    root = tk.Tk()
    app = KeyMapperApp(root)
    root.mainloop()