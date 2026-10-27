"""
Módulo de Visualización y Renderizado del Grafo de la Máquina de Turing.
Permite calcular la distribución de nodos del autómata para su renderizado en Tkinter Canvas.
"""

import math
from typing import Dict, Tuple, List


class GraphLayout:
    """Calcula las posiciones (x, y) de los estados del autómata."""

    @staticmethod
    def compute_positions(
        states: List[str],
        initial_state: str,
        width: float = 700.0,
        height: float = 500.0,
        padding: float = 80.0
    ) -> Dict[str, Tuple[float, float]]:
        """
        Calcula una distribución circular ordenada poniendo el estado inicial al inicio.
        """
        n = len(states)
        if n == 0:
            return {}
        if n == 1:
            return {states[0]: (width / 2, height / 2)}

        # Ordenar para que el estado inicial quede a la izquierda (ángulo pi)
        ordered = [initial_state] + [s for s in states if s != initial_state]
        positions: Dict[str, Tuple[float, float]] = {}

        cx = width / 2
        cy = height / 2
        rx = max(100.0, (width - 2 * padding) / 2)
        ry = max(80.0, (height - 2 * padding) / 2)

        for i, state in enumerate(ordered):
            angle = math.pi + (2 * math.pi * i / n)
            x = cx + rx * math.cos(angle)
            y = cy + ry * math.sin(angle)
            positions[state] = (round(x, 1), round(y, 1))

        return positions
