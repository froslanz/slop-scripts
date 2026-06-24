# extendedscript.py
# -*- coding: utf-8 -*-
import os
import sys
import platform

def speak(texto_puro):
    """Hace que la computadora hable el texto enviado de forma inmediata y limpia."""
    import sys
    import os
    
    if sys.platform.startswith("win"):
        # Ejecuta la voz directamente en un proceso limpio de Windows sin tablas ni esperas
        comando_voz = f'powershell -WindowStyle Hidden -Command "$sp = New-Object -ComObject SAPI.SpVoice; $sp.Speak(\'{texto_puro}\')"'
        os.system(comando_voz)
    else:
        # Comando para Mac / Linux en segundo plano
        os.system(f'say "{texto_puro}" &')
    

def obtener_info_sistema():
    """Devuelve datos básicos de la PC donde corre el lenguaje."""
    sistema = platform.system()
    procesador = platform.processor() or "Procesador Genérico"
    return f"Sistema: {sistema} | Hardware: {procesador}"

def crear_archivo(nombre_archivo, contenido):
    """Crea un archivo de texto en la PC con el contenido indicado."""
    try:
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
        return f"¡Archivo '{nombre_archivo}' creado con éxito!"
    except Exception as e:
        return f"Error al crear el archivo: {str(e)}"