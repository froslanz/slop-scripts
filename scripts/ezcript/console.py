# console.py
# -*- coding: utf-8 -*-
import sys
import os

# Esto obliga a Python a buscar 'interprete.py' y 'extendedscript.py' en la misma carpeta
ruta_actual = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ruta_actual)

from interprete import InterpreteSimple

def iniciar_consola_interactiva():
    interprete = InterpreteSimple()
    print("=== EZScript Consola Interactiva (v1.0) ===")
    print("Escribe 'salir' para cerrar.\n")
    
    while True:
        try:
            linea = input("EZScript> ")
            if linea.strip().lower() == "salir":
                break
            interprete.ejecutar_linea(linea)
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            break

def ejecutar_archivo(ruta_archivo):
    # Validamos que el archivo termine en .ezs
    if not ruta_archivo.lower().endswith('.ezs'):
        print("Error: El archivo debe tener la extensión oficial '.ezs'")
        return

    interprete = InterpreteSimple()
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            for linea in archivo:
                # 🔥 AQUÍ ESTÁ EL CAMBIO CLAVE:
                # .strip() elimina por completo los saltos de línea (\n) del archivo 
                # para que el intérprete no se confunda con los comandos como 'sumar'
                linea_limpia = linea.strip()
                
                # Si la línea tiene texto y no es un comentario, se ejecuta
                if linea_limpia and not linea_limpia.startswith("#"):
                    interprete.ejecutar_linea(linea_limpia)
                
    except FileNotFoundError:
        print(f"Error: El archivo '{ruta_archivo}' no existe.")
    except Exception as e:
        print(f"Error crítico al ejecutar el archivo: {str(e)}")

if __name__ == "__main__":
    # Si pasamos el archivo por consola (ej: python console.py test.ezs)
    if len(sys.argv) > 1:
        ejecutar_archivo(sys.argv[1])
    else:
        # Si ejecutamos solo 'python console.py', abre la consola en vivo
        iniciar_consola_interactiva()