import cv2
import urllib.request
import numpy as np
import json
import time
import os
import sys

# --- CONFIGURACIÓN ---
URL_ESP32 = "http://10.17.123.130"   # Cambia a la IP de tu ESP32-CAM
MODEL_PATH = "best.onnx"            # Nombre de tu modelo entrenado en Kaggle (ONNX)
IMG_SIZE = 512                      # Cambiar a 512 ya que entrenaste con imgsz=512
CONF_THRESHOLD = 0.40               # Confianza mínima
NMS_THRESHOLD = 0.40                # Umbral para no encimar cajas

# Nombres de las clases que entrenaste (road-obstacles-ur2wn)
NOMBRES_CLASES = {
    0: "indian-street-dog",
    1: "pole",
    2: "signboard",
    3: "stairs",
    4: "tree",
    5: "two-wheeler-vehicle",
    6: "vehicle"
}

# Inicializar reproductor de audio
AUDIO_SUPPORT = None
try:
    import pygame
    pygame.mixer.init()
    AUDIO_SUPPORT = "pygame"
    print("-> Soporte de audio: pygame cargado correctamente.")
except ImportError:
    if os.name != 'nt' and os.path.exists('/data/data/com.termux'):
        AUDIO_SUPPORT = "termux"
        print("-> Soporte de audio: Termux (comandos de sistema).")
    else:
        AUDIO_SUPPORT = "print_only"
        print("-> Soporte de audio: Ninguno (solo se imprimirán alertas). Instala pygame: pip install pygame")

def reproducir_archivo(ruta_audio):
    # Si no existe el audio, buscamos en la carpeta 'audios'
    if not os.path.exists(ruta_audio):
        base = os.path.basename(ruta_audio)
        ruta_audio = os.path.join("audios", base)
        if not os.path.exists(ruta_audio):
            # Intentar también subiendo un nivel si se ejecuta desde subcarpetas
            ruta_audio = os.path.join("..", "audios", base)
            if not os.path.exists(ruta_audio):
                print(f"[Audio no encontrado]: {base}")
                return

    if AUDIO_SUPPORT == "pygame":
        try:
            pygame.mixer.music.load(ruta_audio)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        except Exception as e:
            print(f"Error al reproducir con pygame: {e}")
    elif AUDIO_SUPPORT == "termux":
        os.system(f"termux-media-player play {ruta_audio} > /dev/null 2>&1")
        time.sleep(1.0) 
    else:
        print(f"[REPRODUCIENDO]: {ruta_audio}")
        time.sleep(0.5)

def alertar_peligro(objeto_nombre, posicion):
    print(f"\n📢 ALERTA: Peligro, {objeto_nombre} a la {posicion}")
    
    # 1. Reproducir "Peligro"
    reproducir_archivo("peligro.mp3")
    
    # 2. Reproducir el nombre del objeto
    nombre_limpio = objeto_nombre.lower().replace("í", "i").replace("ú", "u").replace("é", "e").replace("á", "a").replace("ó", "o")
    reproducir_archivo(f"{nombre_limpio}.mp3")
    
    # 3. Reproducir la dirección
    posicion_limpia = posicion.lower()
    reproducir_archivo(f"{posicion_limpia}.mp3")

# Cargar Red Neuronal (ONNX)
print(f"Cargando modelo YOLOv8 ({MODEL_PATH}) a resolución {IMG_SIZE}x{IMG_SIZE}...")
try:
    # Buscar el modelo en la carpeta principal o en la carpeta models/
    if not os.path.exists(MODEL_PATH):
        posible_ruta = os.path.join("models", MODEL_PATH)
        if os.path.exists(posible_ruta):
            MODEL_PATH = posible_ruta
        else:
            posible_ruta = os.path.join("..", "models", MODEL_PATH)
            if os.path.exists(posible_ruta):
                MODEL_PATH = posible_ruta

    net = cv2.dnn.readNetFromONNX(MODEL_PATH)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    print("¡Modelo cargado exitosamente!")
except Exception as e:
    print(f"ERROR al cargar el modelo {MODEL_PATH}: {e}")
    print("Asegúrate de colocar 'best.onnx' en la raíz del proyecto o dentro de la carpeta 'models/'.")
    sys.exit(1)

print("Iniciando conexión con ESP32-CAM...")
ultimo_audio_reproducido = 0
cooldown_audio = 2.5  # Segundos mínimos entre alertas de voz

while True:
    inicio = time.time()
    try:
        respuesta = urllib.request.urlopen(URL_ESP32, timeout=5)
        img_array = np.array(bytearray(respuesta.read()), dtype=np.uint8)
        frame = cv2.imdecode(img_array, -1)
        
        if frame is None:
            continue
            
        alto_original, ancho_original = frame.shape[:2]
        
        # YOLOv8 preprocesamiento
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (IMG_SIZE, IMG_SIZE), swapRB=True, crop=False)
        net.setInput(blob)
        
        # Inferencia
        salidas = net.forward()
        salida = salidas[0]
        salida = salida.T
        
        cajas = []
        confianzas = []
        ids_clases = []
        
        x_factor = ancho_original / IMG_SIZE
        y_factor = alto_original / IMG_SIZE
        
        for fila in salida:
            scores = fila[4:]
            id_clase = np.argmax(scores)
            confianza = scores[id_clase]
            
            if confianza > CONF_THRESHOLD:
                cx, cy, w, h = fila[0:4]
                x = int((cx - (w / 2)) * x_factor)
                y = int((cy - (h / 2)) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)
                
                cajas.append([x, y, width, height])
                confianzas.append(float(confianza))
                ids_clases.append(id_clase)
                
        indices = cv2.dnn.NMSBoxes(cajas, confianzas, CONF_THRESHOLD, NMS_THRESHOLD)
        
        objetos = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = cajas[i]
                centro_x = x + (w / 2)
                
                if centro_x < (ancho_original / 3):
                    pos = "Izquierda"
                elif centro_x > (ancho_original / 3) * 2:
                    pos = "Derecha"
                else:
                    pos = "Centro"
                    
                nombre = NOMBRES_CLASES.get(ids_clases[i], f"objeto_{ids_clases[i]}")
                area = w * h
                objetos.append({"nombre": nombre, "posicion": pos, "area": area})
        
        latencia = round((time.time() - inicio) * 1000, 2)
        
        if objetos:
            objetos.sort(key=lambda item: item['area'], reverse=True)
            peligro = objetos[0]
            print(f"Detecciones: {[f'{obj[\"nombre\"]}({obj[\"posicion\"]})' for obj in objetos]} | Latencia: {latencia} ms")
            
            tiempo_actual = time.time()
            if tiempo_actual - ultimo_audio_reproducido > cooldown_audio:
                alertar_peligro(peligro["nombre"], peligro["posicion"])
                ultimo_audio_reproducido = time.time()
        else:
            print(f"Camino despejado. ({latencia} ms)", end="\r")
            
    except KeyboardInterrupt:
        print("\nSaliendo...")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)
