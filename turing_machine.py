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


class Direccion(str, Enum):
    IZQUIERDA = 'L'
    DERECHA = 'R'
    QUIETO = 'S'

    # Alias para compatibilidad con código existente
    LEFT = 'L'
    RIGHT = 'R'
    STAY = 'S'

    @classmethod
    def desde_cadena(cls, valor: str) -> 'Direccion':
        valor = valor.strip().upper()
        if valor in ('L', 'IZQ', 'IZQUIERDA', '<'):
            return cls.IZQUIERDA
        elif valor in ('R', 'DER', 'DERECHA', '>'):
            return cls.DERECHA
        elif valor in ('S', 'N', 'QUIETO', 'PARAR', '-'):
            return cls.QUIETO
        raise ValueError(f"Dirección inválida: '{valor}'. Use 'L', 'R' o 'S'.")

    # Alias del método
    from_str = desde_cadena


# Alias de clase para compatibilidad
Direction = Direccion


@dataclass(frozen=True)
class ClaveTransicion:
    estado: str
    simbolo: str


# Alias para compatibilidad
TransitionKey = ClaveTransicion


@dataclass
class ValorTransicion:
    nuevo_estado: str
    simbolo_escrito: str
    direccion: Direccion


# Alias para compatibilidad
TransitionValue = ValorTransicion


@dataclass
class RegistroPaso:
    numero_paso: int
    estado_actual: str
    simbolo_leido: str
    nuevo_estado: Optional[str]
    simbolo_escrito: Optional[str]
    direccion: Optional[Direccion]
    posicion_cabezal: int
    captura_cinta: str
    descripcion_estado: str


# Alias para compatibilidad
StepRecord = RegistroPaso


class MaquinaTuring:

    def __init__(
        self,
        nombre: str = "Máquina de Turing",
        estados: Optional[Set[str]] = None,
        alfabeto_entrada: Optional[Set[str]] = None,
        alfabeto_cinta: Optional[Set[str]] = None,
        simbolo_blanco: str = "B",
        estado_inicial: str = "q0",
        estados_aceptacion: Optional[Set[str]] = None,
        estados_rechazo: Optional[Set[str]] = None,
    ):
        self.nombre = nombre
        self.simbolo_blanco = simbolo_blanco if simbolo_blanco else "B"
        self.estados = set(estados) if estados else {estado_inicial}
        self.alfabeto_entrada = set(alfabeto_entrada) if alfabeto_entrada else set()
        self.alfabeto_cinta = set(alfabeto_cinta) if alfabeto_cinta else set()
        self.estado_inicial = estado_inicial
        self.estados_aceptacion = set(estados_aceptacion) if estados_aceptacion else set()
        self.estados_rechazo = set(estados_rechazo) if estados_rechazo else set()

        self.transiciones: Dict[ClaveTransicion, ValorTransicion] = {}

        self.alfabeto_cinta.add(self.simbolo_blanco)
        self.alfabeto_cinta.update(self.alfabeto_entrada)
        self.estados.add(self.estado_inicial)
        self.estados.update(self.estados_aceptacion)
        self.estados.update(self.estados_rechazo)

        self.cinta: Dict[int, str] = {}
        self.posicion_cabezal: int = 0
        self.estado_actual: str = self.estado_inicial
        self.contador_pasos: int = 0
        self.detenida: bool = False
        self.aceptada: bool = False
        self.rechazada: bool = False
        self.historial: List[RegistroPaso] = []

    def agregar_transicion(
        self,
        estado: str,
        simbolo_leido: str,
        nuevo_estado: str,
        simbolo_escrito: str,
        direccion: Direccion | str
    ):
        
        dir_enum = direccion if isinstance(direccion, Direccion) else Direccion.desde_cadena(direccion)
        estado = estado.strip()
        simbolo_leido = simbolo_leido.strip()
        nuevo_estado = nuevo_estado.strip()
        simbolo_escrito = simbolo_escrito.strip()

        self.estados.add(estado)
        self.estados.add(nuevo_estado)
        self.alfabeto_cinta.add(simbolo_leido)
        self.alfabeto_cinta.add(simbolo_escrito)

        clave = ClaveTransicion(estado, simbolo_leido)
        valor = ValorTransicion(nuevo_estado, simbolo_escrito, dir_enum)
        self.transiciones[clave] = valor

    add_transition = agregar_transicion

    def eliminar_transicion(self, estado: str, simbolo_leido: str) -> bool:
        """Elimina una transición existente."""
        clave = ClaveTransicion(estado.strip(), simbolo_leido.strip())
        if clave in self.transiciones:
            del self.transiciones[clave]
            return True
        return False

    remove_transition = eliminar_transicion

    def limpiar_transiciones(self):
        self.transiciones.clear()

    clear_transitions = limpiar_transiciones

    def validar(self) -> Tuple[bool, List[str]]:
    
        errores = []

        if not self.estados:
            errores.append("El conjunto de estados Q no puede estar vacío.")
        if self.estado_inicial not in self.estados:
            errores.append(f"El estado inicial '{self.estado_inicial}' no pertenece al conjunto de estados Q.")
        if self.simbolo_blanco in self.alfabeto_entrada:
            errores.append(f"El símbolo blanco '{self.simbolo_blanco}' no debe pertenecer al alfabeto de entrada Sigma.")
        if not self.alfabeto_entrada.issubset(self.alfabeto_cinta):
            faltantes = self.alfabeto_entrada - self.alfabeto_cinta
            errores.append(f"El alfabeto de entrada Sigma debe ser subconjunto de Gamma. Faltan: {faltantes}")
        if self.simbolo_blanco not in self.alfabeto_cinta:
            errores.append(f"El símbolo blanco '{self.simbolo_blanco}' debe pertenecer al alfabeto de cinta Gamma.")

        if not self.estados_aceptacion:
            errores.append("Se recomienda definir al menos un estado de aceptación.")
        for s in self.estados_aceptacion:
            if s not in self.estados:
                errores.append(f"El estado de aceptación '{s}' no pertenece a Q.")

        for clave, valor in self.transiciones.items():
            if clave.estado not in self.estados:
                errores.append(f"Transición con estado origen '{clave.estado}' fuera de Q.")
            if clave.simbolo not in self.alfabeto_cinta:
                errores.append(f"Transición con símbolo leído '{clave.simbolo}' fuera de Gamma.")
            if valor.nuevo_estado not in self.estados:
                errores.append(f"Transición con estado destino '{valor.nuevo_estado}' fuera de Q.")
            if valor.simbolo_escrito not in self.alfabeto_cinta:
                errores.append(f"Transición con símbolo escrito '{valor.simbolo_escrito}' fuera de Gamma.")

        es_valida = len(errores) == 0 or all("recomienda" in err for err in errores)
        return es_valida, errores

    validate = validar

    def cargar_entrada(self, cadena_entrada: str = ""):
        self.cinta.clear()
        self.posicion_cabezal = 0
        self.estado_actual = self.estado_inicial
        self.contador_pasos = 0
        self.detenida = False
        self.aceptada = False
        self.rechazada = False
        self.historial.clear()

        for i, caracter in enumerate(cadena_entrada):
            self.cinta[i] = caracter

        simbolo_inicial = self.obtener_simbolo_cinta(0)
        self.historial.append(
            RegistroPaso(
                numero_paso=0,
                estado_actual=self.estado_actual,
                simbolo_leido=simbolo_inicial,
                nuevo_estado=None,
                simbolo_escrito=None,
                direccion=None,
                posicion_cabezal=0,
                captura_cinta=self.obtener_cadena_cinta(),
                descripcion_estado="Inicio de la simulación"
            )
        )

        if self.estado_actual in self.estados_aceptacion:
            self.detenida = True
            self.aceptada = True
            self.historial[-1].descripcion_estado = "Parada: Cadena aceptada (Estado inicial es de aceptación)."

    load_input = cargar_entrada

    def obtener_simbolo_cinta(self, posicion: int) -> str:
        """Obtiene el símbolo en una posición dada de la cinta (o blanco)."""
        return self.cinta.get(posicion, self.simbolo_blanco)

    get_tape_symbol = obtener_simbolo_cinta

    def obtener_limites_cinta(self) -> Tuple[int, int]:
    
        indices = list(self.cinta.keys())
        indices.append(self.posicion_cabezal)
        min_indice = min(indices)
        max_indice = max(indices)
        return min_indice - 1, max_indice + 1

    get_tape_bounds = obtener_limites_cinta

    def obtener_cadena_cinta(self) -> str:
        min_indice, max_indice = self.obtener_limites_cinta()
        caracteres = []
        for i in range(min_indice, max_indice + 1):
            caracter = self.obtener_simbolo_cinta(i)
            if i == self.posicion_cabezal:
                caracteres.append(f"[{caracter}]")
            else:
                caracteres.append(caracter)
        return "".join(caracteres)

    get_tape_string = obtener_cadena_cinta

    def ejecutar_paso(self) -> Tuple[bool, str]:
        """
        Ejecuta un solo paso de la Máquina de Turing.
        Retorna (continua_ejecucion, mensaje_estado).
        """
        if self.detenida:
            if self.aceptada:
                return False, "La máquina ya se detuvo: Cadena ACEPTADA."
            elif self.rechazada:
                return False, "La máquina ya se detuvo: Cadena RECHAZADA."
            return False, "La máquina ya se detuvo."

        simbolo_actual = self.obtener_simbolo_cinta(self.posicion_cabezal)
        clave = ClaveTransicion(self.estado_actual, simbolo_actual)

        if clave not in self.transiciones:
            self.detenida = True
            if self.estado_actual in self.estados_aceptacion:
                self.aceptada = True
                mensaje = f"Parada en estado de aceptación '{self.estado_actual}'. Cadena ACEPTADA."
            else:
                self.rechazada = True
                mensaje = f"No hay transición para ({self.estado_actual}, '{simbolo_actual}'). Cadena RECHAZADA."

            if self.historial:
                self.historial[-1].descripcion_estado = mensaje
            return False, mensaje

        transicion = self.transiciones[clave]
        self.contador_pasos += 1

        self.cinta[self.posicion_cabezal] = transicion.simbolo_escrito

        if transicion.direccion == Direccion.IZQUIERDA:
            self.posicion_cabezal -= 1
        elif transicion.direccion == Direccion.DERECHA:
            self.posicion_cabezal += 1

        estado_anterior = self.estado_actual
        self.estado_actual = transicion.nuevo_estado

        mensaje = f"Paso {self.contador_pasos}: ({estado_anterior}, '{simbolo_actual}') -> ({transicion.nuevo_estado}, '{transicion.simbolo_escrito}', {transicion.direccion.value})"

        if self.estado_actual in self.estados_aceptacion:
            self.detenida = True
            self.aceptada = True
            mensaje += f" | Estado de Aceptación alcanzado: {self.estado_actual}. Cadena ACEPTADA."
        elif self.estado_actual in self.estados_rechazo:
            self.detenida = True
            self.rechazada = True
            mensaje += f" | Estado de Rechazo alcanzado: {self.estado_actual}. Cadena RECHAZADA."

        self.historial.append(
            RegistroPaso(
                numero_paso=self.contador_pasos,
                estado_actual=self.estado_actual,
                simbolo_leido=self.obtener_simbolo_cinta(self.posicion_cabezal),
                nuevo_estado=transicion.nuevo_estado,
                simbolo_escrito=transicion.simbolo_escrito,
                direccion=transicion.direccion,
                posicion_cabezal=self.posicion_cabezal,
                captura_cinta=self.obtener_cadena_cinta(),
                descripcion_estado=mensaje
            )
        )

        return not self.detenida, mensaje

    step = ejecutar_paso
    paso = ejecutar_paso

    def ejecutar(self, cadena_entrada: str = "", max_pasos: int = 2000) -> Tuple[bool, str, int]:
        """
        Ejecuta la máquina completa sobre una palabra dada hasta que se detenga o supere max_pasos.
        Retorna (es_aceptada, mensaje_final, total_pasos).
        """
        self.cargar_entrada(cadena_entrada)
        while not self.detenida and self.contador_pasos < max_pasos:
            continua, _ = self.ejecutar_paso()
            if not continua:
                break

        if not self.detenida:
            self.detenida = True
            self.rechazada = True
            return False, f"Se superó el límite de {max_pasos} pasos (posible bucle infinito).", self.contador_pasos

        resultado_texto = "ACEPTADA" if self.aceptada else "RECHAZADA"
        return self.aceptada, f"Ejecución finalizada en {self.contador_pasos} pasos: {resultado_texto}", self.contador_pasos

    run = ejecutar

    def a_diccionario(self) -> dict:
        """Serializa la máquina a un diccionario."""
        return {
            "nombre": self.nombre,
            "simbolo_blanco": self.simbolo_blanco,
            "alfabeto_entrada": sorted(list(self.alfabeto_entrada)),
            "alfabeto_cinta": sorted(list(self.alfabeto_cinta)),
            "estados": sorted(list(self.estados)),
            "estado_inicial": self.estado_inicial,
            "estados_aceptacion": sorted(list(self.estados_aceptacion)),
            "estados_rechazo": sorted(list(self.estados_rechazo)),
            "transiciones": [
                {
                    "estado": clave.estado,
                    "simbolo_leido": clave.simbolo,
                    "nuevo_estado": valor.nuevo_estado,
                    "simbolo_escrito": valor.simbolo_escrito,
                    "direccion": valor.direccion.value,
                }
                for clave, valor in sorted(self.transiciones.items(), key=lambda x: (x[0].estado, x[0].simbolo))
            ],
        }

    to_dict = a_diccionario

    @classmethod
    def desde_diccionario(cls, datos: dict) -> 'MaquinaTuring':
        nombre = datos.get("nombre") or datos.get("name", "Máquina de Turing")
        simbolo_blanco = datos.get("simbolo_blanco") or datos.get("blank_symbol", "B")
        alfabeto_entrada = set(datos.get("alfabeto_entrada") or datos.get("input_alphabet", []))
        alfabeto_cinta = set(datos.get("alfabeto_cinta") or datos.get("tape_alphabet", []))
        estados = set(datos.get("estados") or datos.get("states", []))
        estado_inicial = datos.get("estado_inicial") or datos.get("initial_state", "q0")
        estados_aceptacion = set(datos.get("estados_aceptacion") or datos.get("accept_states", []))
        estados_rechazo = set(datos.get("estados_rechazo") or datos.get("reject_states", []))

        mt = cls(
            nombre=nombre,
            estados=estados,
            alfabeto_entrada=alfabeto_entrada,
            alfabeto_cinta=alfabeto_cinta,
            simbolo_blanco=simbolo_blanco,
            estado_inicial=estado_inicial,
            estados_aceptacion=estados_aceptacion,
            estados_rechazo=estados_rechazo,
        )
        for t in datos.get("transiciones", []):
            est = t.get("estado") or t.get("state")
            r_sym = t.get("simbolo_leido") or t.get("read_symbol")
            n_est = t.get("nuevo_estado") or t.get("next_state")
            w_sym = t.get("simbolo_escrito") or t.get("write_symbol")
            d = t.get("direccion") or t.get("direction")
            mt.agregar_transicion(
                estado=est,
                simbolo_leido=r_sym,
                nuevo_estado=n_est,
                simbolo_escrito=w_sym,
                direccion=d,
            )
        return mt

    from_dict = desde_diccionario

    def a_json(self, sangria: int = 2) -> str:
    
        return json.dumps(self.a_diccionario(), indent=sangria, ensure_ascii=False)

    to_json = a_json

    @classmethod
    def desde_json(cls, cadena_json: str) -> 'MaquinaTuring':
        """Carga la máquina desde una cadena JSON."""
        return cls.desde_diccionario(json.loads(cadena_json))

    from_json = desde_json

    def obtener_matriz_transiciones(self) -> Tuple[List[str], List[str], Dict[Tuple[str, str], str]]:
        """
        Retorna la tabla de transiciones en forma de matriz:
        (estados_ordenados, simbolos_cinta_ordenados, celda: (estado, simbolo) -> "q',w,D")
        """
        estados = sorted(list(self.estados))
        simbolos = sorted(list(self.alfabeto_cinta))
        matriz: Dict[Tuple[str, str], str] = {}

        for clave, valor in self.transiciones.items():
            matriz[(clave.estado, clave.simbolo)] = f"({valor.nuevo_estado}, {valor.simbolo_escrito}, {valor.direccion.value})"

        return estados, simbolos, matriz

    get_transition_matrix = obtener_matriz_transiciones

    @staticmethod
    def analizar_celda_transicion(cadena_celda: str) -> Optional[Tuple[str, str, Direccion]]:
        s = cadena_celda.strip()
        if not s or s in ('-', '—', 'none', 'null', '/', 'lambda', 'eps'):
            return None
        s = s.strip('()[]{}<>')
        partes = [p.strip() for p in re.split(r'[,;/\s]+', s) if p.strip()]
        if len(partes) == 3:
            nuevo_est, simb_escrito, dir_cadena = partes
            return nuevo_est, simb_escrito, Direccion.desde_cadena(dir_cadena)
        elif len(partes) == 1:
            raise ValueError(f"La celda '{cadena_celda}' debe incluir (nuevo_estado, símbolo_escrito, dirección L/R/S).")
        raise ValueError(f"Formato no reconocido en celda: '{cadena_celda}'. Se esperaba (estado, símbolo, dirección).")

    parse_transition_cell = analizar_celda_transicion

    @staticmethod
    def separar_fila_inteligente(fila_str: str) -> List[str]:
        fila_str = fila_str.strip()
        if '\t' in fila_str:
            return [c.strip().strip('"\'') for c in fila_str.split('\t')]
        if ';' in fila_str and '(' not in fila_str:
            return [c.strip().strip('"\'') for c in fila_str.split(';')]

        elementos = []
        actual = []
        en_parentesis = 0
        for ch in fila_str:
            if ch in '([{<':
                en_parentesis += 1
                actual.append(ch)
            elif ch in ')]}>':
                en_parentesis = max(0, en_parentesis - 1)
                actual.append(ch)
            elif (ch == ',' or ch == ';') and en_parentesis == 0:
                token = ''.join(actual).strip().strip('"\'')
                elementos.append(token)
                actual = []
            else:
                actual.append(ch)
        elementos.append(''.join(actual).strip().strip('"\''))
        return elementos

    smart_split_row = separar_fila_inteligente

    def establecer_transiciones_matriz(
        self,
        datos_matriz: Dict[Tuple[str, str], str],
        limpiar_existentes: bool = True
    ) -> Tuple[int, List[str]]:
        if limpiar_existentes:
            self.transiciones.clear()

        agregadas = 0
        errores = []

        for (est, sym), valor_celda in datos_matriz.items():
            if not valor_celda or not valor_celda.strip():
                continue
            try:
                analizada = self.analizar_celda_transicion(valor_celda)
                if analizada:
                    nuevo_est, w_sym, d = analizada
                    self.agregar_transicion(est, sym, nuevo_est, w_sym, d)
                    agregadas += 1
            except Exception as e:
                errores.append(f"Error en celda ({est}, '{sym}'): {e}")

        return agregadas, errores

    set_matrix_transitions = establecer_transiciones_matriz

    def a_csv(self) -> str:
        estados = sorted(list(self.estados))
        simbolos = sorted(list(self.alfabeto_cinta))
        _, _, matriz = self.obtener_matriz_transiciones()

        salida = io.StringIO()
        escritor = csv.writer(salida)
        escritor.writerow(["Estado"] + simbolos)

        for est in estados:
            fila = [est]
            for sym in simbolos:
                valor_celda = matriz.get((est, sym), "")
                fila.append(valor_celda)
            escritor.writerow(fila)

        return salida.getvalue()

    to_csv = a_csv

    def importar_desde_texto(self, texto_bruto: str, limpiar_existentes: bool = True) -> Tuple[bool, str, int]:
        lineas = [l.strip() for l in texto_bruto.splitlines() if l.strip() and not l.strip().startswith("#")]
        if not lineas:
            return False, "El texto proporcionado está vacío.", 0

        if limpiar_existentes:
            self.transiciones.clear()

        primera_fila = self.separar_fila_inteligente(lineas[0])
        es_matriz = len(primera_fila) >= 2 and (
            primera_fila[0].lower() in ("estado", "state", "q", "estados", "q/σ", "q/sigma", "q\\sigma")
            or any(s in self.alfabeto_cinta for s in primera_fila[1:])
        )

        agregadas = 0
        errores = []

        if es_matriz:
            simbolos = [s for s in primera_fila[1:] if s]
            for sym in simbolos:
                self.alfabeto_cinta.add(sym)

            for linea in lineas[1:]:
                fila = self.separar_fila_inteligente(linea)
                if not fila or not fila[0]:
                    continue
                estado = fila[0]
                self.estados.add(estado)
                for col_idx, celda in enumerate(fila[1:]):
                    if col_idx < len(simbolos):
                        sym = simbolos[col_idx]
                        if celda.strip():
                            try:
                                analizada = self.analizar_celda_transicion(celda)
                                if analizada:
                                    nuevo_est, w_sym, d = analizada
                                    self.agregar_transicion(estado, sym, nuevo_est, w_sym, d)
                                    agregadas += 1
                            except Exception as e:
                                errores.append(f"Fila {estado}, col '{sym}': {e}")

            msg = f"Se cargaron con éxito {agregadas} transiciones desde la matriz 2D."
            if errores:
                msg += f" (Con {len(errores)} advertencias: {'; '.join(errores[:3])})"
            return True, msg, agregadas

        for num_linea, linea in enumerate(lineas, 1):
            limpia = re.sub(r'[\(\)\[\]\->=,;]+', ' ', linea)
            partes = limpia.split()
            if len(partes) >= 5:
                est, r_sym, nuevo_est, w_sym, d_str = partes[:5]
                try:
                    self.agregar_transicion(est, r_sym, nuevo_est, w_sym, d_str)
                    agregadas += 1
                except Exception as e:
                    errores.append(f"Línea {num_linea} ('{linea}'): {e}")
            else:
                errores.append(f"Línea {num_linea}: No tiene 5 campos requeridos ({linea})")

        if agregadas > 0:
            msg = f"Se cargaron con éxito {agregadas} transiciones desde la lista."
            if errores:
                msg += f" (Se omitieron {len(errores)} líneas con advertencias)."
            return True, msg, agregadas
        else:
            return False, f"No se pudo interpretar el formato de las transiciones. Errores: {'; '.join(errores[:3])}", 0

    import_from_text = importar_desde_texto

TuringMachine = MaquinaTuring
