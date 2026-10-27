"""
Módulo del Núcleo de la Máquina de Turing.
Define la estructura formal, validación y simulación paso a paso.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Tuple, Set, List, Optional
import json
import re
import io
import csv


class Direction(str, Enum):
    LEFT = 'L'
    RIGHT = 'R'
    STAY = 'S'

    @classmethod
    def from_str(cls, val: str) -> 'Direction':
        val = val.strip().upper()
        if val in ('L', 'IZQ', 'IZQUIERDA', '<'):
            return cls.LEFT
        elif val in ('R', 'DER', 'DERECHA', '>'):
            return cls.RIGHT
        elif val in ('S', 'N', 'QUIETO', 'PARAR', '-'):
            return cls.STAY
        raise ValueError(f"Dirección inválida: '{val}'. Use 'L', 'R' o 'S'.")


@dataclass(frozen=True)
class TransitionKey:
    state: str
    symbol: str


@dataclass
class TransitionValue:
    next_state: str
    write_symbol: str
    direction: Direction


@dataclass
class StepRecord:
    step_number: int
    current_state: str
    read_symbol: str
    next_state: Optional[str]
    write_symbol: Optional[str]
    direction: Optional[Direction]
    head_position: int
    tape_snapshot: str
    status_description: str


class TuringMachine:
    """
    Representa una Máquina de Turing determinista formal de una cinta:
    M = (Q, Sigma, Gamma, delta, q0, B, F)
    """

    def __init__(
        self,
        name: str = "Máquina de Turing",
        states: Optional[Set[str]] = None,
        input_alphabet: Optional[Set[str]] = None,
        tape_alphabet: Optional[Set[str]] = None,
        blank_symbol: str = "B",
        initial_state: str = "q0",
        accept_states: Optional[Set[str]] = None,
        reject_states: Optional[Set[str]] = None,
    ):
        self.name = name
        self.blank_symbol = blank_symbol if blank_symbol else "B"
        self.states = set(states) if states else {initial_state}
        self.input_alphabet = set(input_alphabet) if input_alphabet else set()
        self.tape_alphabet = set(tape_alphabet) if tape_alphabet else set()
        self.initial_state = initial_state
        self.accept_states = set(accept_states) if accept_states else set()
        self.reject_states = set(reject_states) if reject_states else set()
        
        # delta: (state, read_symbol) -> (next_state, write_symbol, direction)
        self.transitions: Dict[TransitionKey, TransitionValue] = {}

        # Asegurar consistencia de alfabetos
        self.tape_alphabet.add(self.blank_symbol)
        self.tape_alphabet.update(self.input_alphabet)
        self.states.add(self.initial_state)
        self.states.update(self.accept_states)
        self.states.update(self.reject_states)

        # Estado de simulación
        self.tape: Dict[int, str] = {}
        self.head_position: int = 0
        self.current_state: str = self.initial_state
        self.step_count: int = 0
        self.halted: bool = False
        self.accepted: bool = False
        self.rejected: bool = False
        self.history: List[StepRecord] = []

    def add_transition(
        self,
        state: str,
        read_symbol: str,
        next_state: str,
        write_symbol: str,
        direction: Direction | str
    ):
        """Agrega o actualiza una transición en la función delta."""
        dir_enum = direction if isinstance(direction, Direction) else Direction.from_str(direction)
        state = state.strip()
        read_symbol = read_symbol.strip()
        next_state = next_state.strip()
        write_symbol = write_symbol.strip()

        # Registrar estados y símbolos automáticamente si no estaban
        self.states.add(state)
        self.states.add(next_state)
        self.tape_alphabet.add(read_symbol)
        self.tape_alphabet.add(write_symbol)

        key = TransitionKey(state, read_symbol)
        value = TransitionValue(next_state, write_symbol, dir_enum)
        self.transitions[key] = value

    def remove_transition(self, state: str, read_symbol: str) -> bool:
        """Elimina una transición existente."""
        key = TransitionKey(state.strip(), read_symbol.strip())
        if key in self.transitions:
            del self.transitions[key]
            return True
        return False

    def clear_transitions(self):
        """Limpia todas las transiciones."""
        self.transitions.clear()

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Valida formalmente la máquina de Turing.
        Retorna (es_valida, lista_de_advertencias_o_errores).
        """
        errors = []

        if not self.states:
            errors.append("El conjunto de estados Q no puede estar vacío.")
        if self.initial_state not in self.states:
            errors.append(f"El estado inicial '{self.initial_state}' no pertenece al conjunto de estados Q.")
        if self.blank_symbol in self.input_alphabet:
            errors.append(f"El símbolo blanco '{self.blank_symbol}' no debe pertenecer al alfabeto de entrada Sigma.")
        if not self.input_alphabet.issubset(self.tape_alphabet):
            missing = self.input_alphabet - self.tape_alphabet
            errors.append(f"El alfabeto de entrada Sigma debe ser subconjunto de Gamma. Faltan: {missing}")
        if self.blank_symbol not in self.tape_alphabet:
            errors.append(f"El símbolo blanco '{self.blank_symbol}' debe pertenecer al alfabeto de cinta Gamma.")
        
        # Validar estados de aceptación
        if not self.accept_states:
            errors.append("Se recomienda definir al menos un estado de aceptación.")
        for s in self.accept_states:
            if s not in self.states:
                errors.append(f"El estado de aceptación '{s}' no pertenece a Q.")

        # Validar transiciones
        for key, val in self.transitions.items():
            if key.state not in self.states:
                errors.append(f"Transición con estado origen '{key.state}' fuera de Q.")
            if key.symbol not in self.tape_alphabet:
                errors.append(f"Transición con símbolo leído '{key.symbol}' fuera de Gamma.")
            if val.next_state not in self.states:
                errors.append(f"Transición con estado destino '{val.next_state}' fuera de Q.")
            if val.write_symbol not in self.tape_alphabet:
                errors.append(f"Transición con símbolo escrito '{val.write_symbol}' fuera de Gamma.")

        is_valid = len(errors) == 0 or all("recomienda" in err for err in errors)
        return is_valid, errors

    def load_input(self, input_string: str = ""):
        """Carga una palabra de entrada en la cinta y reinicia la máquina."""
        self.tape.clear()
        self.head_position = 0
        self.current_state = self.initial_state
        self.step_count = 0
        self.halted = False
        self.accepted = False
        self.rejected = False
        self.history.clear()

        # Escribir palabra en la cinta comenzando en índice 0
        for i, char in enumerate(input_string):
            self.tape[i] = char

        # Si la palabra está vacía o es el primer paso, registrar estado inicial
        initial_symbol = self.get_tape_symbol(0)
        self.history.append(
            StepRecord(
                step_number=0,
                current_state=self.current_state,
                read_symbol=initial_symbol,
                next_state=None,
                write_symbol=None,
                direction=None,
                head_position=0,
                tape_snapshot=self.get_tape_string(),
                status_description="Inicio de la simulación"
            )
        )

        # Si ya inicia en estado de aceptación
        if self.current_state in self.accept_states:
            self.halted = True
            self.accepted = True
            self.history[-1].status_description = "Parada: Cadena aceptada (Estado inicial es de aceptación)."

    def get_tape_symbol(self, pos: int) -> str:
        """Obtiene el símbolo en una posición dada de la cinta (o blanco)."""
        return self.tape.get(pos, self.blank_symbol)

    def get_tape_bounds(self) -> Tuple[int, int]:
        """Calcula el rango [min_idx, max_idx] con símbolos no blancos y la cabeza."""
        indices = list(self.tape.keys())
        indices.append(self.head_position)
        min_idx = min(indices)
        max_idx = max(indices)
        # Añadir al menos 1 celda de margen a cada lado
        return min_idx - 1, max_idx + 1

    def get_tape_string(self) -> str:
        """Retorna una representación compacta de la cinta."""
        min_idx, max_idx = self.get_tape_bounds()
        chars = []
        for i in range(min_idx, max_idx + 1):
            char = self.get_tape_symbol(i)
            if i == self.head_position:
                chars.append(f"[{char}]")
            else:
                chars.append(char)
        return "".join(chars)

    def step(self) -> Tuple[bool, str]:
        """
        Ejecuta un solo paso de la Máquina de Turing.
        Retorna (continua_ejecucion, mensaje_estado).
        """
        if self.halted:
            if self.accepted:
                return False, "La máquina ya se detuvo: Cadena ACEPTADA."
            elif self.rejected:
                return False, "La máquina ya se detuvo: Cadena RECHAZADA."
            return False, "La máquina ya se detuvo."

        current_symbol = self.get_tape_symbol(self.head_position)
        key = TransitionKey(self.current_state, current_symbol)

        if key not in self.transitions:
            # No hay transición definida -> Parada
            self.halted = True
            if self.current_state in self.accept_states:
                self.accepted = True
                msg = f"Parada en estado de aceptación '{self.current_state}'. Cadena ACEPTADA."
            else:
                self.rejected = True
                msg = f"No hay transición para ({self.current_state}, '{current_symbol}'). Cadena RECHAZADA."
            
            if self.history:
                self.history[-1].status_description = msg
            return False, msg

        trans = self.transitions[key]
        self.step_count += 1

        # Escribir en la cinta
        self.tape[self.head_position] = trans.write_symbol

        # Mover cabezal
        prev_head = self.head_position
        if trans.direction == Direction.LEFT:
            self.head_position -= 1
        elif trans.direction == Direction.RIGHT:
            self.head_position += 1

        # Cambiar de estado
        prev_state = self.current_state
        self.current_state = trans.next_state

        msg = f"Paso {self.step_count}: ({prev_state}, '{current_symbol}') -> ({trans.next_state}, '{trans.write_symbol}', {trans.direction.value})"

        # Verificar si llegó a estado de aceptación o rechazo
        if self.current_state in self.accept_states:
            self.halted = True
            self.accepted = True
            msg += f" | Estado de Aceptación alcanzado: {self.current_state}. Cadena ACEPTADA."
        elif self.current_state in self.reject_states:
            self.halted = True
            self.rejected = True
            msg += f" | Estado de Rechazo alcanzado: {self.current_state}. Cadena RECHAZADA."

        # Registrar paso
        self.history.append(
            StepRecord(
                step_number=self.step_count,
                current_state=self.current_state,
                read_symbol=self.get_tape_symbol(self.head_position),
                next_state=trans.next_state,
                write_symbol=trans.write_symbol,
                direction=trans.direction,
                head_position=self.head_position,
                tape_snapshot=self.get_tape_string(),
                status_description=msg
            )
        )

        return not self.halted, msg

    def run(self, input_string: str = "", max_steps: int = 2000) -> Tuple[bool, str, int]:
        """
        Ejecuta la máquina completa sobre una palabra dada hasta que se detenga o supere max_steps.
        Retorna (es_aceptada, mensaje_final, total_pasos).
        """
        self.load_input(input_string)
        while not self.halted and self.step_count < max_steps:
            running, _ = self.step()
            if not running:
                break

        if not self.halted:
            self.halted = True
            self.rejected = True
            return False, f"Se superó el límite de {max_steps} pasos (posible bucle infinito).", self.step_count

        result_msg = "ACEPTADA" if self.accepted else "RECHAZADA"
        return self.accepted, f"Ejecución finalizada en {self.step_count} pasos: {result_msg}", self.step_count

    def to_dict(self) -> dict:
        """Serializa la máquina a un diccionario."""
        return {
            "name": self.name,
            "blank_symbol": self.blank_symbol,
            "input_alphabet": sorted(list(self.input_alphabet)),
            "tape_alphabet": sorted(list(self.tape_alphabet)),
            "states": sorted(list(self.states)),
            "initial_state": self.initial_state,
            "accept_states": sorted(list(self.accept_states)),
            "reject_states": sorted(list(self.reject_states)),
            "transitions": [
                {
                    "state": key.state,
                    "read_symbol": key.symbol,
                    "next_state": val.next_state,
                    "write_symbol": val.write_symbol,
                    "direction": val.direction.value,
                }
                for key, val in sorted(self.transitions.items(), key=lambda x: (x[0].state, x[0].symbol))
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TuringMachine':
        """Crea una Máquina de Turing a partir de un diccionario."""
        tm = cls(
            name=data.get("name", "Máquina de Turing"),
            states=set(data.get("states", [])),
            input_alphabet=set(data.get("input_alphabet", [])),
            tape_alphabet=set(data.get("tape_alphabet", [])),
            blank_symbol=data.get("blank_symbol", "B"),
            initial_state=data.get("initial_state", "q0"),
            accept_states=set(data.get("accept_states", [])),
            reject_states=set(data.get("reject_states", [])),
        )
        for t in data.get("transitions", []):
            tm.add_transition(
                state=t["state"],
                read_symbol=t["read_symbol"],
                next_state=t["next_state"],
                write_symbol=t["write_symbol"],
                direction=t["direction"],
            )
        return tm

    def to_json(self, indent: int = 2) -> str:
        """Exporta la máquina como cadena JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'TuringMachine':
        """Carga la máquina desde una cadena JSON."""
        return cls.from_dict(json.loads(json_str))

    def get_transition_matrix(self) -> Tuple[List[str], List[str], Dict[Tuple[str, str], str]]:
        """
        Retorna la tabla de transiciones en forma de matriz:
        (estados_ordenados, simbolos_cinta_ordenados, celda: (estado, simbolo) -> "q',w,D")
        """
        states = sorted(list(self.states))
        symbols = sorted(list(self.tape_alphabet))
        matrix: Dict[Tuple[str, str], str] = {}

        for key, val in self.transitions.items():
            matrix[(key.state, key.symbol)] = f"({val.next_state}, {val.write_symbol}, {val.direction.value})"

        return states, symbols, matrix

    @staticmethod
    def parse_transition_cell(cell_str: str) -> Optional[Tuple[str, str, Direction]]:
        s = cell_str.strip()
        if not s or s in ('-', '—', 'none', 'null', '/', 'lambda', 'eps'):
            return None
        s = s.strip('()[]{}<>')
        parts = [p.strip() for p in re.split(r'[,;/\s]+', s) if p.strip()]
        if len(parts) == 3:
            next_st, write_sym, dir_str = parts
            return next_st, write_sym, Direction.from_str(dir_str)
        elif len(parts) == 1:
            raise ValueError(f"La celda '{cell_str}' debe incluir (nuevo_estado, símbolo_escrito, dirección L/R/S).")
        raise ValueError(f"Formato no reconocido en celda: '{cell_str}'. Se esperaba (estado, símbolo, dirección).")

    @staticmethod
    def smart_split_row(row_str: str) -> List[str]:
        row_str = row_str.strip()
        if '\t' in row_str:
            return [c.strip().strip('"\'') for c in row_str.split('\t')]
        if ';' in row_str and '(' not in row_str:
            return [c.strip().strip('"\'') for c in row_str.split(';')]

        tokens = []
        current = []
        in_paren = 0
        for ch in row_str:
            if ch in '([{<':
                in_paren += 1
                current.append(ch)
            elif ch in ')]}>':
                in_paren = max(0, in_paren - 1)
                current.append(ch)
            elif (ch == ',' or ch == ';') and in_paren == 0:
                token = ''.join(current).strip().strip('"\'')
                tokens.append(token)
                current = []
            else:
                current.append(ch)
        tokens.append(''.join(current).strip().strip('"\''))
        return tokens

    def set_matrix_transitions(
        self,
        matrix_data: Dict[Tuple[str, str], str],
        clear_existing: bool = True
    ) -> Tuple[int, List[str]]:
        if clear_existing:
            self.transitions.clear()

        added = 0
        errors = []

        for (st, sym), cell_val in matrix_data.items():
            if not cell_val or not cell_val.strip():
                continue
            try:
                parsed = self.parse_transition_cell(cell_val)
                if parsed:
                    next_st, w_sym, d = parsed
                    self.add_transition(st, sym, next_st, w_sym, d)
                    added += 1
            except Exception as e:
                errors.append(f"Error en celda ({st}, '{sym}'): {e}")

        return added, errors

    def to_csv(self) -> str:
        states = sorted(list(self.states))
        symbols = sorted(list(self.tape_alphabet))
        _, _, matrix = self.get_transition_matrix()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Estado"] + symbols)

        for st in states:
            row = [st]
            for sym in symbols:
                cell_val = matrix.get((st, sym), "")
                row.append(cell_val)
            writer.writerow(row)

        return output.getvalue()

    def import_from_text(self, raw_text: str, clear_existing: bool = True) -> Tuple[bool, str, int]:
        lines = [l.strip() for l in raw_text.splitlines() if l.strip() and not l.strip().startswith("#")]
        if not lines:
            return False, "El texto proporcionado está vacío.", 0

        if clear_existing:
            self.transitions.clear()

        first_row = self.smart_split_row(lines[0])
        is_matrix = len(first_row) >= 2 and (
            first_row[0].lower() in ("estado", "state", "q", "estados", "q/σ", "q/sigma", "q\\sigma")
            or any(s in self.tape_alphabet for s in first_row[1:])
        )

        added = 0
        errors = []

        if is_matrix:
            symbols = [s for s in first_row[1:] if s]
            for sym in symbols:
                self.tape_alphabet.add(sym)

            for line in lines[1:]:
                row = self.smart_split_row(line)
                if not row or not row[0]:
                    continue
                state = row[0]
                self.states.add(state)
                for col_idx, cell in enumerate(row[1:]):
                    if col_idx < len(symbols):
                        sym = symbols[col_idx]
                        if cell.strip():
                            try:
                                parsed = self.parse_transition_cell(cell)
                                if parsed:
                                    next_st, w_sym, d = parsed
                                    self.add_transition(state, sym, next_st, w_sym, d)
                                    added += 1
                            except Exception as e:
                                errors.append(f"Fila {state}, col '{sym}': {e}")

            msg = f"Se cargaron con éxito {added} transiciones desde la matriz 2D."
            if errors:
                msg += f" (Con {len(errors)} advertencias: {'; '.join(errors[:3])})"
            return True, msg, added

        for line_num, line in enumerate(lines, 1):
            cleaned = re.sub(r'[\(\)\[\]\->=,;]+', ' ', line)
            parts = cleaned.split()
            if len(parts) >= 5:
                st, r_sym, next_st, w_sym, d_str = parts[:5]
                try:
                    self.add_transition(st, r_sym, next_st, w_sym, d_str)
                    added += 1
                except Exception as e:
                    errors.append(f"Línea {line_num} ('{line}'): {e}")
            else:
                errors.append(f"Línea {line_num}: No tiene 5 campos requeridos ({line})")

        if added > 0:
            msg = f"Se cargaron con éxito {added} transiciones desde la lista."
            if errors:
                msg += f" (Se omitieron {len(errors)} líneas con advertencias)."
            return True, msg, added
        else:
            return False, f"No se pudo interpretar el formato de las transiciones. Errores: {'; '.join(errors[:3])}", 0
