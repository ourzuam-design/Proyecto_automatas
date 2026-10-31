"""
Módulo de Ejemplos Predefinidos de Máquinas de Turing.
Contiene autómatas clásicos para pruebas y demostraciones.
"""

from turing_machine import MaquinaTuring


def obtener_maquina_an_bn() -> MaquinaTuring:
    """
    Reconocedor del lenguaje L = { a^n b^n | n >= 1 }
    Alfabeto de entrada: {a, b}
    Alfabeto de cinta: {a, b, X, Y, B}
    """
    mt = MaquinaTuring(
        nombre="Reconocedor de a^n b^n (n >= 1)",
        alfabeto_entrada={"a", "b"},
        alfabeto_cinta={"a", "b", "X", "Y", "B"},
        simbolo_blanco="B",
        estado_inicial="q0",
        estados_aceptacion={"q4"},
    )
    mt.agregar_transicion("q0", "a", "q1", "X", "R")
    mt.agregar_transicion("q0", "Y", "q3", "Y", "R")

    mt.agregar_transicion("q1", "a", "q1", "a", "R")
    mt.agregar_transicion("q1", "Y", "q1", "Y", "R")
    mt.agregar_transicion("q1", "b", "q2", "Y", "L")

    mt.agregar_transicion("q2", "a", "q2", "a", "L")
    mt.agregar_transicion("q2", "Y", "q2", "Y", "L")
    mt.agregar_transicion("q2", "X", "q0", "X", "R")

    mt.agregar_transicion("q3", "Y", "q3", "Y", "R")
    mt.agregar_transicion("q3", "B", "q4", "B", "S")

    return mt


def obtener_maquina_incrementador_binario() -> MaquinaTuring:
    """
    Incrementador binario: Suma 1 a un número binario (ej. 1011 -> 1100).
    Alfabeto de entrada: {0, 1}
    Alfabeto de cinta: {0, 1, B}
    """
    mt = MaquinaTuring(
        nombre="Incrementador Binario (w + 1)",
        alfabeto_entrada={"0", "1"},
        alfabeto_cinta={"0", "1", "B"},
        simbolo_blanco="B",
        estado_inicial="q0",
        estados_aceptacion={"q2"}
    )
    mt.agregar_transicion("q0", "0", "q0", "0", "R")
    mt.agregar_transicion("q0", "1", "q0", "1", "R")
    mt.agregar_transicion("q0", "B", "q1", "B", "L")

    mt.agregar_transicion("q1", "0", "q2", "1", "S")
    mt.agregar_transicion("q1", "1", "q1", "0", "L")
    mt.agregar_transicion("q1", "B", "q2", "1", "S")

    return mt


def obtener_maquina_palindromos() -> MaquinaTuring:
    """
    Reconocedor de Palíndromos sobre el alfabeto {a, b}.
    Ejemplos aceptados: 'aba', 'abba', 'a', '', 'bbaabb'
    """
    mt = MaquinaTuring(
        nombre="Reconocedor de Palíndromos {a, b}",
        alfabeto_entrada={"a", "b"},
        alfabeto_cinta={"a", "b", "B"},
        simbolo_blanco="B",
        estado_inicial="q0",
        estados_aceptacion={"q6"}
    )
    mt.agregar_transicion("q0", "a", "q1", "B", "R")
    mt.agregar_transicion("q0", "b", "q2", "B", "R")
    mt.agregar_transicion("q0", "B", "q6", "B", "S")

    mt.agregar_transicion("q1", "a", "q1", "a", "R")
    mt.agregar_transicion("q1", "b", "q1", "b", "R")
    mt.agregar_transicion("q1", "B", "q3", "B", "L")

    mt.agregar_transicion("q3", "a", "q5", "B", "L")
    mt.agregar_transicion("q3", "B", "q6", "B", "S")

    mt.agregar_transicion("q2", "a", "q2", "a", "R")
    mt.agregar_transicion("q2", "b", "q2", "b", "R")
    mt.agregar_transicion("q2", "B", "q4", "B", "L")

    mt.agregar_transicion("q4", "b", "q5", "B", "L")
    mt.agregar_transicion("q4", "B", "q6", "B", "S")

    mt.agregar_transicion("q5", "a", "q5", "a", "L")
    mt.agregar_transicion("q5", "b", "q5", "b", "L")
    mt.agregar_transicion("q5", "B", "q0", "B", "R")

    return mt


def obtener_maquina_inversor_bits() -> MaquinaTuring:
    """
    Inversor de bits (Complemento a 1): cambia 0 por 1 y 1 por 0.
    """
    mt = MaquinaTuring(
        nombre="Inversor de Bits (0 -> 1, 1 -> 0)",
        alfabeto_entrada={"0", "1"},
        alfabeto_cinta={"0", "1", "B"},
        simbolo_blanco="B",
        estado_inicial="q0",
        estados_aceptacion={"q1"}
    )
    mt.agregar_transicion("q0", "0", "q0", "1", "R")
    mt.agregar_transicion("q0", "1", "q0", "0", "R")
    mt.agregar_transicion("q0", "B", "q1", "B", "S")
    return mt


EJEMPLOS_DISPONIBLES = {
    "a^n b^n (n >= 1)": obtener_maquina_an_bn,
    "Incrementador Binario (w + 1)": obtener_maquina_incrementador_binario,
    "Palíndromos {a, b}": obtener_maquina_palindromos,
    "Inversor de Bits (Complemento a 1)": obtener_maquina_inversor_bits,
}
