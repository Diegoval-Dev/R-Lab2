# Lab 2: Comunicación de Tramas con Detección y Corrección de Errores

Este repositorio implementa un sistema emisor–receptor que genera, transmite y verifica tramas de datos con técnicas de detección y corrección de errores. Incluye una interfaz gráfica interactiva basada en Streamlit para monitorear el intercambio de tramas en tiempo real.

## Tabla de Contenidos

- [Arquitectura](#arquitectura)  
- [Objetivos](#objetivos)  
- [Estructura del Repositorio](#estructura-del-repositorio)  
- [Requisitos Previos](#requisitos-previos)  
- [Instalación y Ejecución](#instalación-y-ejecución)  
- [Uso Básico](#uso-básico)  
- [Pruebas y Calidad](#pruebas-y-calidad)  

## Arquitectura

### Emisor (Go)

Construye tramas aplicando algoritmos de CRC-32, Hamming u otras técnicas y las envía por WebSocket.

- Paquete `crc32`: cálculo y verificación de CRC-32  
- Paquete `hamming`: codificación y decodificación con corrección de errores  
- Paquete `ws`: servidor WebSocket que publica las tramas  

#### Opciones de Ejecución

- `--ws-server`: dirección del receptor (por defecto `ws://localhost:9000`)  
- `--frame-rate`: velocidad de emisión (frames por segundo)  
- `--seed`: semilla aleatoria para reproducibilidad  

#### Flujo de Trabajo

1. Genera datos aleatorios de prueba  
2. Aplica CRC y/o Hamming  
3. Envía la trama al receptor vía WebSocket  

### Receptor + GUI (Python + Streamlit)

Actúa como cliente WebSocket, recibe las tramas, aplica los algoritmos para verificar y, si es posible, corregir errores. Muestra el estado de cada trama en una app web sencilla.

## Objetivos

- Demostrar algoritmos clásicos de detección y corrección de errores en un entorno de red simulado  
- Diseñar una arquitectura modular que separe la lógica de bajo nivel (Go) de la capa de presentación (Python)  
- Proporcionar una herramienta visual para validar y depurar tramas transmitidas  

## Estructura del Repositorio

- **emitter-go/**: código del emisor en Go  
- **receiver-py/**: código del receptor y GUI en Python + Streamlit  
- **docs/**: diagramas de arquitectura, especificación de formato de trama, ejemplos  
- **tests/**: suites de pruebas unitarias para Go y Python  

## Requisitos Previos

- Go v1.20+  
- Python 3.8+  
- pip (instalar dependencias Python)  
- Conexión de red local o remota para WebSockets  

## Instalación y Ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/Diegoval-Dev/R-Lab2
cd R-lab2
```

### 2. Compilar el Emisor (Go)

```bash
cd emitter-go
go build ./cmd/emitter
```

### 3. Configurar el Entorno Python

```bash
cd ../receiver-py
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Ejecutar el Emisor

```bash
cd ../emitter-go
./emitter --ws-server ws://localhost:9000
```

### 5. Iniciar la Interfaz Streamlit

```bash
cd ../receiver-py
streamlit run src/streamlit_app.py
```

Abrir el navegador en http://localhost:8501

## Uso Básico

- El emisor genera y envía tramas automáticamente al receptor  
- La app Streamlit refresca cada 0.5 s y muestra:  
  - Trama recibida (binario o JSON)  
  - Resultado de verificación (OK / Error)  
  - Trama corregida y posiciones de bits corregidos (si aplica)  

## Pruebas y Calidad

- **Python**: desde `receiver-py/` ejecutar `pytest`  
- **Go**: desde `emitter-go/` ejecutar `go test ./pkg/frame`  