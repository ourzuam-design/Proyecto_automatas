# 🧠 Simulador y Diseñador de Máquinas de Turing en Python

Un software didáctico y formal desarrollado en **Python** para diseñar, visualizar y simular **Máquinas de Turing Deterministas (MT)** de una cinta.

Permite ingresar formalmente cualquier alfabeto de entrada $\Sigma$, alfabeto de cinta $\Gamma$, símbolo blanco $B$, estados $Q$, estado inicial $q_0$, estados de aceptación $F$, y la **tabla de transiciones** $\delta(q, \sigma) \to (q', \sigma', D)$.

---

## 🌟 Características Principales

1. **Definición Formal Completa**:
   - Alfabeto de entrada $\Sigma$ y de cinta $\Gamma$.
   - Símbolo blanco configurable (ej. `B`, `_`).
   - Estados iniciales, de aceptación y rechazo.
   - Editor de transiciones $\delta(q, \sigma) \to (q', \sigma', D)$ con dirección $D \in \{L, R, S\}$ (Izquierda, Derecha, Quieto).
   - Validador formal automático que detecta estados huérfanos, símbolos no declarados o inconsistencias teóricas.

2. **Simulador de Cinta Gráfico y Paso a Paso**:
   - Visualización interactiva de la cinta bidireccional con cabezal lector/escritor centrado.
   - Modos de ejecución: **Paso a Paso** (`Step`), **Ejecución Automática** (`Play / Pausa`) con slider de velocidad configurable en milisegundos.
   - Registro y bitácora detallada de todas las configuraciones instantáneas $u\, q\, v$.
   - Detección precisa de cadenas **Aceptadas**, **Rechazadas** o parada por ausencia de transición.

3. **Grafo Visual Interactivo**:
   - **Diagrama en Ventana (Tkinter Canvas)**: Grafica los estados en círculos (con doble círculo para aceptación y flecha de inicio), aristas dirigidas y auto-curvadas para transiciones bidireccionales, y bucles para auto-transiciones.
   - **Arrastrar y Soltar**: Puedes hacer clic en cualquier estado y moverlo para reorganizar el grafo como prefieras.
   - **Resaltado en Vivo**: El estado activo durante la simulación de la cinta se ilumina en amarillo en el grafo.

4. **Ejemplos Clásicos Predefinidos**:
   - Reconocedor del lenguaje $a^n b^n$ ($n \ge 1$).
   - Incrementador binario ($w + 1$, ej. `1011` $\to$ `1100`).
   - Reconocedor de palíndromos sobre $\{a, b\}$.
   - Inversor de bits (Complemento a 1).
   - Guardar y cargar autómatas en formato estándar **JSON**.

---

## 🚀 Requisitos e Instalación

El programa utiliza únicamente la **biblioteca estándar de Python** (incluyendo `tkinter`), por lo que **no necesitas instalar ninguna librería externa pesada**.

- **Python 3.8 o superior** instalado en el sistema.

Verifica tu versión con:
```bash
python --version
```

---

## 💻 Cómo Ejecutar el Programa

### Modo Interfaz Gráfica (Recomendado)
Para abrir la interfaz visual completa:
```bash
python main.py
```

### Modo Consola / Terminal (CLI)
Si prefieres interactuar mediante la línea de comandos:
```bash
python main.py --cli
```

---

## 📖 Guía de Uso de la Interfaz Gráfica

La aplicación cuenta con 3 pestañas principales:

### Pestaña 1: Definición y Transiciones
1. **Nuevo Autómata en Blanco**: Presiona **"Nuevo en Blanco"** en la barra superior (o selecciona `[En blanco]` en el selector) para limpiar todos los campos y comenzar a definir un autómata desde cero.
2. **Formalismo**: Ingresa el nombre, alfabeto de entrada $\Sigma$, símbolo blanco $B$, alfabeto de cinta $\Gamma$, conjunto de estados $Q$, estado inicial $q_0$ y estados de aceptación $F$.
3. **Editor de Transiciones (3 Modos Integrados)**:
   - **Matriz 2D Interactiva**: Cuadrícula bidireccional donde las filas son los estados $q \in Q$ y las columnas son los símbolos del alfabeto $\sigma \in \Gamma$. Permite editar directamente cada celda con el formato `(nuevo_estado, símbolo_escrito, dirección)`. Si una celda se deja vacía, representa parada.
   - **Pegar / Importar CSV o Texto**: Permite pegar una matriz en formato CSV o TSV (copiada directamente de Excel o Google Sheets) o una lista de transiciones una por línea (`q0 0 q1 X R`), además de cargar archivos `.csv` o `.txt`.
   - **Vista en Lista**: Editor tradicional fila por fila con formulario rápido y tabla.
4. **Generar Autómata**: Presiona el botón **"Generar Autómata"** para compilar la tabla de transiciones, validar formalmente la máquina, dibujar automáticamente el grafo de estados y pasar de inmediato a la pestaña del diagrama.
5. **Cargar Ejemplo**: En la barra superior, usa el desplegable para cargar máquinas clásicas preconfiguradas.
6. **Validar Autómata**: Presiona **Validar Autómata** para comprobar la consistencia teórica.

### Pestaña 2: Simulador de Cinta
1. Escribe la palabra que deseas probar en el campo **Cadena de Entrada**.
2. Presiona **Cargar Palabra**.
3. Utiliza los botones:
   - **Paso a Paso**: Ejecuta una transición a la vez para estudiar el comportamiento de la máquina.
   - **Ejecutar / Pausa**: Simula automáticamente a la velocidad elegida en el deslizador.
   - **Reiniciar**: Regresa la cinta a su estado inicial.
4. Observa el movimiento del cabezal sobre la cinta y la tabla inferior con la bitácora de cada paso.

### Pestaña 3: Diagrama del Autómata
1. Visualiza el diagrama de estados y transiciones en tiempo real.
2. Haz clic sobre cualquier círculo de estado y arrástralo para posicionarlo donde mejor se aprecie.

---

## 📁 Estructura del Proyecto

```text
Proyecto automatas/
│
├── main.py            # Punto de entrada principal (GUI o CLI)
├── turing_machine.py  # Motor formal de la Máquina de Turing y simulación
├── gui.py             # Interfaz Gráfica con Tkinter y Canvas interactivo
├── graph_renderer.py  # Cálculo de distribución de nodos para el grafo
├── examples_data.py   # Máquinas de Turing clásicas preconfiguradas
└── README.md          # Documentación detallada
```

---

## 📜 Formato de Archivos JSON

Los autómatas pueden guardarse y cargarse fácilmente mediante archivos `.json` con la siguiente estructura (soporta tanto nombres en español como en inglés):

```json
{
  "nombre": "Incrementador Binario (w + 1)",
  "simbolo_blanco": "B",
  "alfabeto_entrada": ["0", "1"],
  "alfabeto_cinta": ["0", "1", "B"],
  "estados": ["q0", "q1", "q_accept"],
  "estado_inicial": "q0",
  "estados_aceptacion": ["q_accept"],
  "estados_rechazo": [],
  "transiciones": [
    {
      "estado": "q0",
      "simbolo_leido": "0",
      "nuevo_estado": "q0",
      "simbolo_escrito": "0",
      "direccion": "R"
    },
    {
      "estado": "q0",
      "simbolo_leido": "B",
      "nuevo_estado": "q1",
      "simbolo_escrito": "B",
      "direccion": "L"
    }
  ]
}
```
