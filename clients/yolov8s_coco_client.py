import cv2
import urllib.request
import numpy as np
import time
import os
import sys

# --- CONFIGURACIÓN ---
URL_ESP32 = "http://10.17.123.130"   # Cambia por la IP de tu ESP32-CAM
MODEL_PATH = "yolov8s.onnx"          # YOLOv8s
IMG_SIZE = 640                       # YOLOv8s original de COCO usa 640x640
CONF_THRESHOLD = 0.45                # Umbral de confianza
NMS_THRESHOLD = 0.40

# Clases filtradas (COCO dataset) y sus nombres adaptados en español para el audio
NOMBRES_CLASES_ES = {
    0: "persona",
    1: "bicicleta",
    2: "carro",
    3: "motocicleta",
    4: "avion",
    5: "autobus",
    6: "tren",
    7: "camion",
    8: "barco",
    9: "semaforo",
    10: "hidrante",
    11: "alto",          # 'stop sign' -> "alto"
    12: "parquimetro"    # 'parking meter' -> "parquimetro"
}

CLASES_INTERES = list(NOMBRES_CLASES_ES.keys())

def descargar_modelo_si_no_existe():
    # Buscar el modelo en el directorio actual o en models/
    global MODEL_PATH
    if not os.path.exists(MODEL_PATH):
        posible_ruta = os.path.join("models", MODEL_PATH)
        if os.path.exists(posible_ruta):
            MODEL_PATH = posible_ruta
            return
        posible_ruta = os.path.join("..", "models", MODEL_PATH)
        if os.path.exists(posible_ruta):
            MODEL_PATH = posible_ruta
            return

        # Si de verdad no existe, se descarga en la carpeta raíz/models
        carpeta_modelos = "models"
        if not os.path.exists(carpeta_modelos):
            os.makedirs(carpeta_modelos)
        MODEL_PATH = os.path.join(carpeta_modelos, MODEL_PATH)
        
        print("----------------------------------------------------------------")
        print("El modelo yolov8s.onnx no se encuentra localmente.")
        print("Descargando modelo oficial YOLOv8s ONNX de Ultralytics (~44.5 MB)...")
        print("Esto puede tardar un momento dependiendo de tu conexión.")
        print("----------------------------------------------------------------")
        url = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8s.onnx"
        try:
            urllib.request.urlretrieve(url, MODEL_PATH)
            print("¡Descarga de YOLOv8s ONNX finalizada correctamente!")
        except Exception as e:
            print(f"Error al descargar el modelo: {e}")
            print("Por favor, descárgalo manualmente y colócalo en la carpeta 'models/' con el nombre 'yolov8s.onnx'.")
            sys.exit(1)

def verificar_y_generar_audios():
    carpeta = "audios"
    # Buscar la carpeta audios
    if not os.path.exists(carpeta):
        posible_ruta = os.path.join("..", "audios")
        if os.path.exists(posible_ruta):
            carpeta = posible_ruta
        else:
            os.makedirs(carpeta)

    # Audios necesarios
    audios_necesarios = {
        "peligro": "Peligro",
        "izquierda": "a la izquierda",
        "derecha": "a la derecha",
        "centro": "al centro",
        "adelante": "adelante"
    }
    
    # Agregar las clases traducidas
    for clase_id, nombre in NOMBRES_CLASES_ES.items():
        audios_necesarios[nombre] = nombre.replace("alto", "señal de alto").replace("avion", "avión").replace("autobus", "autobús").replace("camion", "camión").replace("semaforo", "semáforo").replace("parquimetro", "parquímetro")

    faltan_audios = False
    for archivo in audios_necesarios.keys():
        if not os.path.exists(os.path.join(carpeta, f"{archivo}.mp3")):
            faltan_audios = True
            break

    if faltan_audios:
        print("Detectando audios faltantes. Generándolos de forma automática...")
        try:
            from gtts import gTTS
            for archivo, texto in audios_necesarios.items():
                ruta_mp3 = os.path.join(carpeta, f"{archivo}.mp3")
                if not os.path.exists(ruta_mp3):
                    print(f"Generando audio para: '{texto}' -> {ruta_mp3}")
                    tts = gTTS(text=texto, lang='es', slow=False)
                    tts.save(ruta_mp3)
            print("¡Todos los audios necesarios han sido generados exitosamente!")
        except ImportError:
            print("\n[ADVERTENCIA]: Faltan archivos de audio y la librería 'gtts' no está instalada.")
            print("Por favor ejecuta: pip install gtts")
            print("El script continuará en modo silencioso (solo texto).\n")

def reproducir_audio(archivo):
    # Buscar el audio en 'audios' o '../audios'
    ruta = f"audios/{archivo}.mp3"
    if not os.path.exists(ruta):
        ruta = f"../audios/{archivo}.mp3"
        if not os.path.exists(ruta):
            print(f"[Audio no encontrado]: {archivo}")
            return
            
    if os.path.exists(ruta):
        if os.path.exists("/data/data/com.termux"):
            os.system(f"termux-media-player play {ruta} > /dev/null 2>&1")
            time.sleep(1.0)
        else:
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(ruta)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
            except:
                print(f"[REPRODUCIENDO]: {ruta}")
                time.sleep(0.5)

def alertar(objeto, posicion):
    print(f"\n📢 ALERTA CRÍTICA: Peligro, {objeto} a la {posicion.upper()}")
    reproducir_audio("peligro")
    reproducir_audio(objeto)
    reproducir_audio(posicion.lower())

def main():
    descargar_modelo_si_no_existe()
    verificar_y_generar_audios()

    print("\nIniciando detector OpenCV con YOLOv8s...")
    try:
        net = cv2.dnn.readNetFromONNX(MODEL_PATH)
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        print("¡Modelo loaded correctamente!")
    except Exception as e:
        print(f"Error al inicializar la red ONNX: {e}")
        sys.exit(1)

    print(f"Conectando al stream del ESP32-CAM en: {URL_ESP32}...")
    ultimo_audio = 0
    cooldown = 2.5 

    while True:
        try:
            respuesta = urllib.request.urlopen(URL_ESP32, timeout=5)
            img_arr = np.array(bytearray(respuesta.read()), dtype=np.uint8)
            frame = cv2.imdecode(img_arr, -1)
            
            if frame is None:
                continue

            h_orig, w_orig = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(frame, 1/255.0, (IMG_SIZE, IMG_SIZE), swapRB=True, crop=False)
            net.setInput(blob)
            
            salidas = net.forward()[0].T # Transponer a (8400, 84)

            cajas = []
            confianzas = []
            ids_clases = []

            x_factor = w_orig / IMG_SIZE
            y_factor = h_orig / IMG_SIZE

            for fila in salidas:
                scores = fila[4:]
                id_clase = np.argmax(scores)
                conf = scores[id_clase]

                if conf > CONF_THRESHOLD and id_clase in CLASES_INTERES:
                    cx, cy, w, h = fila[0:4]
                    x = int((cx - w/2) * x_factor)
                    y = int((cy - h/2) * y_factor)
                    cajas.append([x, y, int(w * x_factor), int(h * y_factor)])
                    confianzas.append(float(conf))
                    ids_clases.append(id_clase)

            indices = cv2.dnn.NMSBoxes(cajas, confianzas, CONF_THRESHOLD, NMS_THRESHOLD)

            detectados = []
            if len(indices) > 0:
                for i in indices.flatten():
                    x, y, w, h = cajas[i]
                    centro_x = x + w/2
                    
                    if centro_x < (w_orig / 3):
                        pos = "Izquierda"
                    elif centro_x > (w_orig / 3) * 2:
                        pos = "Derecha"
                    else:
                        pos = "Centro"

                    nombre_es = NOMBRES_CLASES_ES[ids_clases[i]]
                    area = w * h
                    detectados.append({"nombre": nombre_es, "posicion": pos, "area": area})

            if detectados:
                detectados.sort(key=lambda x: x['area'], reverse=True)
                peligro = detectados[0]
                
                print(f"Objetos en pantalla: {[f'{d[\"nombre\"]}({d[\"posicion\"]})' for d in detectados]}")
                
                if time.time() - ultimo_audio > cooldown:
                    alertar(peligro["nombre"], peligro["posicion"])
                    ultimo_audio = time.time()
            else:
                print("Camino libre...", end="\r", flush=True)

        except KeyboardInterrupt:
            print("\nPrograma detenido.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
