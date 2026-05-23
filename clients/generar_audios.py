import os
import sys

def check_and_install_gtts():
    try:
        import gtts
    except ImportError:
        print("Instalando la librería gTTS (Google Text-to-Speech)...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gtts"])
        print("Librería gTTS instalada correctamente.")

def generar_archivos_audio():
    from gtts import gTTS

    # Crear carpeta para los audios
    carpeta_salida = "audios"
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)
        print(f"Carpeta creada: {os.path.abspath(carpeta_salida)}")

    # Diccionario de audios a generar
    # Formato: { "nombre_archivo": "Texto a decir" }
    audios = {
        # Alertas principales
        "peligro": "Peligro",
        
        # Direcciones
        "izquierda": "a la izquierda",
        "derecha": "a la derecha",
        "centro": "al centro",
        "adelante": "adelante",

        # Clases específicas del dataset "road-obstacles-ur2wn"
        "indian-street-dog": "perro en la calle",
        "pole": "poste",
        "signboard": "letrero",
        "stairs": "escaleras",
        "tree": "árbol",
        "two-wheeler-vehicle": "vehículo de dos ruedas",
        "vehicle": "vehículo",

        # Genéricos por si acaso
        "obstaculo": "obstáculo",
        "objeto": "objeto"
    }

    print("\nGenerando archivos de audio...")
    for archivo, texto in audios.items():
        ruta_archivo = os.path.join(carpeta_salida, f"{archivo}.mp3")
        print(f"Generando: {ruta_archivo} -> '{texto}'")
        
        # Crear audio en español
        tts = gTTS(text=texto, lang='es', slow=False)
        tts.save(ruta_archivo)

    print("\n¡Todos los archivos de audio se generaron con éxito!")
    print(f"Los puedes encontrar en: {os.path.abspath(carpeta_salida)}")

if __name__ == "__main__":
    check_and_install_gtts()
    generar_archivos_audio()
