"""
Punto de Entrada Principal del Proyecto de Máquina de Turing.
Permite iniciar la Interfaz Gráfica (GUI) o el Modo Consola (CLI).
"""

import sys
import argparse
import tkinter as tk

from turing_machine import TuringMachine
from examples_data import AVAILABLE_EXAMPLES
from gui import TuringMachineGUI


def run_gui():
    """Inicia la aplicación con Interfaz Gráfica (Tkinter)."""
    root = tk.Tk()
    app = TuringMachineGUI(root)
    root.mainloop()


def run_cli_interactive():
    """Modo interactivo en la terminal para definir y probar una Máquina de Turing."""
    print("=" * 65)
    print("      SIMULADOR Y GENERADOR DE MÁQUINAS DE TURING (CLI)      ")
    print("=" * 65)
    print("1. Usar un ejemplo predefinido")
    print("2. Ingresar un nuevo autómata manualmente")
    print("3. Iniciar la Interfaz Gráfica (Recomendado)")
    
    choice = input("\nSeleccione una opción (1/2/3) [1]: ").strip() or "1"
    
    if choice == "3":
        run_gui()
        return

    tm: TuringMachine

    if choice == "1":
        print("\nEjemplos disponibles:")
        examples_keys = list(AVAILABLE_EXAMPLES.keys())
        for idx, key in enumerate(examples_keys, 1):
            print(f"  [{idx}] {key}")
        
        ex_choice = input(f"Seleccione un ejemplo (1-{len(examples_keys)}) [1]: ").strip() or "1"
        try:
            selected_key = examples_keys[int(ex_choice) - 1]
            tm = AVAILABLE_EXAMPLES[selected_key]()
            print(f"\n✅ Cargado ejemplo: {tm.name}")
        except Exception:
            print("Opción inválida. Cargando ejemplo por defecto.")
            tm = AVAILABLE_EXAMPLES[examples_keys[0]]()
    else:
        name = input("\nNombre del autómata [Mi Máquina]: ").strip() or "Mi Máquina"
        sigma_str = input("Alfabeto de entrada Σ (separado por comas, ej: 0, 1): ").strip()
        sigma = {s.strip() for s in sigma_str.split(",") if s.strip()}

        blank = input("Símbolo blanco [B]: ").strip() or "B"

        gamma_str = input(f"Símbolo(s) adicionales de cinta Γ (además de Σ y {blank}, ej: X, Y): ").strip()
        gamma = set(sigma)
        gamma.add(blank)
        if gamma_str:
            gamma.update({s.strip() for s in gamma_str.split(",") if s.strip()})

        q0 = input("Estado inicial [q0]: ").strip() or "q0"
        accept_str = input("Estados de aceptación F (separados por comas, ej: q_accept): ").strip()
        accept_states = {s.strip() for s in accept_str.split(",") if s.strip()}

        tm = TuringMachine(
            name=name,
            input_alphabet=sigma,
            tape_alphabet=gamma,
            blank_symbol=blank,
            initial_state=q0,
            accept_states=accept_states
        )

        print("\n--- INGRESO DE TABLA DE TRANSICIONES δ ---")
        print("Seleccione cómo desea ingresar las transiciones:")
        print("  [1] Línea a línea (ej: q0 0 q0 1 R)")
        print("  [2] Pegar bloque de texto / Matriz CSV")
        print("  [3] Cargar desde archivo CSV o TXT")
        mode = input("Opción (1/2/3) [1]: ").strip() or "1"

        if mode == "2":
            print("\nPegue las transiciones. Escriba 'FIN' en una línea vacía para terminar:")
            lines = []
            while True:
                line = input()
                if line.strip().upper() == "FIN":
                    break
                lines.append(line)
            raw = "\n".join(lines)
            ok, msg, count = tm.import_from_text(raw)
            print(f"Resultado: {msg}")
        elif mode == "3":
            csv_path = input("Ruta del archivo CSV o TXT: ").strip()
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    content = f.read()
                ok, msg, count = tm.import_from_text(content)
                print(f"Resultado: {msg}")
            except Exception as e:
                print(f"Error al abrir archivo: {e}")
        else:
            print("Formato por línea: <estado_origen> <simbolo_leido> <nuevo_estado> <simbolo_escrito> <direccion L/R/S>")
            print("(Presione ENTER en una línea vacía para finalizar el ingreso de transiciones)")

            while True:
                line = input("Transición > ").strip()
                if not line:
                    break
                parts = line.split()
                if len(parts) != 5:
                    print("Formato incorrecto. Deben ser 5 elementos separados por espacios.")
                    continue
                try:
                    tm.add_transition(parts[0], parts[1], parts[2], parts[3], parts[4])
                    print(f"Transición agregada: δ({parts[0]}, '{parts[1]}') -> ({parts[2]}, '{parts[3]}', {parts[4].upper()})")
                except Exception as e:
                    print(f"Error: {e}")

    is_valid, msgs = tm.validate()
    if msgs:
        print("\nValidación:")
        for m in msgs:
            print(f"  - {m}")

    while True:
        print("\n" + "-" * 50)
        print("ACCIONES:")
        print("  [1] Probar una cadena de entrada en la cinta")
        print("  [2] Mostrar tabla de transiciones actual")
        print("  [3] Guardar máquina en JSON")
        print("  [4] Exportar tabla de transiciones a CSV")
        print("  [5] Salir")

        opt = input("Elija una opción (1-5): ").strip()

        if opt == "1":
            word = input("\nIngrese la palabra a probar: ").strip()
            print(f"\nSimulando palabra: '{word}'...")
            accepted, msg, steps = tm.run(word, max_steps=1000)
            
            print(f"\nResultado: {'ACEPTADA' if accepted else 'RECHAZADA'}")
            print(f"Mensaje: {msg}")
            print(f"Total de pasos: {steps}")
            print("\nÚltimos 10 pasos de ejecución:")
            for rec in tm.history[-10:]:
                print(f"  Paso {rec.step_number:3d} | Estado: {rec.current_state:8s} | Leído: '{rec.read_symbol}' | Cinta: {rec.tape_snapshot}")

        elif opt == "2":
            states, symbols, matrix = tm.get_transition_matrix()
            print(f"\nTABLA DE TRANSICIONES δ PARA: {tm.name}")
            header = f"{'Estado':<10}" + "".join(f"{s:^18}" for s in symbols)
            print("-" * len(header))
            print(header)
            print("-" * len(header))
            for st in states:
                row = f"{st:<10}"
                for sym in symbols:
                    val = matrix.get((st, sym), "-")
                    row += f"{val:^18}"
                print(row)
            print("-" * len(header))

        elif opt == "3":
            filename = input("Nombre de archivo [.json]: ").strip()
            if not filename.endswith(".json"):
                filename += ".json"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(tm.to_json())
            print(f"Guardado exitosamente en '{filename}'.")

        elif opt == "4":
            filename = input("Nombre de archivo CSV [.csv]: ").strip()
            if not filename.endswith(".csv"):
                filename += ".csv"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(tm.to_csv())
            print(f"Tabla de transiciones exportada a '{filename}'.")

        elif opt == "5":
            print("¡Hasta pronto!")
            break


def main():
    parser = argparse.ArgumentParser(description="Simulador y Generador de Máquinas de Turing en Python")
    parser.add_argument("--cli", action="store_true", help="Iniciar en modo consola (CLI)")
    args = parser.parse_args()

    if args.cli:
        run_cli_interactive()
    else:
        try:
            run_gui()
        except Exception as e:
            print(f"No se pudo iniciar la interfaz gráfica ({e}). Cambiando a modo consola...")
            run_cli_interactive()


if __name__ == "__main__":
    main()
