import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.scrolledtext as scrolledtext
import math
import os
from typing import Dict, Tuple, List, Optional

from turing_machine import TuringMachine, Direction, TransitionKey
from graph_renderer import GraphLayout
from examples_data import AVAILABLE_EXAMPLES


class TuringMachineGUI:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Simulador y Diseñador de Máquinas de Turing")
        self.root.geometry("1100x750")
        self.root.minsize(950, 650)

        self.setup_styles()

        self.tm: TuringMachine = AVAILABLE_EXAMPLES["a^n b^n (n >= 1)"]()

        self.node_positions: Dict[str, Tuple[float, float]] = {}
        self.drag_node: Optional[str] = None
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0

        self.is_simulating = False
        self.sim_after_id = None

        self.matrix_entries: Dict[Tuple[str, str], ttk.Entry] = {}

        self.build_ui()
        self.load_machine_into_ui()

    def setup_styles(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 6])
        self.style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), foreground="#ffffff", background="#2563eb")
        self.style.configure("Success.TButton", font=("Segoe UI", 9, "bold"), foreground="#ffffff", background="#16a34a")
        self.style.configure("Danger.TButton", font=("Segoe UI", 9, "bold"), foreground="#ffffff", background="#dc2626")
        try:
            self.style.map("Success.TButton",
                foreground=[('pressed', '#ffffff'), ('active', '#ffffff')],
                background=[('pressed', '#15803d'), ('active', '#22c55e')]
            )
            self.style.map("Accent.TButton",
                foreground=[('pressed', '#ffffff'), ('active', '#ffffff')],
                background=[('pressed', '#1d4ed8'), ('active', '#3b82f6')]
            )
        except Exception:
            pass

    def build_ui(self):
        top_bar = ttk.Frame(self.root, padding="10 8")
        top_bar.pack(fill=tk.X)

        ttk.Label(top_bar, text="Máquina de Turing:", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.lbl_machine_title = ttk.Label(top_bar, text=self.tm.name, font=("Segoe UI", 11, "italic"), foreground="#2563eb")
        self.lbl_machine_title.pack(side=tk.LEFT, padx=(0, 15))

        btn_new_machine = ttk.Button(top_bar, text="Nuevo en Blanco", command=self.new_blank_machine)
        btn_new_machine.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(top_bar, text="Cargar Ejemplo:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(5, 4))
        self.combo_examples = ttk.Combobox(top_bar, values=["[En blanco]"] + list(AVAILABLE_EXAMPLES.keys()), state="readonly", width=24)
        self.combo_examples.set("a^n b^n (n >= 1)")
        self.combo_examples.pack(side=tk.LEFT, padx=(0, 10))
        self.combo_examples.bind("<<ComboboxSelected>>", self.on_example_selected)

        btn_save_json = ttk.Button(top_bar, text="Guardar JSON", command=self.save_to_json)
        btn_save_json.pack(side=tk.RIGHT, padx=4)

        btn_load_json = ttk.Button(top_bar, text="Cargar JSON", command=self.load_from_json)
        btn_load_json.pack(side=tk.RIGHT, padx=4)

        btn_generate_top = ttk.Button(top_bar, text="Generar Autómata", style="Success.TButton", command=self.generate_automaton_action)
        btn_generate_top.pack(side=tk.RIGHT, padx=6)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        self.tab_definition = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_definition, text="1. Definición y Transiciones")
        self.build_definition_tab()

        self.tab_simulation = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_simulation, text="2. Simulador de Cinta")
        self.build_simulation_tab()

        self.tab_graph = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_graph, text="3. Diagrama del Autómata")
        self.build_graph_tab()

        self.status_bar = ttk.Label(self.root, text="Listo.", relief=tk.SUNKEN, anchor=tk.W, padding=(8, 4))
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def build_definition_tab(self):
        left_pane = ttk.LabelFrame(self.tab_definition, text="Formalismo M = (Q, Σ, Γ, δ, q0, B, F)", padding=10)
        left_pane.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Label(left_pane, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.entry_name = ttk.Entry(left_pane, width=32)
        self.entry_name.grid(row=0, column=1, sticky=tk.W, pady=3)

        ttk.Label(left_pane, text="Alfabeto Entrada Σ:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.entry_sigma = ttk.Entry(left_pane, width=32)
        self.entry_sigma.grid(row=1, column=1, sticky=tk.W, pady=3)

        ttk.Label(left_pane, text="Símbolo Blanco (B):").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.entry_blank = ttk.Entry(left_pane, width=10)
        self.entry_blank.grid(row=2, column=1, sticky=tk.W, pady=3)

        ttk.Label(left_pane, text="Alfabeto Cinta Γ:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.entry_gamma = ttk.Entry(left_pane, width=32)
        self.entry_gamma.grid(row=3, column=1, sticky=tk.W, pady=3)

        ttk.Label(left_pane, text="Estados Q:").grid(row=4, column=0, sticky=tk.W, pady=3)
        self.entry_states = ttk.Entry(left_pane, width=32)
        self.entry_states.grid(row=4, column=1, sticky=tk.W, pady=3)

        ttk.Label(left_pane, text="Estado Inicial (q0):").grid(row=5, column=0, sticky=tk.W, pady=3)
        self.entry_init_state = ttk.Entry(left_pane, width=15)
        self.entry_init_state.grid(row=5, column=1, sticky=tk.W, pady=3)

        ttk.Label(left_pane, text="Estados Aceptación (F):").grid(row=6, column=0, sticky=tk.W, pady=3)
        self.entry_accept_states = ttk.Entry(left_pane, width=32)
        self.entry_accept_states.grid(row=6, column=1, sticky=tk.W, pady=3)

        ttk.Label(left_pane, text="Estados Rechazo:").grid(row=7, column=0, sticky=tk.W, pady=3)
        self.entry_reject_states = ttk.Entry(left_pane, width=32)
        self.entry_reject_states.grid(row=7, column=1, sticky=tk.W, pady=3)

        btn_apply_def = ttk.Button(left_pane, text="Actualizar Parámetros", command=self.apply_definition_inputs)
        btn_apply_def.grid(row=8, column=0, columnspan=2, pady=(14, 4), sticky=tk.EW)

        btn_regen_from_left = ttk.Button(left_pane, text="Reconstruir Cuadrícula", command=self.rebuild_matrix_grid)
        btn_regen_from_left.grid(row=9, column=0, columnspan=2, pady=4, sticky=tk.EW)

        btn_validate = ttk.Button(left_pane, text="Validar Autómata", command=self.validate_machine)
        btn_validate.grid(row=10, column=0, columnspan=2, pady=4, sticky=tk.EW)

        btn_gen_left = ttk.Button(left_pane, text="Generar Autómata", style="Success.TButton", command=self.generate_automaton_action)
        btn_gen_left.grid(row=11, column=0, columnspan=2, pady=(12, 4), sticky=tk.EW)

        right_pane = ttk.LabelFrame(self.tab_definition, text="Función y Tabla de Transiciones δ", padding=8)
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        trans_toolbar = ttk.Frame(right_pane)
        trans_toolbar.pack(fill=tk.X, pady=(0, 6))

        btn_gen_main = ttk.Button(trans_toolbar, text="Generar Autómata", style="Success.TButton", command=self.generate_automaton_action)
        btn_gen_main.pack(side=tk.LEFT, padx=(0, 6))

        btn_regen_grid = ttk.Button(trans_toolbar, text="Regenerar Cuadrícula", command=self.rebuild_matrix_grid)
        btn_regen_grid.pack(side=tk.LEFT, padx=4)

        btn_export_csv = ttk.Button(trans_toolbar, text="Exportar Tabla a CSV", command=self.export_matrix_to_csv)
        btn_export_csv.pack(side=tk.LEFT, padx=4)

        self.lbl_trans_count = ttk.Label(trans_toolbar, text="Total: 0 transiciones", font=("Segoe UI", 9, "italic"))
        self.lbl_trans_count.pack(side=tk.RIGHT, padx=4)

        self.trans_notebook = ttk.Notebook(right_pane)
        self.trans_notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_matrix = ttk.Frame(self.trans_notebook, padding=6)
        self.trans_notebook.add(self.tab_matrix, text="Matriz 2D")
        self.build_matrix_tab()

        self.tab_text_import = ttk.Frame(self.trans_notebook, padding=6)
        self.trans_notebook.add(self.tab_text_import, text="Pegar / Importar Texto")
        self.build_text_import_tab()

        self.tab_list = ttk.Frame(self.trans_notebook, padding=6)
        self.trans_notebook.add(self.tab_list, text="Vista en Lista")
        self.build_list_tab()

    def build_matrix_tab(self):
        grid_container = ttk.Frame(self.tab_matrix)
        grid_container.pack(fill=tk.BOTH, expand=True)

        self.matrix_canvas = tk.Canvas(grid_container, bg="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        v_scroll = ttk.Scrollbar(grid_container, orient=tk.VERTICAL, command=self.matrix_canvas.yview)
        h_scroll = ttk.Scrollbar(grid_container, orient=tk.HORIZONTAL, command=self.matrix_canvas.xview)

        self.matrix_inner_frame = ttk.Frame(self.matrix_canvas)
        self.matrix_inner_frame.bind(
            "<Configure>",
            lambda e: self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all"))
        )
        self.matrix_window_id = self.matrix_canvas.create_window((0, 0), window=self.matrix_inner_frame, anchor="nw")

        self.matrix_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        self.matrix_canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        grid_container.grid_rowconfigure(0, weight=1)
        grid_container.grid_columnconfigure(0, weight=1)

        matrix_bottom = ttk.Frame(self.tab_matrix)
        matrix_bottom.pack(fill=tk.X, pady=(6, 0))

        btn_apply_matrix = ttk.Button(matrix_bottom, text="Guardar Cambios de la Matriz", command=self.apply_matrix_changes)
        btn_apply_matrix.pack(side=tk.LEFT, padx=4)

        btn_gen_from_matrix = ttk.Button(matrix_bottom, text="Generar Autómata", style="Accent.TButton", command=self.generate_automaton_action)
        btn_gen_from_matrix.pack(side=tk.LEFT, padx=4)

        btn_clear_matrix = ttk.Button(matrix_bottom, text="Limpiar Celdas", command=self.clear_matrix_cells)
        btn_clear_matrix.pack(side=tk.RIGHT, padx=4)

    def rebuild_matrix_grid(self):
        for widget in self.matrix_inner_frame.winfo_children():
            widget.destroy()

        self.matrix_entries = {}

        raw_states_str = self.entry_states.get().strip() if hasattr(self, 'entry_states') else ""
        if raw_states_str:
            states_list = [s.strip() for s in raw_states_str.split(",") if s.strip()]
        else:
            states_list = sorted(list(self.tm.states))

        init_st = self.entry_init_state.get().strip() or self.tm.initial_state
        if init_st in states_list:
            states_list.remove(init_st)
            states_list = [init_st] + states_list
        elif init_st:
            states_list = [init_st] + states_list

        raw_sigma_str = self.entry_sigma.get().strip() if hasattr(self, 'entry_sigma') else ""
        raw_gamma_str = self.entry_gamma.get().strip() if hasattr(self, 'entry_gamma') else ""
        blank = self.entry_blank.get().strip() if hasattr(self, 'entry_blank') else self.tm.blank_symbol

        sigma_symbols = [s.strip() for s in raw_sigma_str.split(",") if s.strip()] if raw_sigma_str else sorted(list(self.tm.input_alphabet))
        gamma_symbols = [s.strip() for s in raw_gamma_str.split(",") if s.strip()] if raw_gamma_str else sorted(list(self.tm.tape_alphabet))

        symbols_list = []
        for s in sigma_symbols:
            if s not in symbols_list and s != blank:
                symbols_list.append(s)
        for s in gamma_symbols:
            if s not in symbols_list and s != blank:
                symbols_list.append(s)
        if blank and blank not in symbols_list:
            symbols_list.append(blank)

        if not symbols_list:
            symbols_list = ["0", "1", "B"]

        lbl_corner = tk.Label(
            self.matrix_inner_frame,
            text="Estado \\ Símbolo",
            font=("Segoe UI", 9, "bold"),
            bg="#e2e8f0",
            fg="#1e293b",
            padx=10,
            pady=6,
            relief=tk.RIDGE
        )
        lbl_corner.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        for col_idx, sym in enumerate(symbols_list, start=1):
            lbl_sym = tk.Label(
                self.matrix_inner_frame,
                text=f"'{sym}'",
                font=("Consolas", 10, "bold"),
                bg="#f1f5f9",
                fg="#2563eb" if sym in sigma_symbols else "#475569",
                padx=8,
                pady=6,
                relief=tk.RIDGE,
                width=16
            )
            lbl_sym.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)

        accept_states = {s.strip() for s in self.entry_accept_states.get().split(",") if s.strip()} if hasattr(self, 'entry_accept_states') else self.tm.accept_states
        reject_states = {s.strip() for s in self.entry_reject_states.get().split(",") if s.strip()} if hasattr(self, 'entry_reject_states') else self.tm.reject_states

        for row_idx, st in enumerate(states_list, start=1):
            bg_st = "#f8fafc"
            fg_st = "#0f172a"
            if st == init_st:
                bg_st = "#e0f2fe"
                fg_st = "#0369a1"
            elif st in accept_states:
                bg_st = "#dcfce7"
                fg_st = "#15803d"
            elif st in reject_states:
                bg_st = "#fee2e2"
                fg_st = "#b91c1c"

            lbl_st = tk.Label(
                self.matrix_inner_frame,
                text=st,
                font=("Segoe UI", 9, "bold"),
                bg=bg_st,
                fg=fg_st,
                padx=8,
                pady=4,
                relief=tk.RIDGE,
                anchor="center",
                width=12
            )
            lbl_st.grid(row=row_idx, column=0, sticky="nsew", padx=1, pady=1)

            for col_idx, sym in enumerate(symbols_list, start=1):
                ent = ttk.Entry(self.matrix_inner_frame, font=("Consolas", 9), width=16, justify=tk.CENTER)
                ent.grid(row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)

                key = TransitionKey(st, sym)
                if key in self.tm.transitions:
                    val = self.tm.transitions[key]
                    ent.insert(0, f"({val.next_state}, {val.write_symbol}, {val.direction.value})")

                self.matrix_entries[(st, sym)] = ent

        self.matrix_inner_frame.update_idletasks()
        self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all"))

    def apply_matrix_changes(self, show_msg: bool = True) -> bool:
        if not hasattr(self, 'matrix_entries') or not self.matrix_entries:
            return True

        matrix_dict = {}
        for (st, sym), ent in self.matrix_entries.items():
            val = ent.get().strip()
            if val:
                matrix_dict[(st, sym)] = val

        added, errors = self.tm.set_matrix_transitions(matrix_dict, clear_existing=True)
        self.refresh_transitions_table()
        self.recalculate_graph_layout()

        if errors:
            err_text = "\n".join(errors[:5])
            if len(errors) > 5:
                err_text += f"\n...y {len(errors) - 5} advertencias más."
            messagebox.showwarning("Advertencias en Celdas", f"Se aplicaron {added} transiciones, pero hubo observaciones:\n\n{err_text}")
            return False

        if show_msg:
            messagebox.showinfo("Matriz Aplicada", f"Se actualizaron exitosamente {added} transiciones.")
        self.status_bar.config(text=f"Matriz actualizada: {added} transiciones.")
        return True

    def clear_matrix_cells(self):
        if messagebox.askyesno("Confirmar Limpieza", "¿Deseas borrar el contenido de todas las celdas de la matriz?"):
            for ent in self.matrix_entries.values():
                ent.delete(0, tk.END)

    def build_text_import_tab(self):
        top_ctrl = ttk.Frame(self.tab_text_import)
        top_ctrl.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(top_ctrl, text="Tabla de transiciones (CSV o lista):", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        btn_template_csv = ttk.Button(top_ctrl, text="Plantilla Matriz CSV", command=self.insert_csv_template)
        btn_template_csv.pack(side=tk.RIGHT, padx=4)

        btn_template_list = ttk.Button(top_ctrl, text="Plantilla Lista", command=self.insert_list_template)
        btn_template_list.pack(side=tk.RIGHT, padx=4)

        btn_file_load = ttk.Button(top_ctrl, text="Cargar Archivo", command=self.load_text_file)
        btn_file_load.pack(side=tk.RIGHT, padx=4)

        self.txt_bulk_import = scrolledtext.ScrolledText(self.tab_text_import, height=12, font=("Consolas", 10), wrap=tk.NONE)
        self.txt_bulk_import.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        bottom_ctrl = ttk.Frame(self.tab_text_import)
        bottom_ctrl.pack(fill=tk.X)

        btn_process = ttk.Button(bottom_ctrl, text="Procesar Texto", command=self.process_text_import)
        btn_process.pack(side=tk.LEFT, padx=4)

        btn_process_and_gen = ttk.Button(bottom_ctrl, text="Procesar y Generar", style="Success.TButton", command=self.generate_from_text_action)
        btn_process_and_gen.pack(side=tk.LEFT, padx=4)

        btn_clear_text = ttk.Button(bottom_ctrl, text="Limpiar Texto", command=lambda: self.txt_bulk_import.delete("1.0", tk.END))
        btn_clear_text.pack(side=tk.RIGHT, padx=4)

    def insert_csv_template(self):
        sample = (
            "Estado, 0, 1, B\n"
            "q0, (q0, 0, R), (q0, 1, R), (q1, B, L)\n"
            "q1, (q_accept, 1, S), (q1, 0, L), (q_accept, 1, S)\n"
            "q_accept, , , \n"
        )
        self.txt_bulk_import.delete("1.0", tk.END)
        self.txt_bulk_import.insert(tk.END, sample)

    def insert_list_template(self):
        sample = (
            "q0 0 q0 0 R\n"
            "q0 1 q0 1 R\n"
            "q0 B q1 B L\n"
            "q1 0 q_accept 1 S\n"
            "q1 1 q1 0 L\n"
            "q1 B q_accept 1 S\n"
        )
        self.txt_bulk_import.delete("1.0", tk.END)
        self.txt_bulk_import.insert(tk.END, sample)

    def load_text_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Archivos CSV y Texto", "*.csv;*.txt"), ("Archivos CSV", "*.csv"), ("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")],
            title="Cargar Tabla de Transiciones"
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.txt_bulk_import.delete("1.0", tk.END)
                self.txt_bulk_import.insert(tk.END, content)
                self.status_bar.config(text=f"Archivo cargado: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error al leer archivo", str(e))

    def process_text_import(self, show_msg: bool = True) -> bool:
        raw_text = self.txt_bulk_import.get("1.0", tk.END).strip()
        if not raw_text:
            if show_msg:
                messagebox.showwarning("Texto Vacío", "Por favor escribe o pega la tabla de transiciones antes de procesar.")
            return False

        ok, msg, count = self.tm.import_from_text(raw_text, clear_existing=True)
        if not ok:
            messagebox.showerror("Error al Procesar Transiciones", msg)
            return False

        if hasattr(self, 'entry_states'):
            self.entry_states.delete(0, tk.END)
            self.entry_states.insert(0, ", ".join(sorted(list(self.tm.states))))

        self.entry_gamma.delete(0, tk.END)
        self.entry_gamma.insert(0, ", ".join(sorted(list(self.tm.tape_alphabet))))

        self.refresh_transitions_table()
        self.rebuild_matrix_grid()
        self.recalculate_graph_layout()

        if show_msg:
            messagebox.showinfo("Procesamiento Exitoso", msg)
        self.status_bar.config(text=msg)
        return True

    def generate_from_text_action(self):
        if self.process_text_import(show_msg=False):
            self.generate_automaton_action()

    def export_matrix_to_csv(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            title="Exportar Tabla de Transiciones como CSV"
        )
        if not filepath:
            return
        try:
            csv_str = self.tm.to_csv()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(csv_str)
            messagebox.showinfo("Exportación Exitosa", f"Tabla de transiciones exportada a:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error al Exportar", f"No se pudo guardar el archivo: {e}")

    def build_list_tab(self):
        add_frame = ttk.Frame(self.tab_list)
        add_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(add_frame, text="Estado:").grid(row=0, column=0, padx=2)
        self.entry_t_state = ttk.Entry(add_frame, width=8)
        self.entry_t_state.grid(row=0, column=1, padx=2)

        ttk.Label(add_frame, text="Lee:").grid(row=0, column=2, padx=2)
        self.entry_t_read = ttk.Entry(add_frame, width=5)
        self.entry_t_read.grid(row=0, column=3, padx=2)

        ttk.Label(add_frame, text="Nuevo Est:").grid(row=0, column=4, padx=2)
        self.entry_t_next = ttk.Entry(add_frame, width=8)
        self.entry_t_next.grid(row=0, column=5, padx=2)

        ttk.Label(add_frame, text="Escribe:").grid(row=0, column=6, padx=2)
        self.entry_t_write = ttk.Entry(add_frame, width=5)
        self.entry_t_write.grid(row=0, column=7, padx=2)

        ttk.Label(add_frame, text="Dir:").grid(row=0, column=8, padx=2)
        self.combo_t_dir = ttk.Combobox(add_frame, values=["R", "L", "S"], width=5, state="readonly")
        self.combo_t_dir.set("R")
        self.combo_t_dir.grid(row=0, column=9, padx=2)

        btn_add_trans = ttk.Button(add_frame, text="Agregar / Modificar", command=self.add_transition_from_inputs)
        btn_add_trans.grid(row=0, column=10, padx=(8, 2))

        table_container = ttk.Frame(self.tab_list)
        table_container.pack(fill=tk.BOTH, expand=True)

        columns = ("state", "read", "next", "write", "dir")
        self.tree_transitions = ttk.Treeview(table_container, columns=columns, show="headings", selectmode="browse")
        self.tree_transitions.heading("state", text="Estado Origen")
        self.tree_transitions.heading("read", text="Símbolo Leído")
        self.tree_transitions.heading("next", text="Nuevo Estado")
        self.tree_transitions.heading("write", text="Símbolo Escrito")
        self.tree_transitions.heading("dir", text="Dirección")

        self.tree_transitions.column("state", width=120, anchor=tk.CENTER)
        self.tree_transitions.column("read", width=110, anchor=tk.CENTER)
        self.tree_transitions.column("next", width=120, anchor=tk.CENTER)
        self.tree_transitions.column("write", width=110, anchor=tk.CENTER)
        self.tree_transitions.column("dir", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree_transitions.yview)
        self.tree_transitions.configure(yscroll=scrollbar.set)
        self.tree_transitions.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_transitions.bind("<<TreeviewSelect>>", self.on_transition_row_selected)

        table_btn_frame = ttk.Frame(self.tab_list)
        table_btn_frame.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(table_btn_frame, text="Eliminar Seleccionada", command=self.delete_selected_transition).pack(side=tk.LEFT, padx=4)
        ttk.Button(table_btn_frame, text="Limpiar Transiciones", command=self.clear_all_transitions).pack(side=tk.LEFT, padx=4)
        self.lbl_trans_count = ttk.Label(table_btn_frame, text="Total: 0 transiciones", font=("Segoe UI", 9, "italic"))
        self.lbl_trans_count.pack(side=tk.RIGHT, padx=4)

    def build_simulation_tab(self):
        top_ctrl = ttk.LabelFrame(self.tab_simulation, text="Entrada y Control de Ejecución", padding=10)
        top_ctrl.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_ctrl, text="Cadena de Entrada:").pack(side=tk.LEFT, padx=(0, 6))
        self.entry_sim_word = ttk.Entry(top_ctrl, width=28, font=("Consolas", 11))
        self.entry_sim_word.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_sim_word.insert(0, "aabb")

        btn_load_word = ttk.Button(top_ctrl, text="Cargar Palabra", command=self.sim_load_word)
        btn_load_word.pack(side=tk.LEFT, padx=4)

        self.btn_step = ttk.Button(top_ctrl, text="Paso a Paso", command=self.sim_step)
        self.btn_step.pack(side=tk.LEFT, padx=4)

        self.btn_play = ttk.Button(top_ctrl, text="Ejecutar", command=self.sim_toggle_play)
        self.btn_play.pack(side=tk.LEFT, padx=4)

        btn_reset = ttk.Button(top_ctrl, text="Reiniciar", command=self.sim_reset)
        btn_reset.pack(side=tk.LEFT, padx=4)

        ttk.Label(top_ctrl, text="Velocidad:").pack(side=tk.LEFT, padx=(15, 4))
        self.speed_slider = tk.Scale(top_ctrl, from_=50, to=1000, orient=tk.HORIZONTAL, length=120, showvalue=False)
        self.speed_slider.set(300)
        self.speed_slider.pack(side=tk.LEFT, padx=2)
        ttk.Label(top_ctrl, text="ms", font=("Segoe UI", 8)).pack(side=tk.LEFT)

        self.lbl_sim_status = tk.Label(
            self.tab_simulation,
            text="Listo para simular.",
            font=("Segoe UI", 11, "bold"),
            bg="#e0f2fe",
            fg="#0369a1",
            padx=10,
            pady=6,
            relief=tk.GROOVE
        )
        self.lbl_sim_status.pack(fill=tk.X, pady=(0, 10))

        tape_frame = ttk.LabelFrame(self.tab_simulation, text="Visualización de la Cinta", padding=5)
        tape_frame.pack(fill=tk.X, pady=(0, 10))

        self.tape_canvas = tk.Canvas(tape_frame, height=130, bg="#f8fafc", highlightthickness=1, highlightbackground="#cbd5e1")
        self.tape_canvas.pack(fill=tk.X, expand=True)

        info_frame = ttk.Frame(self.tab_simulation)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_sim_cur_state = ttk.Label(info_frame, text="Estado: q0", font=("Segoe UI", 10, "bold"))
        self.lbl_sim_cur_state.pack(side=tk.LEFT, padx=15)

        self.lbl_sim_steps = ttk.Label(info_frame, text="Pasos: 0", font=("Segoe UI", 10))
        self.lbl_sim_steps.pack(side=tk.LEFT, padx=15)

        self.lbl_sim_head_pos = ttk.Label(info_frame, text="Posición Cabezal: 0", font=("Segoe UI", 10))
        self.lbl_sim_head_pos.pack(side=tk.LEFT, padx=15)

        log_frame = ttk.LabelFrame(self.tab_simulation, text="Historial de Pasos", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)

        log_cols = ("step", "state", "read", "trans", "tape")
        self.tree_log = ttk.Treeview(log_frame, columns=log_cols, show="headings")
        self.tree_log.heading("step", text="Paso")
        self.tree_log.heading("state", text="Estado")
        self.tree_log.heading("read", text="Leído")
        self.tree_log.heading("trans", text="Transición Aplicada")
        self.tree_log.heading("tape", text="Instantánea de Cinta [Cabezal]")

        self.tree_log.column("step", width=60, anchor=tk.CENTER)
        self.tree_log.column("state", width=90, anchor=tk.CENTER)
        self.tree_log.column("read", width=70, anchor=tk.CENTER)
        self.tree_log.column("trans", width=200, anchor=tk.W)
        self.tree_log.column("tape", width=500, anchor=tk.W)

        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.tree_log.yview)
        self.tree_log.configure(yscroll=log_scroll.set)
        self.tree_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def build_graph_tab(self):
        graph_top = ttk.Frame(self.tab_graph)
        graph_top.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(graph_top, text="Grafo de Estados y Transiciones:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        btn_recalc = ttk.Button(graph_top, text="Reorganizar Nodos", command=self.recalculate_graph_layout)
        btn_recalc.pack(side=tk.RIGHT, padx=4)

        self.graph_canvas = tk.Canvas(self.tab_graph, bg="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        self.graph_canvas.pack(fill=tk.BOTH, expand=True)

        self.graph_canvas.bind("<ButtonPress-1>", self.on_graph_click)
        self.graph_canvas.bind("<B1-Motion>", self.on_graph_drag)
        self.graph_canvas.bind("<ButtonRelease-1>", self.on_graph_release)
        self.graph_canvas.bind("<Configure>", lambda e: self.draw_graph())

    def new_blank_machine(self):
        self.tm = TuringMachine(
            name="Nuevo Autómata",
            states={"q0"},
            input_alphabet=set(),
            tape_alphabet={"B"},
            blank_symbol="B",
            initial_state="q0",
            accept_states=set(),
            reject_states=set()
        )
        self.lbl_machine_title.config(text=self.tm.name)
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, self.tm.name)

        self.entry_sigma.delete(0, tk.END)
        self.entry_blank.delete(0, tk.END)
        self.entry_blank.insert(0, "B")
        self.entry_gamma.delete(0, tk.END)
        self.entry_gamma.insert(0, "B")
        self.entry_states.delete(0, tk.END)
        self.entry_states.insert(0, "q0")
        self.entry_init_state.delete(0, tk.END)
        self.entry_init_state.insert(0, "q0")
        self.entry_accept_states.delete(0, tk.END)
        self.entry_reject_states.delete(0, tk.END)
        self.entry_sim_word.delete(0, tk.END)
        if hasattr(self, 'txt_bulk_import'):
            self.txt_bulk_import.delete("1.0", tk.END)

        self.combo_examples.set("[En blanco]")
        self.refresh_transitions_table()
        if hasattr(self, 'matrix_inner_frame'):
            self.rebuild_matrix_grid()
        self.recalculate_graph_layout()
        self.sim_load_word()
        self.status_bar.config(text="Autómata en blanco listo para definir.")

    def load_machine_into_ui(self):
        self.lbl_machine_title.config(text=self.tm.name)
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, self.tm.name)

        self.entry_sigma.delete(0, tk.END)
        self.entry_sigma.insert(0, ", ".join(sorted(list(self.tm.input_alphabet))))

        self.entry_blank.delete(0, tk.END)
        self.entry_blank.insert(0, self.tm.blank_symbol)

        self.entry_gamma.delete(0, tk.END)
        self.entry_gamma.insert(0, ", ".join(sorted(list(self.tm.tape_alphabet))))

        self.entry_init_state.delete(0, tk.END)
        self.entry_init_state.insert(0, self.tm.initial_state)

        self.entry_accept_states.delete(0, tk.END)
        self.entry_accept_states.insert(0, ", ".join(sorted(list(self.tm.accept_states))))

        self.entry_reject_states.delete(0, tk.END)
        self.entry_reject_states.insert(0, ", ".join(sorted(list(self.tm.reject_states))))

        if hasattr(self, 'entry_states'):
            self.entry_states.delete(0, tk.END)
            self.entry_states.insert(0, ", ".join(sorted(list(self.tm.states))))

        self.refresh_transitions_table()
        if hasattr(self, 'matrix_inner_frame'):
            self.rebuild_matrix_grid()
        self.recalculate_graph_layout()
        self.sim_load_word()

    def refresh_transitions_table(self):
        for item in self.tree_transitions.get_children():
            self.tree_transitions.delete(item)

        sorted_keys = sorted(self.tm.transitions.keys(), key=lambda k: (k.state, k.symbol))
        for key in sorted_keys:
            val = self.tm.transitions[key]
            self.tree_transitions.insert("", tk.END, values=(key.state, key.symbol, val.next_state, val.write_symbol, val.direction.value))

        self.lbl_trans_count.config(text=f"Total: {len(self.tm.transitions)} transiciones")

    def on_example_selected(self, event=None):
        name = self.combo_examples.get()
        if name == "[En blanco]":
            self.new_blank_machine()
            return
        if name in AVAILABLE_EXAMPLES:
            self.tm = AVAILABLE_EXAMPLES[name]()
            if "a^n b^n" in name:
                self.entry_sim_word.delete(0, tk.END)
                self.entry_sim_word.insert(0, "aabb")
            elif "Incrementador" in name:
                self.entry_sim_word.delete(0, tk.END)
                self.entry_sim_word.insert(0, "1011")
            elif "Palíndromos" in name:
                self.entry_sim_word.delete(0, tk.END)
                self.entry_sim_word.insert(0, "abba")
            elif "Inversor" in name:
                self.entry_sim_word.delete(0, tk.END)
                self.entry_sim_word.insert(0, "11010")

            self.load_machine_into_ui()
            self.status_bar.config(text=f"Ejemplo '{name}' cargado.")

    def _apply_definition_data(self):
        name = self.entry_name.get().strip() or "Máquina de Turing"
        blank = self.entry_blank.get().strip() or "B"

        def parse_set(text: str) -> set:
            return {part.strip() for part in text.split(",") if part.strip()}

        sigma = parse_set(self.entry_sigma.get())
        gamma = parse_set(self.entry_gamma.get())
        states_declared = parse_set(self.entry_states.get()) if hasattr(self, 'entry_states') else set()
        init_state = self.entry_init_state.get().strip() or "q0"
        accept = parse_set(self.entry_accept_states.get())
        reject = parse_set(self.entry_reject_states.get())

        self.tm.name = name
        self.tm.blank_symbol = blank
        self.tm.input_alphabet = sigma
        self.tm.tape_alphabet = gamma
        self.tm.initial_state = init_state
        self.tm.accept_states = accept
        self.tm.reject_states = reject

        self.tm.tape_alphabet.add(blank)
        self.tm.tape_alphabet.update(sigma)
        self.tm.states.update(states_declared)
        self.tm.states.add(init_state)
        self.tm.states.update(accept)
        self.tm.states.update(reject)

        self.lbl_machine_title.config(text=self.tm.name)

    def apply_definition_inputs(self):
        self._apply_definition_data()
        if hasattr(self, 'matrix_inner_frame'):
            self.rebuild_matrix_grid()
        self.recalculate_graph_layout()
        messagebox.showinfo("Parámetros Actualizados", "Los parámetros del formalismo fueron actualizados correctamente.")

    def generate_automaton_action(self):
        self._apply_definition_data()

        if hasattr(self, 'trans_notebook'):
            try:
                current_tab_idx = self.trans_notebook.index(self.trans_notebook.select())
                if current_tab_idx == 0:
                    if not self.apply_matrix_changes(show_msg=False):
                        return
                elif current_tab_idx == 1:
                    if not self.process_text_import(show_msg=False):
                        return
            except Exception:
                pass

        self.refresh_transitions_table()
        if hasattr(self, 'matrix_inner_frame'):
            self.rebuild_matrix_grid()

        is_valid, msgs = self.tm.validate()

        self.recalculate_graph_layout()
        self.draw_graph()

        self.notebook.select(self.tab_graph)

        trans_count = len(self.tm.transitions)
        states_count = len(self.tm.states)
        status_msg = f"Autómata generado: {states_count} estados, {trans_count} transiciones."
        self.status_bar.config(text=status_msg)

        if not is_valid:
            warns = "\n- ".join(msgs[:4])
            messagebox.showwarning(
                "Autómata Generado con Observaciones",
                f"El autómata se generó con {states_count} estados y {trans_count} transiciones, pero tiene observaciones:\n\n- {warns}"
            )
        else:
            messagebox.showinfo(
                "Autómata Generado",
                f"El autómata '{self.tm.name}' fue generado exitosamente.\n\n"
                f"Estados: {states_count}\n"
                f"Transiciones: {trans_count}"
            )

    def add_transition_from_inputs(self):
        state = self.entry_t_state.get().strip()
        read_sym = self.entry_t_read.get().strip()
        next_state = self.entry_t_next.get().strip()
        write_sym = self.entry_t_write.get().strip()
        dir_val = self.combo_t_dir.get().split()[0]

        if not state or not read_sym or not next_state or not write_sym:
            messagebox.showwarning("Campos Requeridos", "Por favor completa todos los campos de la transición.")
            return

        self.tm.add_transition(state, read_sym, next_state, write_sym, dir_val)
        self.refresh_transitions_table()
        if hasattr(self, 'matrix_inner_frame'):
            self.rebuild_matrix_grid()
        self.recalculate_graph_layout()

        self.entry_t_read.delete(0, tk.END)
        self.entry_t_write.delete(0, tk.END)
        self.status_bar.config(text=f"Transición guardada: ({state}, {read_sym}) -> ({next_state}, {write_sym}, {dir_val})")

    def on_transition_row_selected(self, event=None):
        selected = self.tree_transitions.selection()
        if not selected:
            return
        item = self.tree_transitions.item(selected[0])
        vals = item['values']
        if len(vals) == 5:
            self.entry_t_state.delete(0, tk.END)
            self.entry_t_state.insert(0, str(vals[0]))
            self.entry_t_read.delete(0, tk.END)
            self.entry_t_read.insert(0, str(vals[1]))
            self.entry_t_next.delete(0, tk.END)
            self.entry_t_next.insert(0, str(vals[2]))
            self.entry_t_write.delete(0, tk.END)
            self.entry_t_write.insert(0, str(vals[3]))
            dir_str = str(vals[4])
            for opt in ["R", "L", "S"]:
                if opt == dir_str:
                    self.combo_t_dir.set(opt)
                    break

    def delete_selected_transition(self):
        selected = self.tree_transitions.selection()
        if not selected:
            messagebox.showinfo("Selección requerida", "Selecciona una fila de la tabla para eliminar.")
            return
        vals = self.tree_transitions.item(selected[0])['values']
        state, read_sym = str(vals[0]), str(vals[1])
        if self.tm.remove_transition(state, read_sym):
            self.refresh_transitions_table()
            if hasattr(self, 'matrix_inner_frame'):
                self.rebuild_matrix_grid()
            self.recalculate_graph_layout()
            self.status_bar.config(text=f"Transición eliminada: ({state}, {read_sym})")

    def clear_all_transitions(self):
        if messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar todas las transiciones?"):
            self.tm.clear_transitions()
            self.refresh_transitions_table()
            if hasattr(self, 'matrix_inner_frame'):
                self.rebuild_matrix_grid()
            self.recalculate_graph_layout()
            self.status_bar.config(text="Todas las transiciones han sido eliminadas.")

    def validate_machine(self):
        is_valid, messages = self.tm.validate()
        if is_valid and not messages:
            messagebox.showinfo("Validación Exitosa", "La Máquina de Turing está formalmente bien definida.")
        elif is_valid:
            warns = "\n- ".join(messages)
            messagebox.showwarning("Advertencias", f"La máquina es válida pero tiene observaciones:\n\n- {warns}")
        else:
            errs = "\n- ".join(messages)
            messagebox.showerror("Errores de Validación", f"Se encontraron errores formales:\n\n- {errs}")

    def save_to_json(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
            title="Guardar Máquina de Turing"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(self.tm.to_json())
                messagebox.showinfo("Guardado", f"Máquina guardada con éxito en:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error al guardar", str(e))

    def load_from_json(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
            title="Cargar Máquina de Turing"
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.tm = TuringMachine.from_json(content)
                self.load_machine_into_ui()
                messagebox.showinfo("Cargado", f"Máquina cargada correctamente desde:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error al cargar", f"No se pudo procesar el archivo:\n{e}")

    def sim_load_word(self):
        if self.is_simulating:
            self.sim_toggle_play()

        word = self.entry_sim_word.get().strip()
        self.tm.load_input(word)
        self.refresh_simulation_view()
        self.status_bar.config(text=f"Palabra '{word}' cargada.")

    def sim_reset(self):
        self.sim_load_word()

    def sim_step(self):
        if self.tm.halted:
            return

        running, msg = self.tm.step()
        self.refresh_simulation_view(msg)

        if not running and self.is_simulating:
            self.sim_toggle_play()

    def sim_toggle_play(self):
        if self.is_simulating:
            self.is_simulating = False
            self.btn_play.config(text="Ejecutar")
            if self.sim_after_id:
                self.root.after_cancel(self.sim_after_id)
                self.sim_after_id = None
        else:
            if self.tm.halted:
                self.sim_load_word()

            self.is_simulating = True
            self.btn_play.config(text="Pausa")
            self.run_sim_loop()

    def run_sim_loop(self):
        if not self.is_simulating:
            return

        if not self.tm.halted:
            self.sim_step()
            delay = int(self.speed_slider.get())
            self.sim_after_id = self.root.after(delay, self.run_sim_loop)
        else:
            self.sim_toggle_play()

    def refresh_simulation_view(self, status_msg: Optional[str] = None):
        self.lbl_sim_cur_state.config(text=f"Estado: {self.tm.current_state}")
        self.lbl_sim_steps.config(text=f"Pasos: {self.tm.step_count}")
        self.lbl_sim_head_pos.config(text=f"Posición Cabezal: {self.tm.head_position}")

        if self.tm.accepted:
            self.lbl_sim_status.config(
                text=f"Cadena ACEPTADA. Parada en estado '{self.tm.current_state}' ({self.tm.step_count} pasos)",
                bg="#dcfce7", fg="#15803d"
            )
        elif self.tm.rejected:
            self.lbl_sim_status.config(
                text=f"Cadena RECHAZADA. Parada en estado '{self.tm.current_state}' ({self.tm.step_count} pasos)",
                bg="#fee2e2", fg="#b91c1c"
            )
        else:
            msg = status_msg or f"Simulando. Estado actual: {self.tm.current_state}"
            self.lbl_sim_status.config(text=msg, bg="#e0f2fe", fg="#0369a1")

        self.draw_tape()

        for item in self.tree_log.get_children():
            self.tree_log.delete(item)

        for rec in self.tm.history:
            trans_str = ""
            if rec.next_state:
                trans_str = f"({rec.next_state}, '{rec.write_symbol}', {rec.direction.value if rec.direction else ''})"
            elif rec.step_number == 0:
                trans_str = "(Inicio)"
            else:
                trans_str = "(Parada)"

            self.tree_log.insert("", tk.END, values=(
                rec.step_number,
                rec.current_state,
                rec.read_symbol,
                trans_str,
                rec.tape_snapshot
            ))

        children = self.tree_log.get_children()
        if children:
            self.tree_log.see(children[-1])

        self.draw_graph()

    def draw_tape(self):
        self.tape_canvas.delete("all")
        cw = self.tape_canvas.winfo_width()
        if cw < 50:
            cw = 750
        ch = 130

        cell_w = 48
        cell_h = 50
        cell_y = 35

        center_x = cw / 2
        head = self.tm.head_position

        cells_each_side = int(cw / (2 * cell_w)) + 2
        min_cell = head - cells_each_side
        max_cell = head + cells_each_side

        for i in range(min_cell, max_cell + 1):
            x1 = center_x + (i - head) * cell_w - (cell_w / 2)
            x2 = x1 + cell_w
            y1 = cell_y
            y2 = y1 + cell_h

            is_head = (i == head)
            bg_color = "#dbeafe" if is_head else "#ffffff"
            border_color = "#2563eb" if is_head else "#cbd5e1"
            border_width = 3 if is_head else 1

            self.tape_canvas.create_rectangle(x1, y1, x2, y2, fill=bg_color, outline=border_color, width=border_width)
            self.tape_canvas.create_text(x1 + cell_w / 2, y1 - 10, text=str(i), font=("Segoe UI", 8), fill="#64748b")

            symbol = self.tm.get_tape_symbol(i)
            font_weight = "bold" if is_head else "normal"
            text_color = "#1e3a8a" if is_head else "#0f172a"
            self.tape_canvas.create_text(x1 + cell_w / 2, y1 + cell_h / 2, text=symbol, font=("Consolas", 16, font_weight), fill=text_color)

            if is_head:
                arrow_y = y2 + 5
                self.tape_canvas.create_polygon(
                    center_x, arrow_y,
                    center_x - 9, arrow_y + 14,
                    center_x + 9, arrow_y + 14,
                    fill="#2563eb", outline="#1d4ed8"
                )
                self.tape_canvas.create_text(center_x, arrow_y + 26, text="CABEZAL", font=("Segoe UI", 8, "bold"), fill="#2563eb")

    def recalculate_graph_layout(self):
        w = self.graph_canvas.winfo_width() or 750
        h = self.graph_canvas.winfo_height() or 500
        states_list = sorted(list(self.tm.states))
        self.node_positions = GraphLayout.compute_positions(
            states=states_list,
            initial_state=self.tm.initial_state,
            width=w,
            height=h
        )
        self.draw_graph()

    def draw_graph(self):
        self.graph_canvas.delete("all")
        if not self.node_positions:
            return

        radius = 28.0

        edges: Dict[Tuple[str, str], List[str]] = {}
        for key, val in self.tm.transitions.items():
            pair = (key.state, val.next_state)
            label = f"{key.symbol}/{val.write_symbol},{val.direction.value}"
            edges.setdefault(pair, []).append(label)

        for (u, v), labels in edges.items():
            if u not in self.node_positions or v not in self.node_positions:
                continue

            x1, y1 = self.node_positions[u]
            x2, y2 = self.node_positions[v]
            label_text = "\n".join(labels)

            if u == v:
                loop_h = 55.0
                cx, cy = x1, y1 - radius
                self.graph_canvas.create_arc(
                    cx - 24, cy - loop_h, cx + 24, cy + 10,
                    start=20, extent=320, style=tk.ARC,
                    outline="#64748b", width=2
                )
                self.graph_canvas.create_line(
                    cx + 18, cy - 2, cx + 5, cy + 5,
                    arrow=tk.LAST, fill="#64748b", width=2
                )
                self.graph_canvas.create_text(cx, cy - loop_h - 10, text=label_text, font=("Segoe UI", 8, "bold"), fill="#334155")
            else:
                dx = x2 - x1
                dy = y2 - y1
                dist = math.hypot(dx, dy)
                if dist == 0:
                    continue

                ux = dx / dist
                uy = dy / dist

                has_reverse = (v, u) in edges
                offset = 24.0 if has_reverse else 0.0

                start_x = x1 + ux * radius - uy * offset * 0.4
                start_y = y1 + uy * radius + ux * offset * 0.4
                end_x = x2 - ux * radius - uy * offset * 0.4
                end_y = y2 - uy * radius + ux * offset * 0.4

                mid_x = (start_x + end_x) / 2 - uy * offset
                mid_y = (start_y + end_y) / 2 + ux * offset

                self.graph_canvas.create_line(
                    start_x, start_y, mid_x, mid_y, end_x, end_y,
                    smooth=True, arrow=tk.LAST, arrowshape=(12, 14, 5),
                    fill="#64748b", width=2
                )

                label_x = mid_x - uy * 10
                label_y = mid_y + ux * 10
                self.graph_canvas.create_text(
                    label_x, label_y,
                    text=label_text,
                    font=("Segoe UI", 8, "bold"),
                    fill="#1e293b"
                )

        for state, (x, y) in self.node_positions.items():
            is_init = (state == self.tm.initial_state)
            is_acc = (state in self.tm.accept_states)
            is_rej = (state in self.tm.reject_states)
            is_current = (state == self.tm.current_state)

            if is_current:
                bg = "#fef08a"
                border = "#ca8a04"
                border_w = 4
            elif is_acc:
                bg = "#dcfce7"
                border = "#16a34a"
                border_w = 3
            elif is_rej:
                bg = "#fee2e2"
                border = "#dc2626"
                border_w = 3
            else:
                bg = "#eff6ff"
                border = "#2563eb"
                border_w = 2

            self.graph_canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                fill=bg, outline=border, width=border_w, tags=("node", state)
            )

            if is_acc:
                self.graph_canvas.create_oval(
                    x - (radius - 5), y - (radius - 5), x + (radius - 5), y + (radius - 5),
                    outline=border, width=2, tags=("node", state)
                )

            if is_init:
                self.graph_canvas.create_line(
                    x - radius - 30, y, x - radius, y,
                    arrow=tk.LAST, fill="#0f172a", width=3
                )
                self.graph_canvas.create_text(x - radius - 45, y, text="Inicio", font=("Segoe UI", 8, "bold"), fill="#0f172a")

            font_style = ("Segoe UI", 10, "bold") if is_current else ("Segoe UI", 10)
            self.graph_canvas.create_text(x, y, text=state, font=font_style, fill="#0f172a", tags=("node", state))

    def on_graph_click(self, event):
        x, y = event.x, event.y
        radius = 30.0
        for state, (nx, ny) in self.node_positions.items():
            if math.hypot(x - nx, y - ny) <= radius:
                self.drag_node = state
                self.drag_offset_x = nx - x
                self.drag_offset_y = ny - y
                return

    def on_graph_drag(self, event):
        if self.drag_node and self.drag_node in self.node_positions:
            new_x = event.x + self.drag_offset_x
            new_y = event.y + self.drag_offset_y
            self.node_positions[self.drag_node] = (new_x, new_y)
            self.draw_graph()

    def on_graph_release(self, event):
        self.drag_node = None
