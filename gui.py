"""
Módulo de la Interfaz Gráfica de Usuario (GUI) para la Máquina de Turing.
Permite definir, visualizar en grafo, editar en matriz y simular la cinta interactivamente.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.scrolledtext as scrolledtext
import math
import os
from typing import Dict, Tuple, List, Optional

from turing_machine import MaquinaTuring, Direccion, ClaveTransicion
from graph_renderer import DistribucionGrafo
from examples_data import EJEMPLOS_DISPONIBLES


class InterfazMaquinaTuring:

    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        self.raiz.title("Simulador y Diseñador de Máquinas de Turing")
        self.raiz.geometry("1100x750")
        self.raiz.minsize(950, 650)

        self.configurar_estilos()

        self.mt: MaquinaTuring = EJEMPLOS_DISPONIBLES["a^n b^n (n >= 1)"]()

        self.posiciones_nodos: Dict[str, Tuple[float, float]] = {}
        self.nodo_arrastrado: Optional[str] = None
        self.desplazamiento_arrastre_x = 0.0
        self.desplazamiento_arrastre_y = 0.0

        self._tamano_lienzo: Tuple[int, int] = (0, 0)
        self._nodos_movidos = False

        self.simulando = False
        self.id_temporizador_simulacion = None

        self.entradas_matriz: Dict[Tuple[str, str], ttk.Entry] = {}

        self.construir_interfaz()
        self.cargar_maquina_en_interfaz()

    def configurar_estilos(self):
        self.estilo = ttk.Style()
        try:
            self.estilo.theme_use('clam')
        except Exception:
            pass

        self.estilo.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 6])
        self.estilo.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), foreground="#ffffff", background="#2563eb")
        self.estilo.configure("Success.TButton", font=("Segoe UI", 9, "bold"), foreground="#ffffff", background="#16a34a")
        self.estilo.configure("Danger.TButton", font=("Segoe UI", 9, "bold"), foreground="#ffffff", background="#dc2626")
        try:
            self.estilo.map("Success.TButton",
                foreground=[('pressed', '#ffffff'), ('active', '#ffffff')],
                background=[('pressed', '#15803d'), ('active', '#22c55e')]
            )
            self.estilo.map("Accent.TButton",
                foreground=[('pressed', '#ffffff'), ('active', '#ffffff')],
                background=[('pressed', '#1d4ed8'), ('active', '#3b82f6')]
            )
        except Exception:
            pass

    def construir_interfaz(self):
        self.barra_superior = ttk.Frame(self.raiz, padding="10 8")
        self.barra_superior.pack(fill=tk.X)

        ttk.Label(self.barra_superior, text="Máquina de Turing:", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.etiqueta_titulo_mt = ttk.Label(self.barra_superior, text=self.mt.nombre, font=("Segoe UI", 11, "italic"), foreground="#2563eb")
        self.etiqueta_titulo_mt.pack(side=tk.LEFT, padx=(0, 15))

        self.boton_nueva_maquina = ttk.Button(self.barra_superior, text="Nuevo en Blanco", command=self.nueva_maquina_en_blanco)
        self.boton_nueva_maquina.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(self.barra_superior, text="Cargar Ejemplo:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(5, 4))
        self.desplegable_ejemplos = ttk.Combobox(
            self.barra_superior,
            values=["[En blanco]"] + list(EJEMPLOS_DISPONIBLES.keys()),
            state="readonly",
            width=24
        )
        self.desplegable_ejemplos.set("a^n b^n (n >= 1)")
        self.desplegable_ejemplos.pack(side=tk.LEFT, padx=(0, 10))
        self.desplegable_ejemplos.bind("<<ComboboxSelected>>", self.al_seleccionar_ejemplo)

        self.boton_guardar_json = ttk.Button(self.barra_superior, text="Guardar JSON", command=self.guardar_en_json)
        self.boton_guardar_json.pack(side=tk.RIGHT, padx=4)

        self.boton_cargar_json = ttk.Button(self.barra_superior, text="Cargar JSON", command=self.cargar_desde_json)
        self.boton_cargar_json.pack(side=tk.RIGHT, padx=4)

        self.boton_generar_superior = ttk.Button(
            self.barra_superior,
            text="Generar Autómata",
            style="Success.TButton",
            command=self.accion_generar_automata
        )
        self.boton_generar_superior.pack(side=tk.RIGHT, padx=6)

        self.panel_pestanas = ttk.Notebook(self.raiz)
        self.panel_pestanas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        self.pestana_definicion = ttk.Frame(self.panel_pestanas, padding=10)
        self.panel_pestanas.add(self.pestana_definicion, text="1. Definición y Transiciones")
        self.construir_pestana_definicion()

        self.pestana_simulacion = ttk.Frame(self.panel_pestanas, padding=10)
        self.panel_pestanas.add(self.pestana_simulacion, text="2. Simulador de Cinta")
        self.construir_pestana_simulacion()

        self.pestana_grafo = ttk.Frame(self.panel_pestanas, padding=10)
        self.panel_pestanas.add(self.pestana_grafo, text="3. Diagrama del Autómata")
        self.construir_pestana_grafo()

        self.barra_estado = ttk.Label(self.raiz, text="Listo.", relief=tk.SUNKEN, anchor=tk.W, padding=(8, 4))
        self.barra_estado.pack(fill=tk.X, side=tk.BOTTOM)

    def construir_pestana_definicion(self):
        panel_izquierdo = ttk.LabelFrame(self.pestana_definicion, text="Formalismo M = (Q, Σ, Γ, δ, q0, B, F)", padding=10)
        panel_izquierdo.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Label(panel_izquierdo, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.entrada_nombre = ttk.Entry(panel_izquierdo, width=32)
        self.entrada_nombre.grid(row=0, column=1, sticky=tk.W, pady=3)

        ttk.Label(panel_izquierdo, text="Alfabeto Entrada Σ:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.entrada_sigma = ttk.Entry(panel_izquierdo, width=32)
        self.entrada_sigma.grid(row=1, column=1, sticky=tk.W, pady=3)

        ttk.Label(panel_izquierdo, text="Símbolo Blanco (B):").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.entrada_blanco = ttk.Entry(panel_izquierdo, width=10)
        self.entrada_blanco.grid(row=2, column=1, sticky=tk.W, pady=3)

        ttk.Label(panel_izquierdo, text="Alfabeto Cinta Γ:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.entrada_gamma = ttk.Entry(panel_izquierdo, width=32)
        self.entrada_gamma.grid(row=3, column=1, sticky=tk.W, pady=3)

        ttk.Label(panel_izquierdo, text="Estados Q:").grid(row=4, column=0, sticky=tk.W, pady=3)
        self.entrada_estados = ttk.Entry(panel_izquierdo, width=32)
        self.entrada_estados.grid(row=4, column=1, sticky=tk.W, pady=3)

        ttk.Label(panel_izquierdo, text="Estado Inicial (q0):").grid(row=5, column=0, sticky=tk.W, pady=3)
        self.entrada_estado_inicial = ttk.Entry(panel_izquierdo, width=15)
        self.entrada_estado_inicial.grid(row=5, column=1, sticky=tk.W, pady=3)

        ttk.Label(panel_izquierdo, text="Estados Aceptación (F):").grid(row=6, column=0, sticky=tk.W, pady=3)
        self.entrada_estados_aceptacion = ttk.Entry(panel_izquierdo, width=32)
        self.entrada_estados_aceptacion.grid(row=6, column=1, sticky=tk.W, pady=3)

        ttk.Label(panel_izquierdo, text="Estados Rechazo:").grid(row=7, column=0, sticky=tk.W, pady=3)
        self.entrada_estados_rechazo = ttk.Entry(panel_izquierdo, width=32)
        self.entrada_estados_rechazo.grid(row=7, column=1, sticky=tk.W, pady=3)

        boton_aplicar_def = ttk.Button(panel_izquierdo, text="Actualizar Parámetros", command=self.aplicar_entradas_definicion)
        boton_aplicar_def.grid(row=8, column=0, columnspan=2, pady=(14, 4), sticky=tk.EW)

        boton_regen_izq = ttk.Button(panel_izquierdo, text="Reconstruir Cuadrícula", command=self.reconstruir_cuadricula_matriz)
        boton_regen_izq.grid(row=9, column=0, columnspan=2, pady=4, sticky=tk.EW)

        boton_validar = ttk.Button(panel_izquierdo, text="Validar Autómata", command=self.validar_maquina)
        boton_validar.grid(row=10, column=0, columnspan=2, pady=4, sticky=tk.EW)

        boton_gen_izq = ttk.Button(panel_izquierdo, text="Generar Autómata", style="Success.TButton", command=self.accion_generar_automata)
        boton_gen_izq.grid(row=11, column=0, columnspan=2, pady=(12, 4), sticky=tk.EW)

        panel_derecho = ttk.LabelFrame(self.pestana_definicion, text="Función y Tabla de Transiciones δ", padding=8)
        panel_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        barra_herramientas_trans = ttk.Frame(panel_derecho)
        barra_herramientas_trans.pack(fill=tk.X, pady=(0, 6))

        boton_gen_principal = ttk.Button(
            barra_herramientas_trans,
            text="Generar Autómata",
            style="Success.TButton",
            command=self.accion_generar_automata
        )
        boton_gen_principal.pack(side=tk.LEFT, padx=(0, 6))

        boton_regen_cuadricula = ttk.Button(barra_herramientas_trans, text="Regenerar Cuadrícula", command=self.reconstruir_cuadricula_matriz)
        boton_regen_cuadricula.pack(side=tk.LEFT, padx=4)

        boton_exportar_csv = ttk.Button(barra_herramientas_trans, text="Exportar Tabla a CSV", command=self.exportar_matriz_a_csv)
        boton_exportar_csv.pack(side=tk.LEFT, padx=4)

        self.etiqueta_conteo_trans = ttk.Label(barra_herramientas_trans, text="Total: 0 transiciones", font=("Segoe UI", 9, "italic"))
        self.etiqueta_conteo_trans.pack(side=tk.RIGHT, padx=4)

        self.panel_transiciones = ttk.Notebook(panel_derecho)
        self.panel_transiciones.pack(fill=tk.BOTH, expand=True)

        self.pestana_matriz = ttk.Frame(self.panel_transiciones, padding=6)
        self.panel_transiciones.add(self.pestana_matriz, text="Matriz 2D")
        self.construir_pestana_matriz()

        self.pestana_importar_texto = ttk.Frame(self.panel_transiciones, padding=6)
        self.panel_transiciones.add(self.pestana_importar_texto, text="Pegar / Importar Texto")
        self.construir_pestana_importacion_texto()

        self.pestana_lista = ttk.Frame(self.panel_transiciones, padding=6)
        self.panel_transiciones.add(self.pestana_lista, text="Vista en Lista")
        self.construir_pestana_lista()

    def construir_pestana_matriz(self):
        contenedor_cuadricula = ttk.Frame(self.pestana_matriz)
        contenedor_cuadricula.pack(fill=tk.BOTH, expand=True)

        self.lienzo_matriz = tk.Canvas(contenedor_cuadricula, bg="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        desplazamiento_v = ttk.Scrollbar(contenedor_cuadricula, orient=tk.VERTICAL, command=self.lienzo_matriz.yview)
        desplazamiento_h = ttk.Scrollbar(contenedor_cuadricula, orient=tk.HORIZONTAL, command=self.lienzo_matriz.xview)

        self.marco_interno_matriz = ttk.Frame(self.lienzo_matriz)
        self.marco_interno_matriz.bind(
            "<Configure>",
            lambda e: self.lienzo_matriz.configure(scrollregion=self.lienzo_matriz.bbox("all"))
        )
        self.id_ventana_matriz = self.lienzo_matriz.create_window((0, 0), window=self.marco_interno_matriz, anchor="nw")

        self.lienzo_matriz.configure(xscrollcommand=desplazamiento_h.set, yscrollcommand=desplazamiento_v.set)

        self.lienzo_matriz.grid(row=0, column=0, sticky="nsew")
        desplazamiento_v.grid(row=0, column=1, sticky="ns")
        desplazamiento_h.grid(row=1, column=0, sticky="ew")

        contenedor_cuadricula.grid_rowconfigure(0, weight=1)
        contenedor_cuadricula.grid_columnconfigure(0, weight=1)

        panel_inferior_matriz = ttk.Frame(self.pestana_matriz)
        panel_inferior_matriz.pack(fill=tk.X, pady=(6, 0))

        boton_aplicar_matriz = ttk.Button(panel_inferior_matriz, text="Guardar Cambios de la Matriz", command=self.aplicar_cambios_matriz)
        boton_aplicar_matriz.pack(side=tk.LEFT, padx=4)

        boton_gen_desde_matriz = ttk.Button(
            panel_inferior_matriz,
            text="Generar Autómata",
            style="Accent.TButton",
            command=self.accion_generar_automata
        )
        boton_gen_desde_matriz.pack(side=tk.LEFT, padx=4)

        boton_limpiar_matriz = ttk.Button(panel_inferior_matriz, text="Limpiar Celdas", command=self.limpiar_celdas_matriz)
        boton_limpiar_matriz.pack(side=tk.RIGHT, padx=4)

    def reconstruir_cuadricula_matriz(self):
        for elemento in self.marco_interno_matriz.winfo_children():
            elemento.destroy()

        self.entradas_matriz = {}

        cadena_estados_bruta = self.entrada_estados.get().strip() if hasattr(self, 'entrada_estados') else ""
        if cadena_estados_bruta:
            lista_estados = [s.strip() for s in cadena_estados_bruta.split(",") if s.strip()]
        else:
            lista_estados = sorted(list(self.mt.estados))

        estado_ini = self.entrada_estado_inicial.get().strip() or self.mt.estado_inicial
        if estado_ini in lista_estados:
            lista_estados.remove(estado_ini)
            lista_estados = [estado_ini] + lista_estados
        elif estado_ini:
            lista_estados = [estado_ini] + lista_estados

        cadena_sigma_bruta = self.entrada_sigma.get().strip() if hasattr(self, 'entrada_sigma') else ""
        cadena_gamma_bruta = self.entrada_gamma.get().strip() if hasattr(self, 'entrada_gamma') else ""
        blanco = self.entrada_blanco.get().strip() if hasattr(self, 'entrada_blanco') else self.mt.simbolo_blanco

        simbolos_sigma = [s.strip() for s in cadena_sigma_bruta.split(",") if s.strip()] if cadena_sigma_bruta else sorted(list(self.mt.alfabeto_entrada))
        simbolos_gamma = [s.strip() for s in cadena_gamma_bruta.split(",") if s.strip()] if cadena_gamma_bruta else sorted(list(self.mt.alfabeto_cinta))

        lista_simbolos = []
        for s in simbolos_sigma:
            if s not in lista_simbolos and s != blanco:
                lista_simbolos.append(s)
        for s in simbolos_gamma:
            if s not in lista_simbolos and s != blanco:
                lista_simbolos.append(s)
        if blanco and blanco not in lista_simbolos:
            lista_simbolos.append(blanco)

        if not lista_simbolos:
            lista_simbolos = ["0", "1", "B"]

        etiqueta_esquina = tk.Label(
            self.marco_interno_matriz,
            text="Estado \\ Símbolo",
            font=("Segoe UI", 9, "bold"),
            bg="#e2e8f0",
            fg="#1e293b",
            padx=10,
            pady=6,
            relief=tk.RIDGE
        )
        etiqueta_esquina.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        for col_idx, sym in enumerate(lista_simbolos, start=1):
            etiqueta_sim = tk.Label(
                self.marco_interno_matriz,
                text=f"'{sym}'",
                font=("Consolas", 10, "bold"),
                bg="#f1f5f9",
                fg="#2563eb" if sym in simbolos_sigma else "#475569",
                padx=8,
                pady=6,
                relief=tk.RIDGE,
                width=16
            )
            etiqueta_sim.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)

        estados_aceptacion = {s.strip() for s in self.entrada_estados_aceptacion.get().split(",") if s.strip()} if hasattr(self, 'entrada_estados_aceptacion') else self.mt.estados_aceptacion
        estados_rechazo = {s.strip() for s in self.entrada_estados_rechazo.get().split(",") if s.strip()} if hasattr(self, 'entrada_estados_rechazo') else self.mt.estados_rechazo

        for fila_idx, st in enumerate(lista_estados, start=1):
            fondo_st = "#f8fafc"
            texto_st = "#0f172a"
            if st == estado_ini:
                fondo_st = "#e0f2fe"
                texto_st = "#0369a1"
            elif st in estados_aceptacion:
                fondo_st = "#dcfce7"
                texto_st = "#15803d"
            elif st in estados_rechazo:
                fondo_st = "#fee2e2"
                texto_st = "#b91c1c"

            etiqueta_st = tk.Label(
                self.marco_interno_matriz,
                text=st,
                font=("Segoe UI", 9, "bold"),
                bg=fondo_st,
                fg=texto_st,
                padx=8,
                pady=4,
                relief=tk.RIDGE,
                anchor="center",
                width=12
            )
            etiqueta_st.grid(row=fila_idx, column=0, sticky="nsew", padx=1, pady=1)

            for col_idx, sym in enumerate(lista_simbolos, start=1):
                entrada_celda = ttk.Entry(self.marco_interno_matriz, font=("Consolas", 9), width=16, justify=tk.CENTER)
                entrada_celda.grid(row=fila_idx, column=col_idx, sticky="nsew", padx=1, pady=1)

                clave = ClaveTransicion(st, sym)
                if clave in self.mt.transiciones:
                    valor = self.mt.transiciones[clave]
                    entrada_celda.insert(0, f"({valor.nuevo_estado}, {valor.simbolo_escrito}, {valor.direccion.value})")

                self.entradas_matriz[(st, sym)] = entrada_celda

        self.marco_interno_matriz.update_idletasks()
        self.lienzo_matriz.configure(scrollregion=self.lienzo_matriz.bbox("all"))

    def aplicar_cambios_matriz(self, mostrar_mensaje: bool = True) -> bool:
        if not hasattr(self, 'entradas_matriz') or not self.entradas_matriz:
            return True

        diccionario_matriz = {}
        for (st, sym), entrada_celda in self.entradas_matriz.items():
            valor = entrada_celda.get().strip()
            if valor:
                diccionario_matriz[(st, sym)] = valor

        agregadas, errores = self.mt.establecer_transiciones_matriz(diccionario_matriz, limpiar_existentes=True)
        self.actualizar_tabla_transiciones()
        self.recalcular_distribucion_grafo()

        if errores:
            texto_errores = "\n".join(errores[:5])
            if len(errores) > 5:
                texto_errores += f"\n...y {len(errores) - 5} advertencias más."
            messagebox.showwarning("Advertencias en Celdas", f"Se aplicaron {agregadas} transiciones, pero hubo observaciones:\n\n{texto_errores}")
            return False

        if mostrar_mensaje:
            messagebox.showinfo("Matriz Aplicada", f"Se actualizaron exitosamente {agregadas} transiciones.")
        self.barra_estado.config(text=f"Matriz actualizada: {agregadas} transiciones.")
        return True

    def limpiar_celdas_matriz(self):
        if messagebox.askyesno("Confirmar Limpieza", "¿Deseas borrar el contenido de todas las celdas de la matriz?"):
            for entrada in self.entradas_matriz.values():
                entrada.delete(0, tk.END)

    def construir_pestana_importacion_texto(self):
        control_superior = ttk.Frame(self.pestana_importar_texto)
        control_superior.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(control_superior, text="Tabla de transiciones (CSV o lista):", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        boton_plantilla_csv = ttk.Button(control_superior, text="Plantilla Matriz CSV", command=self.insertar_plantilla_csv)
        boton_plantilla_csv.pack(side=tk.RIGHT, padx=4)

        boton_plantilla_lista = ttk.Button(control_superior, text="Plantilla Lista", command=self.insertar_plantilla_lista)
        boton_plantilla_lista.pack(side=tk.RIGHT, padx=4)

        boton_cargar_archivo = ttk.Button(control_superior, text="Cargar Archivo", command=self.cargar_archivo_texto)
        boton_cargar_archivo.pack(side=tk.RIGHT, padx=4)

        self.texto_importacion_masiva = scrolledtext.ScrolledText(self.pestana_importar_texto, height=12, font=("Consolas", 10), wrap=tk.NONE)
        self.texto_importacion_masiva.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        control_inferior = ttk.Frame(self.pestana_importar_texto)
        control_inferior.pack(fill=tk.X)

        boton_procesar = ttk.Button(control_inferior, text="Procesar Texto", command=self.procesar_importacion_texto)
        boton_procesar.pack(side=tk.LEFT, padx=4)

        boton_procesar_y_generar = ttk.Button(
            control_inferior,
            text="Procesar y Generar",
            style="Success.TButton",
            command=self.accion_generar_desde_texto
        )
        boton_procesar_y_generar.pack(side=tk.LEFT, padx=4)

        boton_limpiar_texto = ttk.Button(
            control_inferior,
            text="Limpiar Texto",
            command=lambda: self.texto_importacion_masiva.delete("1.0", tk.END)
        )
        boton_limpiar_texto.pack(side=tk.RIGHT, padx=4)

    def insertar_plantilla_csv(self):
        muestra = (
            "Estado, 0, 1, B\n"
            "q0, (q0, 0, R), (q0, 1, R), (q1, B, L)\n"
            "q1, (q_accept, 1, S), (q1, 0, L), (q_accept, 1, S)\n"
            "q_accept, , , \n"
        )
        self.texto_importacion_masiva.delete("1.0", tk.END)
        self.texto_importacion_masiva.insert(tk.END, muestra)

    def insertar_plantilla_lista(self):
        muestra = (
            "q0 0 q0 0 R\n"
            "q0 1 q0 1 R\n"
            "q0 B q1 B L\n"
            "q1 0 q_accept 1 S\n"
            "q1 1 q1 0 L\n"
            "q1 B q_accept 1 S\n"
        )
        self.texto_importacion_masiva.delete("1.0", tk.END)
        self.texto_importacion_masiva.insert(tk.END, muestra)

    def cargar_archivo_texto(self):
        ruta_archivo = filedialog.askopenfilename(
            filetypes=[("Archivos CSV y Texto", "*.csv;*.txt"), ("Archivos CSV", "*.csv"), ("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")],
            title="Cargar Tabla de Transiciones"
        )
        if ruta_archivo:
            try:
                with open(ruta_archivo, "r", encoding="utf-8") as f:
                    contenido = f.read()
                self.texto_importacion_masiva.delete("1.0", tk.END)
                self.texto_importacion_masiva.insert(tk.END, contenido)
                self.barra_estado.config(text=f"Archivo cargado: {os.path.basename(ruta_archivo)}")
            except Exception as e:
                messagebox.showerror("Error al leer archivo", str(e))

    def procesar_importacion_texto(self, mostrar_mensaje: bool = True) -> bool:
        texto_bruto = self.texto_importacion_masiva.get("1.0", tk.END).strip()
        if not texto_bruto:
            if mostrar_mensaje:
                messagebox.showwarning("Texto Vacío", "Por favor escribe o pega la tabla de transiciones antes de procesar.")
            return False

        exito, mensaje, conteo = self.mt.importar_desde_texto(texto_bruto, limpiar_existentes=True)
        if not exito:
            messagebox.showerror("Error al Procesar Transiciones", mensaje)
            return False

        if hasattr(self, 'entrada_estados'):
            self.entrada_estados.delete(0, tk.END)
            self.entrada_estados.insert(0, ", ".join(sorted(list(self.mt.estados))))

        self.entrada_gamma.delete(0, tk.END)
        self.entrada_gamma.insert(0, ", ".join(sorted(list(self.mt.alfabeto_cinta))))

        self.actualizar_tabla_transiciones()
        self.reconstruir_cuadricula_matriz()
        self.recalcular_distribucion_grafo()

        if mostrar_mensaje:
            messagebox.showinfo("Procesamiento Exitoso", mensaje)
        self.barra_estado.config(text=mensaje)
        return True

    def accion_generar_desde_texto(self):
        if self.procesar_importacion_texto(mostrar_mensaje=False):
            self.accion_generar_automata()

    def exportar_matriz_a_csv(self):
        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            title="Exportar Tabla de Transiciones como CSV"
        )
        if not ruta_archivo:
            return
        try:
            cadena_csv = self.mt.a_csv()
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.write(cadena_csv)
            messagebox.showinfo("Exportación Exitosa", f"Tabla de transiciones exportada a:\n{ruta_archivo}")
        except Exception as e:
            messagebox.showerror("Error al Exportar", f"No se pudo guardar el archivo: {e}")

    def construir_pestana_lista(self):
        marco_agregar = ttk.Frame(self.pestana_lista)
        marco_agregar.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(marco_agregar, text="Estado:").grid(row=0, column=0, padx=2)
        self.entrada_t_estado = ttk.Entry(marco_agregar, width=8)
        self.entrada_t_estado.grid(row=0, column=1, padx=2)

        ttk.Label(marco_agregar, text="Lee:").grid(row=0, column=2, padx=2)
        self.entrada_t_lectura = ttk.Entry(marco_agregar, width=5)
        self.entrada_t_lectura.grid(row=0, column=3, padx=2)

        ttk.Label(marco_agregar, text="Nuevo Est:").grid(row=0, column=4, padx=2)
        self.entrada_t_siguiente = ttk.Entry(marco_agregar, width=8)
        self.entrada_t_siguiente.grid(row=0, column=5, padx=2)

        ttk.Label(marco_agregar, text="Escribe:").grid(row=0, column=6, padx=2)
        self.entrada_t_escritura = ttk.Entry(marco_agregar, width=5)
        self.entrada_t_escritura.grid(row=0, column=7, padx=2)

        ttk.Label(marco_agregar, text="Dir:").grid(row=0, column=8, padx=2)
        self.desplegable_t_direccion = ttk.Combobox(marco_agregar, values=["R", "L", "S"], width=5, state="readonly")
        self.desplegable_t_direccion.set("R")
        self.desplegable_t_direccion.grid(row=0, column=9, padx=2)

        boton_agregar_trans = ttk.Button(marco_agregar, text="Agregar / Modificar", command=self.agregar_transicion_desde_entradas)
        boton_agregar_trans.grid(row=0, column=10, padx=(8, 2))

        contenedor_tabla = ttk.Frame(self.pestana_lista)
        contenedor_tabla.pack(fill=tk.BOTH, expand=True)

        columnas = ("state", "read", "next", "write", "dir")
        self.arbol_transiciones = ttk.Treeview(contenedor_tabla, columns=columnas, show="headings", selectmode="browse")
        self.arbol_transiciones.heading("state", text="Estado Origen")
        self.arbol_transiciones.heading("read", text="Símbolo Leído")
        self.arbol_transiciones.heading("next", text="Nuevo Estado")
        self.arbol_transiciones.heading("write", text="Símbolo Escrito")
        self.arbol_transiciones.heading("dir", text="Dirección")

        self.arbol_transiciones.column("state", width=120, anchor=tk.CENTER)
        self.arbol_transiciones.column("read", width=110, anchor=tk.CENTER)
        self.arbol_transiciones.column("next", width=120, anchor=tk.CENTER)
        self.arbol_transiciones.column("write", width=110, anchor=tk.CENTER)
        self.arbol_transiciones.column("dir", width=100, anchor=tk.CENTER)

        barra_scroll = ttk.Scrollbar(contenedor_tabla, orient=tk.VERTICAL, command=self.arbol_transiciones.yview)
        self.arbol_transiciones.configure(yscroll=barra_scroll.set)
        self.arbol_transiciones.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.arbol_transiciones.bind("<<TreeviewSelect>>", self.al_seleccionar_fila_transicion)

        marco_botones_tabla = ttk.Frame(self.pestana_lista)
        marco_botones_tabla.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(marco_botones_tabla, text="Eliminar Seleccionada", command=self.eliminar_transicion_seleccionada).pack(side=tk.LEFT, padx=4)
        ttk.Button(marco_botones_tabla, text="Limpiar Transiciones", command=self.limpiar_todas_las_transiciones).pack(side=tk.LEFT, padx=4)
        self.etiqueta_conteo_trans_lista = ttk.Label(marco_botones_tabla, text="Total: 0 transiciones", font=("Segoe UI", 9, "italic"))
        self.etiqueta_conteo_trans_lista.pack(side=tk.RIGHT, padx=4)

    def construir_pestana_simulacion(self):
        control_superior = ttk.LabelFrame(self.pestana_simulacion, text="Entrada y Control de Ejecución", padding=10)
        control_superior.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(control_superior, text="Cadena de Entrada:").pack(side=tk.LEFT, padx=(0, 6))
        self.entrada_sim_palabra = ttk.Entry(control_superior, width=28, font=("Consolas", 11))
        self.entrada_sim_palabra.pack(side=tk.LEFT, padx=(0, 10))
        self.entrada_sim_palabra.insert(0, "aabb")

        boton_cargar_palabra = ttk.Button(control_superior, text="Cargar Palabra", command=self.sim_cargar_palabra)
        boton_cargar_palabra.pack(side=tk.LEFT, padx=4)

        self.boton_paso = ttk.Button(control_superior, text="Paso a Paso", command=self.sim_paso)
        self.boton_paso.pack(side=tk.LEFT, padx=4)

        self.boton_reproducir = ttk.Button(control_superior, text="Ejecutar", command=self.sim_alternar_reproduccion)
        self.boton_reproducir.pack(side=tk.LEFT, padx=4)

        boton_reiniciar = ttk.Button(control_superior, text="Reiniciar", command=self.sim_reiniciar)
        boton_reiniciar.pack(side=tk.LEFT, padx=4)

        ttk.Label(control_superior, text="Velocidad:").pack(side=tk.LEFT, padx=(15, 4))
        self.deslizador_velocidad = tk.Scale(control_superior, from_=50, to=1000, orient=tk.HORIZONTAL, length=120, showvalue=False)
        self.deslizador_velocidad.set(300)
        self.deslizador_velocidad.pack(side=tk.LEFT, padx=2)
        ttk.Label(control_superior, text="ms", font=("Segoe UI", 8)).pack(side=tk.LEFT)

        self.etiqueta_estado_sim = tk.Label(
            self.pestana_simulacion,
            text="Listo para simular.",
            font=("Segoe UI", 11, "bold"),
            bg="#e0f2fe",
            fg="#0369a1",
            padx=10,
            pady=6,
            relief=tk.GROOVE
        )
        self.etiqueta_estado_sim.pack(fill=tk.X, pady=(0, 10))

        marco_cinta = ttk.LabelFrame(self.pestana_simulacion, text="Visualización de la Cinta", padding=5)
        marco_cinta.pack(fill=tk.X, pady=(0, 10))

        self.lienzo_cinta = tk.Canvas(marco_cinta, height=130, bg="#f8fafc", highlightthickness=1, highlightbackground="#cbd5e1")
        self.lienzo_cinta.pack(fill=tk.X, expand=True)

        marco_info = ttk.Frame(self.pestana_simulacion)
        marco_info.pack(fill=tk.X, pady=(0, 10))

        self.etiqueta_sim_estado_actual = ttk.Label(marco_info, text="Estado: q0", font=("Segoe UI", 10, "bold"))
        self.etiqueta_sim_estado_actual.pack(side=tk.LEFT, padx=15)

        self.etiqueta_sim_pasos = ttk.Label(marco_info, text="Pasos: 0", font=("Segoe UI", 10))
        self.etiqueta_sim_pasos.pack(side=tk.LEFT, padx=15)

        self.etiqueta_sim_pos_cabezal = ttk.Label(marco_info, text="Posición Cabezal: 0", font=("Segoe UI", 10))
        self.etiqueta_sim_pos_cabezal.pack(side=tk.LEFT, padx=15)

        marco_registro = ttk.LabelFrame(self.pestana_simulacion, text="Historial de Pasos", padding=5)
        marco_registro.pack(fill=tk.BOTH, expand=True)

        columnas_registro = ("step", "state", "read", "trans", "tape")
        self.arbol_registro = ttk.Treeview(marco_registro, columns=columnas_registro, show="headings")
        self.arbol_registro.heading("step", text="Paso")
        self.arbol_registro.heading("state", text="Estado")
        self.arbol_registro.heading("read", text="Leído")
        self.arbol_registro.heading("trans", text="Transición Aplicada")
        self.arbol_registro.heading("tape", text="Instantánea de Cinta [Cabezal]")

        self.arbol_registro.column("step", width=60, anchor=tk.CENTER)
        self.arbol_registro.column("state", width=90, anchor=tk.CENTER)
        self.arbol_registro.column("read", width=70, anchor=tk.CENTER)
        self.arbol_registro.column("trans", width=200, anchor=tk.W)
        self.arbol_registro.column("tape", width=500, anchor=tk.W)

        scroll_registro = ttk.Scrollbar(marco_registro, orient=tk.VERTICAL, command=self.arbol_registro.yview)
        self.arbol_registro.configure(yscroll=scroll_registro.set)
        self.arbol_registro.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_registro.pack(side=tk.RIGHT, fill=tk.Y)

    def construir_pestana_grafo(self):
        panel_superior_grafo = ttk.Frame(self.pestana_grafo)
        panel_superior_grafo.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(panel_superior_grafo, text="Grafo de Estados y Transiciones:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        boton_reorganizar = ttk.Button(panel_superior_grafo, text="Reorganizar Nodos", command=self.recalcular_distribucion_grafo)
        boton_reorganizar.pack(side=tk.RIGHT, padx=4)

        self.lienzo_grafo = tk.Canvas(self.pestana_grafo, bg="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        self.lienzo_grafo.pack(fill=tk.BOTH, expand=True)

        self.lienzo_grafo.bind("<ButtonPress-1>", self.al_hacer_clic_grafo)
        self.lienzo_grafo.bind("<B1-Motion>", self.al_arrastrar_grafo)
        self.lienzo_grafo.bind("<ButtonRelease-1>", self.al_soltar_grafo)
        self.lienzo_grafo.bind("<Configure>", self.al_redimensionar_grafo)

    def al_redimensionar_grafo(self, evento):
        """
        Se dispara cuando el canvas del diagrama recibe su tamaño real o cuando cambia.
        Recalcula el layout con el tamaño correcto, salvo que el usuario ya haya movido nodos a mano.
        """
        if evento.width < 50 or evento.height < 50:
            return
        tamano = (evento.width, evento.height)
        if tamano != self._tamano_lienzo and not self._nodos_movidos:
            self._tamano_lienzo = tamano
            self.recalcular_distribucion_grafo()
        else:
            self._tamano_lienzo = tamano
            self.dibujar_grafo()

    def nueva_maquina_en_blanco(self):
        self.mt = MaquinaTuring(
            nombre="Nuevo Autómata",
            estados={"q0"},
            alfabeto_entrada=set(),
            alfabeto_cinta={"B"},
            simbolo_blanco="B",
            estado_inicial="q0",
            estados_aceptacion=set(),
            estados_rechazo=set()
        )
        self.etiqueta_titulo_mt.config(text=self.mt.nombre)
        self.entrada_nombre.delete(0, tk.END)
        self.entrada_nombre.insert(0, self.mt.nombre)

        self.entrada_sigma.delete(0, tk.END)
        self.entrada_blanco.delete(0, tk.END)
        self.entrada_blanco.insert(0, "B")
        self.entrada_gamma.delete(0, tk.END)
        self.entrada_gamma.insert(0, "B")
        self.entrada_estados.delete(0, tk.END)
        self.entrada_estados.insert(0, "q0")
        self.entrada_estado_inicial.delete(0, tk.END)
        self.entrada_estado_inicial.insert(0, "q0")
        self.entrada_estados_aceptacion.delete(0, tk.END)
        self.entrada_estados_rechazo.delete(0, tk.END)
        self.entrada_sim_palabra.delete(0, tk.END)
        if hasattr(self, 'texto_importacion_masiva'):
            self.texto_importacion_masiva.delete("1.0", tk.END)

        self.desplegable_ejemplos.set("[En blanco]")
        self.actualizar_tabla_transiciones()
        if hasattr(self, 'marco_interno_matriz'):
            self.reconstruir_cuadricula_matriz()
        self.recalcular_distribucion_grafo()
        self.sim_cargar_palabra()
        self.barra_estado.config(text="Autómata en blanco listo para definir.")

    def cargar_maquina_en_interfaz(self):
        self.etiqueta_titulo_mt.config(text=self.mt.nombre)
        self.entrada_nombre.delete(0, tk.END)
        self.entrada_nombre.insert(0, self.mt.nombre)

        self.entrada_sigma.delete(0, tk.END)
        self.entrada_sigma.insert(0, ", ".join(sorted(list(self.mt.alfabeto_entrada))))

        self.entrada_blanco.delete(0, tk.END)
        self.entrada_blanco.insert(0, self.mt.simbolo_blanco)

        self.entrada_gamma.delete(0, tk.END)
        self.entrada_gamma.insert(0, ", ".join(sorted(list(self.mt.alfabeto_cinta))))

        self.entrada_estado_inicial.delete(0, tk.END)
        self.entrada_estado_inicial.insert(0, self.mt.estado_inicial)

        self.entrada_estados_aceptacion.delete(0, tk.END)
        self.entrada_estados_aceptacion.insert(0, ", ".join(sorted(list(self.mt.estados_aceptacion))))

        self.entrada_estados_rechazo.delete(0, tk.END)
        self.entrada_estados_rechazo.insert(0, ", ".join(sorted(list(self.mt.estados_rechazo))))

        if hasattr(self, 'entrada_estados'):
            self.entrada_estados.delete(0, tk.END)
            self.entrada_estados.insert(0, ", ".join(sorted(list(self.mt.estados))))

        self.actualizar_tabla_transiciones()
        if hasattr(self, 'marco_interno_matriz'):
            self.reconstruir_cuadricula_matriz()
        self.recalcular_distribucion_grafo()
        self.sim_cargar_palabra()

    def actualizar_tabla_transiciones(self):
        for elemento in self.arbol_transiciones.get_children():
            self.arbol_transiciones.delete(elemento)

        claves_ordenadas = sorted(self.mt.transiciones.keys(), key=lambda k: (k.estado, k.simbolo))
        for clave in claves_ordenadas:
            valor = self.mt.transiciones[clave]
            self.arbol_transiciones.insert(
                "",
                tk.END,
                values=(clave.estado, clave.simbolo, valor.nuevo_estado, valor.simbolo_escrito, valor.direccion.value)
            )

        total_texto = f"Total: {len(self.mt.transiciones)} transiciones"
        self.etiqueta_conteo_trans.config(text=total_texto)
        if hasattr(self, 'etiqueta_conteo_trans_lista'):
            self.etiqueta_conteo_trans_lista.config(text=total_texto)

    def al_seleccionar_ejemplo(self, evento=None):
        nombre = self.desplegable_ejemplos.get()
        if nombre == "[En blanco]":
            self.nueva_maquina_en_blanco()
            return
        if nombre in EJEMPLOS_DISPONIBLES:
            self.mt = EJEMPLOS_DISPONIBLES[nombre]()
            if "a^n b^n" in nombre:
                self.entrada_sim_palabra.delete(0, tk.END)
                self.entrada_sim_palabra.insert(0, "aabb")
            elif "Incrementador" in nombre:
                self.entrada_sim_palabra.delete(0, tk.END)
                self.entrada_sim_palabra.insert(0, "1011")
            elif "Palíndromos" in nombre:
                self.entrada_sim_palabra.delete(0, tk.END)
                self.entrada_sim_palabra.insert(0, "abba")
            elif "Inversor" in nombre:
                self.entrada_sim_palabra.delete(0, tk.END)
                self.entrada_sim_palabra.insert(0, "11010")

            self.cargar_maquina_en_interfaz()
            self.barra_estado.config(text=f"Ejemplo '{nombre}' cargado.")

    def _aplicar_datos_definicion(self):
        nombre = self.entrada_nombre.get().strip() or "Máquina de Turing"
        blanco = self.entrada_blanco.get().strip() or "B"

        def analizar_conjunto(texto: str) -> set:
            return {parte.strip() for parte in texto.split(",") if parte.strip()}

        sigma = analizar_conjunto(self.entrada_sigma.get())
        gamma = analizar_conjunto(self.entrada_gamma.get())
        estados_declarados = analizar_conjunto(self.entrada_estados.get()) if hasattr(self, 'entrada_estados') else set()
        estado_ini = self.entrada_estado_inicial.get().strip() or "q0"
        aceptacion = analizar_conjunto(self.entrada_estados_aceptacion.get())
        rechazo = analizar_conjunto(self.entrada_estados_rechazo.get())

        self.mt.nombre = nombre
        self.mt.simbolo_blanco = blanco
        self.mt.alfabeto_entrada = sigma
        self.mt.alfabeto_cinta = gamma
        self.mt.estado_inicial = estado_ini
        self.mt.estados_aceptacion = aceptacion
        self.mt.estados_rechazo = rechazo

        self.mt.alfabeto_cinta.add(blanco)
        self.mt.alfabeto_cinta.update(sigma)
        self.mt.estados.update(estados_declarados)
        self.mt.estados.add(estado_ini)
        self.mt.estados.update(aceptacion)
        self.mt.estados.update(rechazo)

        self.etiqueta_titulo_mt.config(text=self.mt.nombre)

    def aplicar_entradas_definicion(self):
        self._aplicar_datos_definicion()
        if hasattr(self, 'marco_interno_matriz'):
            self.reconstruir_cuadricula_matriz()
        self.recalcular_distribucion_grafo()
        messagebox.showinfo("Parámetros Actualizados", "Los parámetros del formalismo fueron actualizados correctamente.")

    def accion_generar_automata(self):
        self._aplicar_datos_definicion()

        if hasattr(self, 'panel_transiciones'):
            try:
                pestana_actual_idx = self.panel_transiciones.index(self.panel_transiciones.select())
                if pestana_actual_idx == 0:
                    if not self.aplicar_cambios_matriz(mostrar_mensaje=False):
                        return
                elif pestana_actual_idx == 1:
                    if not self.procesar_importacion_texto(mostrar_mensaje=False):
                        return
            except Exception:
                pass

        self.actualizar_tabla_transiciones()
        if hasattr(self, 'marco_interno_matriz'):
            self.reconstruir_cuadricula_matriz()

        es_valido, mensajes = self.mt.validar()

        self.panel_pestanas.select(self.pestana_grafo)
        self.raiz.update_idletasks()
        self.recalcular_distribucion_grafo()

        conteo_trans = len(self.mt.transiciones)
        conteo_estados = len(self.mt.estados)
        mensaje_estado = f"Autómata generado: {conteo_estados} estados, {conteo_trans} transiciones."
        self.barra_estado.config(text=mensaje_estado)

        if not es_valido:
            observaciones = "\n- ".join(mensajes[:4])
            messagebox.showwarning(
                "Autómata Generado con Observaciones",
                f"El autómata se generó con {conteo_estados} estados y {conteo_trans} transiciones, pero tiene observaciones:\n\n- {observaciones}"
            )
        else:
            messagebox.showinfo(
                "Autómata Generado",
                f"El autómata '{self.mt.nombre}' fue generado exitosamente.\n\n"
                f"Estados: {conteo_estados}\n"
                f"Transiciones: {conteo_trans}"
            )

    def agregar_transicion_desde_entradas(self):
        estado = self.entrada_t_estado.get().strip()
        simb_lectura = self.entrada_t_lectura.get().strip()
        nuevo_estado = self.entrada_t_siguiente.get().strip()
        simb_escritura = self.entrada_t_escritura.get().strip()
        dir_val = self.desplegable_t_direccion.get().split()[0]

        if not estado or not simb_lectura or not nuevo_estado or not simb_escritura:
            messagebox.showwarning("Campos Requeridos", "Por favor completa todos los campos de la transición.")
            return

        self.mt.agregar_transicion(estado, simb_lectura, nuevo_estado, simb_escritura, dir_val)
        self.actualizar_tabla_transiciones()
        if hasattr(self, 'marco_interno_matriz'):
            self.reconstruir_cuadricula_matriz()
        self.recalcular_distribucion_grafo()

        self.entrada_t_lectura.delete(0, tk.END)
        self.entrada_t_escritura.delete(0, tk.END)
        self.barra_estado.config(text=f"Transición guardada: ({estado}, {simb_lectura}) -> ({nuevo_estado}, {simb_escritura}, {dir_val})")

    def al_seleccionar_fila_transicion(self, evento=None):
        seleccion = self.arbol_transiciones.selection()
        if not seleccion:
            return
        elemento = self.arbol_transiciones.item(seleccion[0])
        valores = elemento['values']
        if len(valores) == 5:
            self.entrada_t_estado.delete(0, tk.END)
            self.entrada_t_estado.insert(0, str(valores[0]))
            self.entrada_t_lectura.delete(0, tk.END)
            self.entrada_t_lectura.insert(0, str(valores[1]))
            self.entrada_t_siguiente.delete(0, tk.END)
            self.entrada_t_siguiente.insert(0, str(valores[2]))
            self.entrada_t_escritura.delete(0, tk.END)
            self.entrada_t_escritura.insert(0, str(valores[3]))
            dir_str = str(valores[4])
            for opt in ["R", "L", "S"]:
                if opt == dir_str:
                    self.desplegable_t_direccion.set(opt)
                    break

    def eliminar_transicion_seleccionada(self):
        seleccion = self.arbol_transiciones.selection()
        if not seleccion:
            messagebox.showinfo("Selección requerida", "Selecciona una fila de la tabla para eliminar.")
            return
        valores = self.arbol_transiciones.item(seleccion[0])['values']
        estado, simb_lectura = str(valores[0]), str(valores[1])
        if self.mt.eliminar_transicion(estado, simb_lectura):
            self.actualizar_tabla_transiciones()
            if hasattr(self, 'marco_interno_matriz'):
                self.reconstruir_cuadricula_matriz()
            self.recalcular_distribucion_grafo()
            self.barra_estado.config(text=f"Transición eliminada: ({estado}, {simb_lectura})")

    def limpiar_todas_las_transiciones(self):
        if messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar todas las transiciones?"):
            self.mt.limpiar_transiciones()
            self.actualizar_tabla_transiciones()
            if hasattr(self, 'marco_interno_matriz'):
                self.reconstruir_cuadricula_matriz()
            self.recalcular_distribucion_grafo()
            self.barra_estado.config(text="Todas las transiciones han sido eliminadas.")

    def validar_maquina(self):
        es_valido, mensajes = self.mt.validar()
        if es_valido and not mensajes:
            messagebox.showinfo("Validación Exitosa", "La Máquina de Turing está formalmente bien definida.")
        elif es_valido:
            observaciones = "\n- ".join(mensajes)
            messagebox.showwarning("Advertencias", f"La máquina es válida pero tiene observaciones:\n\n- {observaciones}")
        else:
            errores = "\n- ".join(mensajes)
            messagebox.showerror("Errores de Validación", f"Se encontraron errores formales:\n\n- {errores}")

    def guardar_en_json(self):
        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
            title="Guardar Máquina de Turing"
        )
        if ruta_archivo:
            try:
                with open(ruta_archivo, "w", encoding="utf-8") as f:
                    f.write(self.mt.a_json())
                messagebox.showinfo("Guardado", f"Máquina guardada con éxito en:\n{ruta_archivo}")
            except Exception as e:
                messagebox.showerror("Error al guardar", str(e))

    def cargar_desde_json(self):
        ruta_archivo = filedialog.askopenfilename(
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
            title="Cargar Máquina de Turing"
        )
        if ruta_archivo:
            try:
                with open(ruta_archivo, "r", encoding="utf-8") as f:
                    contenido = f.read()
                self.mt = MaquinaTuring.desde_json(contenido)
                self.cargar_maquina_en_interfaz()
                messagebox.showinfo("Cargado", f"Máquina cargada correctamente desde:\n{ruta_archivo}")
            except Exception as e:
                messagebox.showerror("Error al cargar", f"No se pudo procesar el archivo:\n{e}")

    def sim_cargar_palabra(self):
        if self.simulando:
            self.sim_alternar_reproduccion()

        palabra = self.entrada_sim_palabra.get().strip()
        self.mt.cargar_entrada(palabra)
        self.actualizar_vista_simulacion()
        self.barra_estado.config(text=f"Palabra '{palabra}' cargada.")

    def sim_reiniciar(self):
        self.sim_cargar_palabra()

    def sim_paso(self):
        if self.mt.detenida:
            return

        continua, mensaje = self.mt.ejecutar_paso()
        self.actualizar_vista_simulacion(mensaje)

        if not continua and self.simulando:
            self.sim_alternar_reproduccion()

    def sim_alternar_reproduccion(self):
        if self.simulando:
            self.simulando = False
            self.boton_reproducir.config(text="Ejecutar")
            if self.id_temporizador_simulacion:
                self.raiz.after_cancel(self.id_temporizador_simulacion)
                self.id_temporizador_simulacion = None
        else:
            if self.mt.detenida:
                self.sim_cargar_palabra()

            self.simulando = True
            self.boton_reproducir.config(text="Pausa")
            self.ejecutar_bucle_simulacion()

    def ejecutar_bucle_simulacion(self):
        if not self.simulando:
            return

        if not self.mt.detenida:
            self.sim_paso()
            demora = int(self.deslizador_velocidad.get())
            self.id_temporizador_simulacion = self.raiz.after(demora, self.ejecutar_bucle_simulacion)
        else:
            self.sim_alternar_reproduccion()

    def actualizar_vista_simulacion(self, mensaje_estado: Optional[str] = None):
        self.etiqueta_sim_estado_actual.config(text=f"Estado: {self.mt.estado_actual}")
        self.etiqueta_sim_pasos.config(text=f"Pasos: {self.mt.contador_pasos}")
        self.etiqueta_sim_pos_cabezal.config(text=f"Posición Cabezal: {self.mt.posicion_cabezal}")

        if self.mt.aceptada:
            self.etiqueta_estado_sim.config(
                text=f"Cadena ACEPTADA. Parada en estado '{self.mt.estado_actual}' ({self.mt.contador_pasos} pasos)",
                bg="#dcfce7", fg="#15803d"
            )
        elif self.mt.rechazada:
            self.etiqueta_estado_sim.config(
                text=f"Cadena RECHAZADA. Parada en estado '{self.mt.estado_actual}' ({self.mt.contador_pasos} pasos)",
                bg="#fee2e2", fg="#b91c1c"
            )
        else:
            mensaje = mensaje_estado or f"Simulando. Estado actual: {self.mt.estado_actual}"
            self.etiqueta_estado_sim.config(text=mensaje, bg="#e0f2fe", fg="#0369a1")

        self.dibujar_cinta()

        for elemento in self.arbol_registro.get_children():
            self.arbol_registro.delete(elemento)

        for reg in self.mt.historial:
            cadena_trans = ""
            if reg.nuevo_estado:
                cadena_trans = f"({reg.nuevo_estado}, '{reg.simbolo_escrito}', {reg.direccion.value if reg.direccion else ''})"
            elif reg.numero_paso == 0:
                cadena_trans = "(Inicio)"
            else:
                cadena_trans = "(Parada)"

            self.arbol_registro.insert("", tk.END, values=(
                reg.numero_paso,
                reg.estado_actual,
                reg.simbolo_leido,
                cadena_trans,
                reg.captura_cinta
            ))

        elementos = self.arbol_registro.get_children()
        if elementos:
            self.arbol_registro.see(elementos[-1])

        self.dibujar_grafo()

    def dibujar_cinta(self):
        self.lienzo_cinta.delete("all")
        ancho_lienzo = self.lienzo_cinta.winfo_width()
        if ancho_lienzo < 50:
            ancho_lienzo = 750
        alto_lienzo = 130

        ancho_celda = 48
        alto_celda = 50
        pos_y_celda = 35

        centro_x = ancho_lienzo / 2
        cabezal = self.mt.posicion_cabezal

        celdas_por_lado = int(ancho_lienzo / (2 * ancho_celda)) + 2
        celda_min = cabezal - celdas_por_lado
        celda_max = cabezal + celdas_por_lado

        for i in range(celda_min, celda_max + 1):
            x1 = centro_x + (i - cabezal) * ancho_celda - (ancho_celda / 2)
            x2 = x1 + ancho_celda
            y1 = pos_y_celda
            y2 = y1 + alto_celda

            es_cabezal = (i == cabezal)
            color_fondo = "#dbeafe" if es_cabezal else "#ffffff"
            color_borde = "#2563eb" if es_cabezal else "#cbd5e1"
            grosor_borde = 3 if es_cabezal else 1

            self.lienzo_cinta.create_rectangle(x1, y1, x2, y2, fill=color_fondo, outline=color_borde, width=grosor_borde)
            self.lienzo_cinta.create_text(x1 + ancho_celda / 2, y1 - 10, text=str(i), font=("Segoe UI", 8), fill="#64748b")

            simbolo = self.mt.obtener_simbolo_cinta(i)
            peso_fuente = "bold" if es_cabezal else "normal"
            color_texto = "#1e3a8a" if es_cabezal else "#0f172a"
            self.lienzo_cinta.create_text(x1 + ancho_celda / 2, y1 + alto_celda / 2, text=simbolo, font=("Consolas", 16, peso_fuente), fill=color_texto)

            if es_cabezal:
                y_flecha = y2 + 5
                self.lienzo_cinta.create_polygon(
                    centro_x, y_flecha,
                    centro_x - 9, y_flecha + 14,
                    centro_x + 9, y_flecha + 14,
                    fill="#2563eb", outline="#1d4ed8"
                )
                self.lienzo_cinta.create_text(centro_x, y_flecha + 26, text="CABEZAL", font=("Segoe UI", 8, "bold"), fill="#2563eb")

    def recalcular_distribucion_grafo(self):
        ancho = self.lienzo_grafo.winfo_width()
        alto = self.lienzo_grafo.winfo_height()
        if ancho < 50 or alto < 50:
            ancho, alto = 750, 500

        self._nodos_movidos = False
        lista_estados = sorted(list(self.mt.estados))
        self.posiciones_nodos = DistribucionGrafo.calcular_posiciones(
            estados=lista_estados,
            estado_inicial=self.mt.estado_inicial,
            ancho=ancho,
            alto=alto
        )
        self.dibujar_grafo()

    def dibujar_grafo(self):
        self.lienzo_grafo.delete("all")
        if not self.posiciones_nodos:
            return

        radio = 28.0

        aristas: Dict[Tuple[str, str], List[str]] = {}
        for clave, valor in self.mt.transiciones.items():
            par = (clave.estado, valor.nuevo_estado)
            etiqueta = f"{clave.simbolo}/{valor.simbolo_escrito},{valor.direccion.value}"
            aristas.setdefault(par, []).append(etiqueta)

        for (u, v), etiquetas in aristas.items():
            if u not in self.posiciones_nodos or v not in self.posiciones_nodos:
                continue

            x1, y1 = self.posiciones_nodos[u]
            x2, y2 = self.posiciones_nodos[v]
            texto_etiqueta = "\n".join(etiquetas)

            if u == v:
                alto_bucle = 55.0
                cx, cy = x1, y1 - radio
                self.lienzo_grafo.create_arc(
                    cx - 24, cy - alto_bucle, cx + 24, cy + 10,
                    start=20, extent=320, style=tk.ARC,
                    outline="#64748b", width=2
                )
                self.lienzo_grafo.create_line(
                    cx + 18, cy - 2, cx + 5, cy + 5,
                    arrow=tk.LAST, fill="#64748b", width=2
                )
                self.lienzo_grafo.create_text(cx, cy - alto_bucle - 10, text=texto_etiqueta, font=("Segoe UI", 8, "bold"), fill="#334155")
            else:
                dx = x2 - x1
                dy = y2 - y1
                dist = math.hypot(dx, dy)
                if dist == 0:
                    continue

                ux = dx / dist
                uy = dy / dist

                tiene_inversa = (v, u) in aristas
                desplazamiento = 24.0 if tiene_inversa else 0.0

                inicio_x = x1 + ux * radio - uy * desplazamiento * 0.4
                inicio_y = y1 + uy * radio + ux * desplazamiento * 0.4
                fin_x = x2 - ux * radio - uy * desplazamiento * 0.4
                fin_y = y2 - uy * radio + ux * desplazamiento * 0.4

                medio_x = (inicio_x + fin_x) / 2 - uy * desplazamiento
                medio_y = (inicio_y + fin_y) / 2 + ux * desplazamiento

                self.lienzo_grafo.create_line(
                    inicio_x, inicio_y, medio_x, medio_y, fin_x, fin_y,
                    smooth=True, arrow=tk.LAST, arrowshape=(12, 14, 5),
                    fill="#64748b", width=2
                )

                etiqueta_x = medio_x - uy * 10
                etiqueta_y = medio_y + ux * 10
                self.lienzo_grafo.create_text(
                    etiqueta_x, etiqueta_y,
                    text=texto_etiqueta,
                    font=("Segoe UI", 8, "bold"),
                    fill="#1e293b"
                )

        for estado, (x, y) in self.posiciones_nodos.items():
            es_inicio = (estado == self.mt.estado_inicial)
            es_aceptacion = (estado in self.mt.estados_aceptacion)
            es_rechazo = (estado in self.mt.estados_rechazo)
            es_actual = (estado == self.mt.estado_actual)

            if es_actual:
                fondo = "#fef08a"
                borde = "#ca8a04"
                grosor_borde = 4
            elif es_aceptacion:
                fondo = "#dcfce7"
                borde = "#16a34a"
                grosor_borde = 3
            elif es_rechazo:
                fondo = "#fee2e2"
                borde = "#dc2626"
                grosor_borde = 3
            else:
                fondo = "#eff6ff"
                borde = "#2563eb"
                grosor_borde = 2

            self.lienzo_grafo.create_oval(
                x - radio, y - radio, x + radio, y + radio,
                fill=fondo, outline=borde, width=grosor_borde, tags=("node", estado)
            )

            if es_aceptacion:
                self.lienzo_grafo.create_oval(
                    x - (radio - 5), y - (radio - 5), x + (radio - 5), y + (radio - 5),
                    outline=borde, width=2, tags=("node", estado)
                )

            if es_inicio:
                self.lienzo_grafo.create_line(
                    x - radio - 30, y, x - radio, y,
                    arrow=tk.LAST, fill="#0f172a", width=3
                )
                self.lienzo_grafo.create_text(x - radio - 45, y, text="Inicio", font=("Segoe UI", 8, "bold"), fill="#0f172a")

            estilo_fuente = ("Segoe UI", 10, "bold") if es_actual else ("Segoe UI", 10)
            self.lienzo_grafo.create_text(x, y, text=estado, font=estilo_fuente, fill="#0f172a", tags=("node", estado))

    def al_hacer_clic_grafo(self, evento):
        pos_x, pos_y = evento.x, evento.y
        radio = 30.0
        for estado, (nx, ny) in self.posiciones_nodos.items():
            if math.hypot(pos_x - nx, pos_y - ny) <= radio:
                self.nodo_arrastrado = estado
                self.desplazamiento_arrastre_x = nx - pos_x
                self.desplazamiento_arrastre_y = ny - pos_y
                return

    def al_arrastrar_grafo(self, evento):
        if self.nodo_arrastrado and self.nodo_arrastrado in self.posiciones_nodos:
            nuevo_x = evento.x + self.desplazamiento_arrastre_x
            nuevo_y = evento.y + self.desplazamiento_arrastre_y
            self.posiciones_nodos[self.nodo_arrastrado] = (nuevo_x, nuevo_y)
            self._nodos_movidos = True
            self.dibujar_grafo()

    def al_soltar_grafo(self, evento):
        self.nodo_arrastrado = None
