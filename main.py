"""
Punto de Entrada Principal del Proyecto de Máquina de Turing.
Permite iniciar la Interfaz Gráfica (GUI) o el Modo Consola (CLI).
"""

import sys
import argparse
import tkinter as tk

from turing_machine import MaquinaTuring
from examples_data import EJEMPLOS_DISPONIBLES
from gui import InterfazMaquinaTuring


def ejecutar_interfaz_grafica():
    """Inicia la aplicación con Interfaz Gráfica (Tkinter)."""
    raiz = tk.Tk()
    aplicacion = InterfazMaquinaTuring(raiz)
    raiz.mainloop()


def ejecutar_cli_interactivo():
    """Modo interactivo en la terminal para definir y probar una Máquina de Turing."""
    print("=" * 65)
    print("      SIMULADOR Y GENERADOR DE MÁQUINAS DE TURING (CLI)      ")
    print("=" * 65)
    print("1. Usar un ejemplo predefinido")
    print("2. Ingresar un nuevo autómata manualmente")
    print("3. Iniciar la Interfaz Gráfica (Recomendado)")

    opcion = input("\nSeleccione una opción (1/2/3) [1]: ").strip() or "1"

    if opcion == "3":
        ejecutar_interfaz_grafica()
        return

    mt: MaquinaTuring

    if opcion == "1":
        print("\nEjemplos disponibles:")
        claves_ejemplos = list(EJEMPLOS_DISPONIBLES.keys())
        for indice, clave in enumerate(claves_ejemplos, 1):
            print(f"  [{indice}] {clave}")

        opcion_ejemplo = input(f"Seleccione un ejemplo (1-{len(claves_ejemplos)}) [1]: ").strip() or "1"
        try:
            clave_seleccionada = claves_ejemplos[int(opcion_ejemplo) - 1]
            mt = EJEMPLOS_DISPONIBLES[clave_seleccionada]()
            print(f"\n✅ Cargado ejemplo: {mt.nombre}")
        except Exception:
            print("Opción inválida. Cargando ejemplo por defecto.")
            mt = EJEMPLOS_DISPONIBLES[claves_ejemplos[0]]()
    else:
        nombre = input("\nNombre del autómata [Mi Máquina]: ").strip() or "Mi Máquina"
        sigma_str = input("Alfabeto de entrada Σ (separado por comas, ej: 0, 1): ").strip()
        sigma = {s.strip() for s in sigma_str.split(",") if s.strip()}

        blanco = input("Símbolo blanco [B]: ").strip() or "B"

        gamma_str = input(f"Símbolo(s) adicionales de cinta Γ (además de Σ y {blanco}, ej: X, Y): ").strip()
        gamma = set(sigma)
        gamma.add(blanco)
        if gamma_str:
            gamma.update({s.strip() for s in gamma_str.split(",") if s.strip()})

        q0 = input("Estado inicial [q0]: ").strip() or "q0"
        aceptacion_str = input("Estados de aceptación F (separados por comas, ej: q_accept): ").strip()
        estados_aceptacion = {s.strip() for s in aceptacion_str.split(",") if s.strip()}

        mt = MaquinaTuring(
            nombre=nombre,
            alfabeto_entrada=sigma,
            alfabeto_cinta=gamma,
            simbolo_blanco=blanco,
            estado_inicial=q0,
            estados_aceptacion=estados_aceptacion
        )

        print("\n--- INGRESO DE TABLA DE TRANSICIONES δ ---")
        print("Seleccione cómo desea ingresar las transiciones:")
        print("  [1] Línea a línea (ej: q0 0 q0 1 R)")
        print("  [2] Pegar bloque de texto / Matriz CSV")
        print("  [3] Cargar desde archivo CSV o TXT")
        modo = input("Opción (1/2/3) [1]: ").strip() or "1"

        if modo == "2":
            print("\nPegue las transiciones. Escriba 'FIN' en una línea vacía para terminar:")
            lineas = []
            while True:
                linea = input()
                if linea.strip().upper() == "FIN":
                    break
                lineas.append(linea)
            texto_bruto = "\n".join(lineas)
            ok, mensaje, conteo = mt.importar_desde_texto(texto_bruto)
            print(f"Resultado: {mensaje}")
        elif modo == "3":
            ruta_csv = input("Ruta del archivo CSV o TXT: ").strip()
            try:
                with open(ruta_csv, "r", encoding="utf-8") as archivo:
                    contenido = archivo.read()
                ok, mensaje, conteo = mt.importar_desde_texto(contenido)
                print(f"Resultado: {mensaje}")
            except Exception as error:
                print(f"Error al abrir archivo: {error}")
        else:
            print("Formato por línea: <estado_origen> <simbolo_leido> <nuevo_estado> <simbolo_escrito> <direccion L/R/S>")
            print("(Presione ENTER en una línea vacía para finalizar el ingreso de transiciones)")

            while True:
                linea = input("Transición > ").strip()
                if not linea:
                    break
                partes = linea.split()
                if len(partes) != 5:
                    print("Formato incorrecto. Deben ser 5 elementos separados por espacios.")
                    continue
                try:
                    mt.agregar_transicion(partes[0], partes[1], partes[2], partes[3], partes[4])
                    print(f"Transición agregada: δ({partes[0]}, '{partes[1]}') -> ({partes[2]}, '{partes[3]}', {partes[4].upper()})")
                except Exception as error:
                    print(f"Error: {error}")

    es_valida, mensajes = mt.validar()
    if mensajes:
        print("\nValidación:")
        for m in mensajes:
            print(f"  - {m}")

    while True:
        print("\n" + "-" * 50)
        print("ACCIONES:")
        print("  [1] Probar una cadena de entrada en la cinta")
        print("  [2] Mostrar tabla de transiciones actual")
        print("  [3] Guardar máquina en JSON")
        print("  [4] Exportar tabla de transiciones a CSV")
        print("  [5] Salir")

        opcion_accion = input("Elija una opción (1-5): ").strip()

        if opcion_accion == "1":
            palabra = input("\nIngrese la palabra a probar: ").strip()
            print(f"\nSimulando palabra: '{palabra}'...")
            aceptada, mensaje, pasos = mt.ejecutar(palabra, max_pasos=1000)

            print(f"\nResultado: {'ACEPTADA' if aceptada else 'RECHAZADA'}")
            print(f"Mensaje: {mensaje}")
            print(f"Total de pasos: {pasos}")
            print("\nÚltimos 10 pasos de ejecución:")
            for registro in mt.historial[-10:]:
                print(f"  Paso {registro.numero_paso:3d} | Estado: {registro.estado_actual:8s} | Leído: '{registro.simbolo_leido}' | Cinta: {registro.captura_cinta}")

        elif opcion_accion == "2":
            estados, simbolos, matriz = mt.obtener_matriz_transiciones()
            print(f"\nTABLA DE TRANSICIONES δ PARA: {mt.nombre}")
            encabezado = f"{'Estado':<10}" + "".join(f"{s:^18}" for s in simbolos)
            print("-" * len(encabezado))
            print(encabezado)
            print("-" * len(encabezado))
            for st in estados:
                fila = f"{st:<10}"
                for sym in simbolos:
                    val = matriz.get((st, sym), "-")
                    fila += f"{val:^18}"
                print(fila)
            print("-" * len(encabezado))

        elif opcion_accion == "3":
            nombre_archivo = input("Nombre de archivo [.json]: ").strip()
            if not nombre_archivo.endswith(".json"):
                nombre_archivo += ".json"
            with open(nombre_archivo, "w", encoding="utf-8") as archivo:
                archivo.write(mt.a_json())
            print(f"Guardado exitosamente en '{nombre_archivo}'.")

        elif opcion_accion == "4":
            nombre_archivo = input("Nombre de archivo CSV [.csv]: ").strip()
            if not nombre_archivo.endswith(".csv"):
                nombre_archivo += ".csv"
            with open(nombre_archivo, "w", encoding="utf-8") as archivo:
                archivo.write(mt.a_csv())
            print(f"Tabla de transiciones exportada a '{nombre_archivo}'.")

        elif opcion_accion == "5":
            print("¡Hasta pronto!")
            break


def principal():
    analizador = argparse.ArgumentParser(description="Simulador y Generador de Máquinas de Turing en Python")
    analizador.add_argument("--cli", action="store_true", help="Iniciar en modo consola (CLI)")
    argumentos = analizador.parse_args()

    if argumentos.cli:
        ejecutar_cli_interactivo()
    else:
        try:
            ejecutar_interfaz_grafica()
        except Exception as error:
            print(f"No se pudo iniciar la interfaz gráfica ({error}). Cambiando a modo consola...")
            ejecutar_cli_interactivo()


if __name__ == "__main__":
    principal()
