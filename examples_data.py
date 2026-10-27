"""
Colección de ejemplos clásicos de Máquinas de Turing predefinidas.
Útiles para pruebas rápidas y demostraciones didácticas.
"""

from turing_machine import TuringMachine


def get_an_bn_machine() -> TuringMachine:
    """
    Reconocedor del lenguaje L = { a^n b^n | n >= 1 }
    Alfabeto de entrada: {a, b}
    Alfabeto de cinta: {a, b, X, Y, B}
    """
    tm = TuringMachine(
        name="Reconocedor de a^n b^n (n >= 1)",
        input_alphabet={"a", "b"},
        tape_alphabet={"a", "b", "X", "Y", "B"},
        blank_symbol="B",
        initial_state="q0",
        accept_states={"q4"},
        reject_states={"q_reject"}
    )
    # q0: Lee 'a', la marca con 'X' y va a buscar 'b'
    tm.add_transition("q0", "a", "q1", "X", "R")
    tm.add_transition("q0", "Y", "q3", "Y", "R")  # Si encuentra Y al inicio, verifica si solo quedan Y

    # q1: Salta 'a' y 'Y' buscando la primera 'b'
    tm.add_transition("q1", "a", "q1", "a", "R")
    tm.add_transition("q1", "Y", "q1", "Y", "R")
    tm.add_transition("q1", "b", "q2", "Y", "L")  # Encuentra 'b', la marca con 'Y' y regresa

    # q2: Retrocede hasta encontrar la 'X' más reciente
    tm.add_transition("q2", "a", "q2", "a", "L")
    tm.add_transition("q2", "Y", "q2", "Y", "L")
    tm.add_transition("q2", "X", "q0", "X", "R")  # Al encontrar 'X', se posiciona en el siguiente símbolo

    # q3: Verifica que solo queden 'Y' antes del blanco final
    tm.add_transition("q3", "Y", "q3", "Y", "R")
    tm.add_transition("q3", "B", "q4", "B", "S")  # Aceptación

    return tm


def get_binary_increment_machine() -> TuringMachine:
    """
    Incrementador binario: Suma 1 a un número binario (ej. 1011 -> 1100).
    Alfabeto de entrada: {0, 1}
    Alfabeto de cinta: {0, 1, B}
    """
    tm = TuringMachine(
        name="Incrementador Binario (w + 1)",
        input_alphabet={"0", "1"},
        tape_alphabet={"0", "1", "B"},
        blank_symbol="B",
        initial_state="q0",
        accept_states={"q_accept"}
    )
    # q0: Se desplaza a la derecha hasta el final del número
    tm.add_transition("q0", "0", "q0", "0", "R")
    tm.add_transition("q0", "1", "q0", "1", "R")
    tm.add_transition("q0", "B", "q1", "B", "L")  # Llegó al final, regresa un paso hacia el bit menos significativo

    # q1: Suma 1 con propagación de acarreo hacia la izquierda
    tm.add_transition("q1", "0", "q_accept", "1", "S")  # 0 + 1 = 1 (sin acarreo, termina)
    tm.add_transition("q1", "1", "q1", "0", "L")        # 1 + 1 = 0 (acarreo a la izquierda)
    tm.add_transition("q1", "B", "q_accept", "1", "S")  # Acarreo sobrepasó el inicio (ej: 111 -> 1000)

    return tm


def get_palindrome_machine() -> TuringMachine:
    """
    Reconocedor de Palíndromos sobre el alfabeto {a, b}.
    Ejemplos aceptados: 'aba', 'abba', 'a', '', 'bbaabb'
    """
    tm = TuringMachine(
        name="Reconocedor de Palíndromos {a, b}",
        input_alphabet={"a", "b"},
        tape_alphabet={"a", "b", "B"},
        blank_symbol="B",
        initial_state="q0",
        accept_states={"q_accept"}
    )
    # q0: Lee el primer símbolo, lo borra y recuerda cuál fue
    tm.add_transition("q0", "a", "q_find_a", "B", "R")
    tm.add_transition("q0", "b", "q_find_b", "B", "R")
    tm.add_transition("q0", "B", "q_accept", "B", "S")  # Cadena vacía o de longitud par completada

    # Rama para 'a': Avanza hasta el blanco final
    tm.add_transition("q_find_a", "a", "q_find_a", "a", "R")
    tm.add_transition("q_find_a", "b", "q_find_a", "b", "R")
    tm.add_transition("q_find_a", "B", "q_check_a", "B", "L")

    # Verifica si el último símbolo coincide con 'a'
    tm.add_transition("q_check_a", "a", "q_rewind", "B", "L")  # Coincide: lo borra y retrocede
    tm.add_transition("q_check_a", "B", "q_accept", "B", "S")  # Solo había 1 símbolo 'a'

    # Rama para 'b': Avanza hasta el blanco final
    tm.add_transition("q_find_b", "a", "q_find_b", "a", "R")
    tm.add_transition("q_find_b", "b", "q_find_b", "b", "R")
    tm.add_transition("q_find_b", "B", "q_check_b", "B", "L")

    # Verifica si el último símbolo coincide con 'b'
    tm.add_transition("q_check_b", "b", "q_rewind", "B", "L")  # Coincide: lo borra y retrocede
    tm.add_transition("q_check_b", "B", "q_accept", "B", "S")  # Solo había 1 símbolo 'b'

    # q_rewind: Retrocede hasta el inicio de la palabra restante
    tm.add_transition("q_rewind", "a", "q_rewind", "a", "L")
    tm.add_transition("q_rewind", "b", "q_rewind", "b", "L")
    tm.add_transition("q_rewind", "B", "q0", "B", "R")  # Llegó al blanco inicial, reinicia el ciclo en q0

    return tm


def get_bit_inverter_machine() -> TuringMachine:
    """
    Inversor de bits (Complemento a 1): cambia 0 por 1 y 1 por 0.
    """
    tm = TuringMachine(
        name="Inversor de Bits (0 -> 1, 1 -> 0)",
        input_alphabet={"0", "1"},
        tape_alphabet={"0", "1", "B"},
        blank_symbol="B",
        initial_state="q0",
        accept_states={"q_accept"}
    )
    tm.add_transition("q0", "0", "q0", "1", "R")
    tm.add_transition("q0", "1", "q0", "0", "R")
    tm.add_transition("q0", "B", "q_accept", "B", "S")
    return tm


AVAILABLE_EXAMPLES = {
    "a^n b^n (n >= 1)": get_an_bn_machine,
    "Incrementador Binario (w + 1)": get_binary_increment_machine,
    "Palíndromos {a, b}": get_palindrome_machine,
    "Inversor de Bits (Complemento a 1)": get_bit_inverter_machine,
}
