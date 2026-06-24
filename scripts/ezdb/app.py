from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sqlite3
import json

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_para_flash_y_sesiones'

# Configuración de rutas de almacenamiento local
DB_FOLDER = 'bovedas'
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

# =====================================================================
# UTILERÍAS DE BASE DE DATOS (SQLITE3)
# =====================================================================
def obtener_conexion(nombre_db):
    path_db = os.path.join(DB_FOLDER, f"{nombre_db}.db")
    # Si no existe, creará el archivo .db automáticamente
    conn = sqlite3.connect(path_db)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_tablas(conn):
    cursor = conn.cursor()
    # Tabla para guardar configuraciones de seguridad (Masterkey, PIN)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')
    # Tabla para las entradas indexadas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entradas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            categoria TEXT DEFAULT 'General',
            datos TEXT NOT NULL,
            cifrado INTEGER DEFAULT 0
        )
    ''')
    conn.commit()

def listar_bovedas_locales():
    return [f.replace('.db', '') for f in os.listdir(DB_FOLDER) if f.endswith('.db')]


# =====================================================================
# RUTAS DE CONTROL DE NAVEGACIÓN Y RENDERIZADO
# =====================================================================
@app.route('/')
def index():
    lista_bovedas = listar_bovedas_locales()
    boveda_actual = session.get('boveda_actual')
    master_actual = session.get('master_actual', '')
    
    no_configurado = False
    registros = []

    if boveda_actual:
        conn = obtener_conexion(boveda_actual)
        inicializar_tablas(conn)
        
        # Verificar si la base de datos tiene contraseñas configuradas
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM config WHERE clave='masterkey'")
        row = cursor.fetchone()
        
        if not row:
            no_configurado = True
        else:
            # Si está configurada, extraer los registros de contraseñas
            cursor.execute("SELECT * FROM entradas")
            rows = cursor.fetchall()
            
            for r in rows:
                # Reconstruir el diccionario desde el string JSON
                try:
                    datos_dict = json.loads(r['datos'])
                except:
                    datos_dict = {"error": "No se pudo decodificar JSON"}

                # Lógica del candado: si está cifrado y la llave no coincide/está vacía, se bloquea
                bloqueado = False
                if r['cifrado'] == 1 and not master_actual:
                    bloqueado = True

                registros.append({
                    "id": r['id'],
                    "titulo": r['titulo'],
                    "categoria": r['categoria'],
                    "datos": datos_dict,
                    "cifrado": r['cifrado'],
                    "bloqueado": bloqueado
                })
        conn.close()

    return render_template(
        'index.html',
        lista_bovedas=lista_bovedas,
        boveda_actual=boveda_actual,
        master_actual=master_actual,
        no_configurado=no_configurado,
        registros=registros
    )


# =====================================================================
# API / ACCIONES DISPARADAS POR FORMULARIOS
# =====================================================================
@app.route('/cambiar_boveda', methods=['POST'])
def cambiar_boveda():
    boveda_destino = request.form.get('boveda_destino')
    if boveda_destino:
        session['boveda_actual'] = boveda_destino
        session.pop('master_actual', None) # Limpiar contraseñas en memoria al cambiar de base de datos
    return redirect(url_for('index'))

@app.route('/crear_boveda', methods=['POST'])
def crear_boveda():
    nombre = request.form.get('nombre_nueva_db').strip().lower()
    master = request.form.get('master_nueva')
    pin = request.form.get('pin_nuevo')

    if nombre:
        conn = obtener_conexion(nombre)
        inicializar_tablas(conn)
        cursor = conn.cursor()
        # Guardar credenciales de acceso directo
        cursor.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('masterkey', ?)", (master,))
        cursor.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('pin', ?)", (pin,))
        conn.commit()
        conn.close()
        
        session['boveda_actual'] = nombre
        flash(f"Bóveda '{nombre}' inicializada correctamente.")
    return redirect(url_for('index'))

@app.route('/configurar_boveda', methods=['POST'])
def configurar_boveda():
    boveda_actual = session.get('boveda_actual')
    master = request.form.get('master_nueva')
    pin = request.form.get('pin_nuevo')

    if boveda_actual:
        conn = obtener_conexion(boveda_actual)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('masterkey', ?)", (master,))
        cursor.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('pin', ?)", (pin,))
        conn.commit()
        conn.close()
        flash("Firmas registradas con éxito.")
    return redirect(url_for('index'))

@app.route('/login_master', methods=['POST'])
def login_master():
    boveda_actual = session.get('boveda_actual')
    master_input = request.form.get('master_key_input')

    if boveda_actual:
        conn = obtener_conexion(boveda_actual)
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM config WHERE clave='masterkey'")
        row = cursor.fetchone()
        conn.close()

        if row and row['valor'] == master_input:
            session['master_actual'] = master_input
            flash("Llave maestra cargada. Registros liberados.")
        else:
            flash("Masterkey incorrecta.")
    return redirect(url_for('index'))

@app.route('/logout_master')
def logout_master():
    session.pop('master_actual', None)
    flash("Llave desmontada de la sesión.")
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_entrada():
    boveda_actual = session.get('boveda_actual')
    if not boveda_actual:
        return redirect(url_for('index'))

    titulo = request.form.get('titulo')
    categoria = request.form.get('categoria') or 'General'
    cifrar = 1 if request.form.get('cifrar') == '1' else 0

    # Construir diccionario dinámico procesando las listas del formulario
    campos = request.form.getlist('campo_nombre[]')
    valores = request.form.getlist('campo_valor[]')
    
    datos_dict = {}
    for k, v in zip(campos, valores):
        if k.strip():
            datos_dict[k.strip()] = v

    datos_json = json.dumps(datos_dict)

    conn = obtener_conexion(boveda_actual)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO entradas (titulo, categoria, datos, cifrado) VALUES (?, ?, ?, ?)",
        (titulo, categoria, datos_json, cifrar)
    )
    conn.commit()
    conn.close()

    flash("Entrada indexada correctamente.")
    return redirect(url_for('index'))

@app.route('/delete/<int:id_registro>')
def delete_entrada(id_registro):
    boveda_actual = session.get('boveda_actual')
    master_actual = session.get('master_actual') 

    # Bloqueo de seguridad que pusimos antes
    if not master_actual:
        flash("❌ Error de autenticación: Debes cargar la Masterkey arriba antes de poder purgar un registro.")
        return redirect(url_for('index'))

    if boveda_actual:
        conn = obtener_conexion(boveda_actual)
        cursor = conn.cursor()
        
        # 1. Primero borramos el registro
        cursor.execute("DELETE FROM entradas WHERE id = ?", (id_registro,))
        
        # 2. 🌟 CRÍTICO: Guardamos los cambios inmediatamente para cerrar la transacción
        conn.commit()
        
        # 3. Ahora que la transacción se cerró, el VACUUM correrá sin protestar
        try:
            cursor.execute("VACUUM")
        except sqlite3.OperationalError:
            # Por si acaso la base de datos está ocupada en ese milisegundo, evitamos el crash
            pass
            
        conn.close()
        
        flash("🗑️ Registro purgado físicamente y espacio de disco compactado.")
        
    return redirect(url_for('index'))

@app.route('/bypass_pin', methods=['POST'])
def bypass_pin():
    boveda_actual = session.get('boveda_actual')
    pin_verificar = request.form.get('pin_verificar')
    master_fresca = request.form.get('master_fresca')

    if boveda_actual:
        conn = obtener_conexion(boveda_actual)
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM config WHERE clave='pin'")
        row = cursor.fetchone()

        if row and row['valor'] == pin_verificar:
            cursor.execute("UPDATE config SET valor = ? WHERE clave = 'masterkey'", (master_fresca,))
            conn.commit()
            session['master_actual'] = master_fresca
            flash("Bypass exitoso: Masterkey reconfigurada con PIN.")
        else:
            flash("PIN Inválido. Intento bloqueado.")
        conn.close()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)