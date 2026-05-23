# YOLOv8 Road Obstacle Detection & Audio Alert System

Este repositorio contiene el sistema completo para la detección de obstáculos en carretera y alertas auditivas secuenciales en tiempo real (por ejemplo: *Peligro, bache al centro*), utilizando una **ESP32-CAM** como capturador de video y un cliente en **Python (Termux en celular o PC)** ejecutando **YOLOv8**.

---

##  Arquitectura del Proyecto

```text
road-obstacle-detector/
├── .gitignore                   # Archivos excluidos del control de versiones
├── README.md                    # Documentación principal
├── firmware/
│   └── esp32_cam_server/
│       └── esp32_cam_server.ino # Código Arduino para la ESP32-CAM
├── clients/
│   ├── generar_audios.py        # Generador de voces usando gTTS
│   ├── yolov8_audio_client.py   # Cliente YOLOv8 con tu modelo personalizado (512px)
│   └── yolov8s_coco_client.py   # Cliente YOLOv8s estándar COCO (640px, 80 clases)
└── models/
    └── README.md                # Indicaciones para descargar archivos de pesos (.onnx / .tflite)
```

---

##  1. ESP32-CAM (Firmware)

El código del servidor web de video se encuentra en [firmware/esp32_cam_server/esp32_cam_server.ino](firmware/esp32_cam_server/esp32_cam_server.ino).

### Conexión y Carga en Arduino IDE
1. Agrega la URL de placas ESP32 en **Preferencias**:
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
2. Ve al **Gestor de Tarjetas** e instala `esp32 by Espressif Systems`.
3. Selecciona la placa `AI Thinker ESP32-CAM` con esquema de partición `Huge APP (3MB No OTA)`.
4. Edita el archivo `esp32_cam_server.ino` con las credenciales de tu red WiFi:
   ```cpp
   const char* ssid = "TU_WIFI";
   const char* password = "TU_PASSWORD";
   ```
5. Pon la placa en modo flash (puente entre **GPIO 0 y GND**), sube el código y luego retira el puente y reinicia la placa.

---

##  2. Clientes Python (Celular con Termux / PC)

Los clientes de procesamiento de Inteligencia Artificial se ejecutan en Python y se conectan vía HTTP al stream de la ESP32-CAM.

### Configuración inicial (Ejemplo en Termux)
1. Instala los paquetes del sistema y OpenCV:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python python-numpy opencv termux-api -y
   termux-setup-storage
   ```
2. Instala la librería para generar voces:
   ```bash
   pip install gtts
   ```

### Generación de Audios
Para generar los audios en español de manera local ejecutando el script generador:
```bash
python clients/generar_audios.py
```
Esto creará una carpeta `audios/` con los archivos `.mp3` secuenciales correspondientes (como *peligro.mp3*, *persona.mp3*, *derecha.mp3*, etc.).

---

##  3. Opciones de Detección

### Opción A: Modelo Personalizado (Detección de Obstáculos en Carretera)
Utiliza el modelo optimizado que entrenamos a resolución `512` con 80 épocas en Kaggle sobre el dataset de Roboflow **`road-obstacles-ur2wn`**.
*   **Modelo recomendado para celular**: `best_int8.tflite` (~3 MB).
*   **Modelo para PC/Termux**: `best.onnx` (Carga con OpenCV DNN).
*   **Clases detectadas**: Perro de la calle, Poste, Letrero, Escaleras, Árbol, Vehículo de dos ruedas, Vehículo.

**Ejecución**:
```bash
python clients/yolov8_audio_client.py
```

### Opción B: Modelo Complejo YOLOv8s (Clases Estándar COCO)
Para detectar elementos cotidianos del entorno urbano como peatones, vehículos de todo tipo y elementos de señalización de tráfico.
*   **Modelo**: `yolov8s.onnx` (Se descarga automáticamente al arrancar el script).
*   **Clases detectadas**: Persona, bicicleta, carro, motocicleta, avión, autobús, tren, camión, barco, semáforo, hidrante, señal de alto (`stop sign`), parquímetro.

**Ejecución**:
```bash
python clients/yolov8s_coco_client.py
```

---

##  Detalles del Entrenamiento YOLOv8 Personalizado
*   **Dataset**: Roboflow (jaggyj/road-obstacles-ur2wn Version 3).
*   **Arquitectura**: YOLOv8n (Nano) para máxima velocidad en dispositivos móviles.
*   **Hiperparámetros**:
    *   `imgsz=512` (Equilibrio perfecto de precisión y FPS).
    *   `epochs=80`.
    *   `batch=8`.
    *   **Augmentations**: Mosaic (1.0), Mixup (0.1), Scale (0.5), Degrees (10).
*   **Formatos exportados**: ONNX, TFLite INT8 (optimizado para Android).
