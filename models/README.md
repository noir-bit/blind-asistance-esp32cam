# Modelos de Redes Neuronales

Para evitar saturar el repositorio con archivos binarios extremadamente pesados (los cuales pueden ser bloqueados por los límites de tamaño de archivo de GitHub), los modelos **NO se suben directamente al repositorio**. 

En su lugar, deben colocarse localmente en esta carpeta (`models/`) antes de ejecutar los clientes correspondientes.

---

## 1. Modelo YOLOv8 Personalizado (Detección de Obstáculos)

Este es el modelo entrenado con el dataset de Roboflow `road-obstacles-ur2wn` a resolución `512` y con optimizaciones de velocidad.

### ONNX (Para PC y Python en Termux)
*   **Nombre de archivo requerido**: `best.onnx`
*   **Instrucciones**: Descarga tu archivo exportado de Kaggle y cópialo en esta carpeta con el nombre exacto de `best.onnx`.

### TFLite INT8 Quantized (Para Apps de Android Studio)
*   **Nombre de archivo recomendado**: `best_int8.tflite`
*   **Instrucciones**: Mueve este archivo al directorio `assets` de tu proyecto de Android Studio.

---

## 2. Modelo YOLOv8 Estándar (COCO)

Este modelo es autodescargable en el cliente `yolov8s_coco_client.py`, pero si deseas colocarlo manualmente:

*   **Nombre de archivo requerido**: `yolov8s.onnx`
*   **Enlace de descarga directa**: [yolov8s.onnx (GitHub Oficial de Ultralytics)](https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8s.onnx)
*   **Instrucciones**: Descárgalo y guárdalo dentro de esta carpeta con el nombre exacto de `yolov8s.onnx`.
