import sqlite3
import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes

BASE_DIR = "bovedas"

def obtener_rutas(nombre_boveda):
    if not nombre_boveda:
        return None, None, None, None
    nombre_seguro = "".join([c for c in nombre_boveda if c.isalnum() or c in ("_", "-")]).strip()
    carpeta = os.path.join(BASE_DIR, nombre_seguro)
    return (
        carpeta,
        os.path.join(carpeta, "mi_almacen.db"),
        os.path.join(carpeta, "master.hash"),
        os.path.join(carpeta, "pin.hash")
    )

def listar_bovedas_disponibles():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
        return []
    bovedas = []
    for item in os.listdir(BASE_DIR):
        ruta_item = os.path.join(BASE_DIR, item)
        if os.path.isdir(ruta_item) and os.path.exists(os.path.join(ruta_item, "mi_almacen.db")):
            bovedas.append(item)
    return bovedas

def calcular_hash(texto):
    digest = hashes.Hash(hashes.SHA256())
    digest.update(texto.encode())
    return digest.finalize()

def generar_fernet_desde_master(master_key_texto):
    if not master_key_texto:
        return None
    hash_32 = calcular_hash(master_key_texto)
    return Fernet(base64.urlsafe_b64encode(hash_32))

def esta_configurado(nombre_boveda):
    carpeta, db, master, pin = obtener_rutas(nombre_boveda)
    if not carpeta: return False
    return os.path.exists(master) and os.path.exists(pin) and os.path.exists(db)

def registrar_boveda_nueva(nombre_boveda, master_key, pin):
    carpeta, db, master, pin_file = obtener_rutas(nombre_boveda)
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    with open(master, "wb") as f:
        f.write(calcular_hash(master_key))
    with open(pin_file, "wb") as f:
        f.write(calcular_hash(pin))
        
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            categoria TEXT DEFAULT 'General',
            contenido TEXT, 
            cifrado INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def verificar_master(nombre_boveda, master_key_texto):
    _, _, master_file, _ = obtener_rutas(nombre_boveda)
    if not os.path.exists(master_file):
        return False
    with open(master_file, "rb") as f:
        return calcular_hash(master_key_texto) == f.read()

def verificar_pin(nombre_boveda, pin_texto):
    _, _, _, pin_file = obtener_rutas(nombre_boveda)
    if not os.path.exists(pin_file):
        return False
    with open(pin_file, "rb") as f:
        return calcular_hash(pin_texto) == f.read()

def resetear_master_con_pin(nombre_boveda, pin_ingresado, nueva_master):
    if not verificar_pin(nombre_boveda, pin_ingresado):
        return False, "❌ El PIN de emergencia es incorrecto."
    _, _, master_file, _ = obtener_rutas(nombre_boveda)
    with open(master_file, "wb") as f:
        f.write(calcular_hash(nueva_master))
    return True, "🔄 ¡Masterkey reconfigurada exitosamente!"

def guardar_registro(nombre_boveda, titulo, categoria, campos_dict, cifrar=False, master_key=None):
    _, db_file, _, _ = obtener_rutas(nombre_boveda)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    json_datos = json.dumps(campos_dict)
    
    if cifrar and master_key:
        fernet = generar_fernet_desde_master(master_key)
        contenido_final = fernet.encrypt(json_datos.encode()).decode()
        es_cifrado = 1
    else:
        contenido_final = json_datos
        es_cifrado = 0
        
    cursor.execute('INSERT INTO registros (titulo, categoria, contenido, cifrado) VALUES (?, ?, ?, ?)', 
                   (titulo, categoria, contenido_final, es_cifrado))
    conn.commit()
    conn.close()

def obtener_registros(nombre_boveda, master_key=None):
    _, db_file, _, _ = obtener_rutas(nombre_boveda)
    if not os.path.exists(db_file):
        return []
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT id, titulo, categoria, contenido, cifrado FROM registros ORDER BY id DESC')
    filas = cursor.fetchall()
    conn.close()
    
    resultados = []
    fernet = generar_fernet_desde_master(master_key) if master_key else None
    
    for fila in filas:
        id_reg, titulo, cat, contenido, cifrado = fila
        bloqueado = False
        datos = {}
        
        if cifrado == 1:
            if fernet:
                try:
                    contenido_decifrado = fernet.decrypt(contenido.encode()).decode()
                    datos = json.loads(contenido_decifrado)
                except Exception:
                    datos = {"error": "[Masterkey inválida]"}
                    bloqueado = True
            else:
                datos = {"info": "Bloqueado"}
                bloqueado = True
        else:
            datos = json.loads(contenido)
            
        resultados.append({
            "id": id_reg,
            "titulo": titulo,
            "categoria": cat,
            "datos": datos,
            "cifrado": bool(cifrado),
            "bloqueado": bloqueado
        })
    return resultados

def eliminar_registro(nombre_boveda, id_registro):
    """Elimina permanentemente una entrada de la base de datos por su ID."""
    _, db_file, _, _ = obtener_rutas(nombre_boveda)
    if not os.path.exists(db_file):
        return False
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM registros WHERE id = ?', (id_registro,))
    conn.commit()
    conn.close()
    return True