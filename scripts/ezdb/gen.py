import json
import subprocess

print("=== GENERADOR DE PLANTILLAS INTERACTIVO ===")

# 1. Datos básicos
titulo = input("Introduce el Título del registro: ")
categoria = input("Introduce la Categoría (ej: Gaming, Servidores): ") or "General"

# 2. Construcción dinámica del "Template"
datos_plantilla = {}
print("\n--- Configuración de la Plantilla (Deja la clave vacía para terminar) ---")

while True:
    clave = input("Nombre del campo (ej: usuario, ip, pin): ").strip()
    if not clave:
        break # Si presionas Enter sin escribir nada, termina el bucle
        
    valor = input(f"Valor para '{clave}': ")
    
    # Intentar convertir a número si es posible, para mantener el JSON limpio
    if valor.isdigit():
        valor = int(valor)
    elif valor.lower() == "true":
        valor = True
    elif valor.lower() == "false":
        valor = False
        
    datos_plantilla[clave] = valor

# 3. ¿Cifrar?
cifrar_input = input("\n¿Quieres que este registro vaya cifrado? (s/n): ").lower()
cifrar_flag = "--cifrar" if cifrar_input == "s" else ""

# 4. Convertir la plantilla a string JSON plano
json_string = json.dumps(datos_plantilla)

print("\n=========================================")
print("JSON Generado con éxito:")
print(json_string)
print("=========================================")

# 5. BONUS: Ejecutar el comando automáticamente en tu gestor_db.py
ejecutar = input("\n¿Quieres insertar este registro en la DB ahora mismo? (s/n): ").lower()
if ejecutar == "s":
    # Construimos el comando exacto para la terminal
    comando = f'python gestor_db.py agregar -t "{titulo}" -c "{categoria}" -d \'{json_string}\' {cifrar_flag}'
    
    # Lo ejecutamos de fondo usando el sistema operativo
    subprocess.run(comando, shell=True)