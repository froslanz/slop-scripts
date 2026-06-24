import sqlite3
import os
import json

# Directorio donde Flask guarda las bases de datos
DB_FOLDER = 'bovedas'

def volcar_boveda(nombre_db):
    path_db = os.path.join(DB_FOLDER, f"{nombre_db}.db")
    
    if not os.path.exists(path_db):
        print(f"[-] Error: No se encontró la base de datos en '{path_db}'")
        return

    print(f"[+] Conectando a boveda: {nombre_db}.db")
    print("=" * 60)

    try:
        conn = sqlite3.connect(path_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Consultar todas las entradas indexadas
        cursor.execute("SELECT id, titulo, categoria, datos, cifrado FROM entradas")
        filas = cursor.fetchall()
        
        if not filas:
            print("[!] La base de datos está vacía.")
            return

        for fila in filas:
            print(f"ID: {fila['id']} | Target: {fila['titulo']} | Cat: {fila['categoria']}")
            
            # Intentar parsear el JSON crudo almacenado
            try:
                datos_decorados = json.loads(fila['datos'])
                
                # Si el registro no requiere llave criptográfica en Flask, lo volcamos directo
                if fila['cifrado'] == 0:
                    print(json.dumps(datos_decorados, indent=4, ensure_ascii=False))
                else:
                    print(" [🔒] Registro marcado como cifrado en la app.")
                    # Volcado del payload crudo/estructurado que está en la celda
                    print(f" Payload crudo en DB: {fila['datos']}")
            except Exception as json_err:
                print(f" [-] Error al decodificar payload: {json_err}")
                print(f" Contenido crudo: {fila['datos']}")
                
            print("-" * 60)
            
        conn.close()
        
    except sqlite3.Error as e:
        print(f"[-] Error de SQLite: {e}")

if __name__ == "__main__":
    # Listar las bases de datos disponibles en la carpeta
    if os.path.exists(DB_FOLDER):
        bovedas = [f.replace('.db', '') for f in os.listdir(DB_FOLDER) if f.endswith('.db')]
        if not bovedas:
            print("[-] No hay bases de datos .db en la carpeta 'bovedas/'.")
        else:
            print("Bóvedas detectadas:")
            for i, b in enumerate(bovedas):
                print(f" [{i}] {b}")
            
            try:
                opcion = int(input("\nSelecciona el número de la DB a volcar: "))
                if 0 <= opcion < len(bovedas):
                    os.system('cls' if os.name == 'nt' else 'clear')
                    volcar_boveda(bovedas[opcion])
                else:
                    print("[-] Opción fuera de rango.")
            except ValueError:
                print("[-] Entrada inválida. Introduce un número.")
    else:
        print("[-] La carpeta 'bovedas/' no existe todavía. Inicia la app web primero.")