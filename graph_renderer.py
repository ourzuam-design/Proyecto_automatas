import math
from typing import Dict, Tuple, List


class DistribucionGrafo:
    
    @staticmethod
    def calcular_posiciones(
        estados: List[str],
        estado_inicial: str,
        ancho: float = 700.0,
        alto: float = 500.0,
        margen: float = 80.0
    ) -> Dict[str, Tuple[float, float]]:
        
        total_estados = len(estados)
        if total_estados == 0:
            return {}
        if total_estados == 1:
            return {estados[0]: (ancho / 2, alto / 2)}

        ordenados = [estado_inicial] + [e for e in estados if e != estado_inicial]
        posiciones: Dict[str, Tuple[float, float]] = {}

        centro_x = ancho / 2
        centro_y = alto / 2
        radio_x = max(100.0, (ancho - 2 * margen) / 2)
        radio_y = max(80.0, (alto - 2 * margen) / 2)

        for i, estado in enumerate(ordenados):
            angulo = math.pi + (2 * math.pi * i / total_estados)
            pos_x = centro_x + radio_x * math.cos(angulo)
            pos_y = centro_y + radio_y * math.sin(angulo)
            posiciones[estado] = (round(pos_x, 1), round(pos_y, 1))

        return posiciones
