from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import gestor_db

app = Flask(__name__)
app.secret_key = "token_llave_maestra_multitenant_flask"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es" data-theme="default">
<head>
    <meta charset="UTF-8">
    <title>Multi-Bóveda Cifrada</title>
    <style>
        :root, [data-theme="default"] {
            --bg-principal: #f4f6f9; --bg-tarjeta: #ffffff; --texto: #1a1a1a;
            --texto-secundario: #555555; --borde: #dddddd; --acento: #007BFF; --fuente: sans-serif;
        }
        [data-theme="dark"] {
            --bg-principal: #121212; --bg-tarjeta: #1e1e1e; --texto: #e0e0e0;
            --texto-secundario: #a0a0a0; --borde: #333333; --acento: #bb86fc; --fuente: sans-serif;
        }
        [data-theme="system24"] {
            --bg-principal: #0b0c10; --bg-tarjeta: #1f2833; --texto: #45f3ff;
            --texto-secundario: #00ff66; --borde: #45f3ff; --acento: #ff0055; --fuente: 'Courier New', monospace;
        }
        body { font-family: var(--fuente); max-width: 850px; margin: 40px auto; padding: 0 20px; background: var(--bg-principal); color: var(--texto); }
        .card { background: var(--bg-tarjeta); padding: 20px; margin-bottom: 20px; border-radius: 6px; border: 1px solid var(--borde); }
        .form-group { margin-bottom: 12px; }
        label { font-weight: bold; color: var(--texto-secundario); display: block; margin-bottom: 4px;}
        input, select { padding: 8px; box-sizing: border-box; background: var(--bg-tarjeta); color: var(--texto); border: 1px solid var(--borde); border-radius: 4px; width: 100%; }
        button { background: var(--acento); color: #fff; padding: 8px 15px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
        .campo-dinamico { display: flex; gap: 10px; margin-bottom: 8px; }
        .campo-dinamico input { flex: 1; }
        .item-lista { margin-bottom: 10px; border: 1px solid var(--borde); border-radius: 4px; background: var(--bg-tarjeta); overflow: hidden; }
        .item-titulo { padding: 12px 20px; background: rgba(0,0,0,0.02); cursor: pointer; display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
        .item-contenido { padding: 15px; border-top: 1px solid var(--borde); display: none; }
        .badge { padding: 3px 6px; border-radius: 4px; font-size: 0.8em; background: var(--borde); color: var(--texto); }
        .badge-locked { background: #dc3545; color: #fff; }
        .badge-unlocked { background: #28a745; color: #fff; }
        pre { background: rgba(0,0,0,0.15); padding: 10px; border-radius: 4px; overflow-x: auto; color: var(--texto); }
        .alert { padding: 10px; background: #fff3cd; color: #856404; border-radius: 4px; margin-bottom: 15px; border: 1px solid #ffeeba; }
        .top-navbar { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--borde); padding-bottom: 10px; margin-bottom: 20px; gap: 15px; }
        .selector-area { display: flex; align-items: center; gap: 10px; }
        
        .btn-delete { background: #dc3545; padding: 5px 10px; font-size: 0.85em; text-decoration: none; color: white; border-radius: 4px; font-weight: bold; float: right; }
        .btn-delete:hover { background: #bd2130; }
    </style>
</head>
<body>

    <div class="top-navbar">
        <h2>📂 Multi-Vault: <span style="color:var(--acento);">{{ boveda_actual or "Ninguna" }}</span></h2>
        <div class="selector-area">
            <form action="/cambiar_boveda" method="POST" style="display:inline-flex; gap:5px; margin:0; width:auto;">
                <select name="boveda_destino" onchange="this.form.submit()" style="width:160px; padding:6px;">
                    <option value="" {% if not boveda_actual %}selected{% endif %}>-- Cambiar DB --</option>
                    {% for b in lista_bovedas %}
                        <option value="{{ b }}" {% if boveda_actual == b %}selected{% endif %}>📁 {{ b }}</option>
                    {% endfor %}
                </select>
            </form>
            <button onclick="document.getElementById('modalCrear').style.display='block'" style="background:#28a745; padding:6px 12px;">+ Nueva DB</button>
            <select id="themeSelect" onchange="cambiarTema(this.value)" style="width: auto; padding:6px;">
                <option value="default">Clean</option>
                <option value="dark">Dark</option>
                <option value="system24">System24</option>
            </select>
        </div>
    </div>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for msg in messages %} <div class="alert">{{ msg }}</div> {% endfor %}
      {% endif %}
    {% endwith %}

    <div id="modalCrear" class="card" style="display:none; border: 2px solid var(--acento); position:fixed; top:20%; left:50%; transform:translate(-50%, 0); z-index:100; max-width:450px; width:90%; box-shadow: 0px 4px 20px rgba(0,0,0,0.3);">
        <h3>🛠️ Crear Nueva Base de Datos / Carpeta</h3>
        <form action="/crear_boveda" method="POST" style="display:flex; flex-direction:column; gap:10px;">
            <div>
                <label>Nombre de la DB:</label>
                <input type="text" name="nombre_nueva_db" placeholder="ej: tokens, logins" required>
            </div>
            <div>
                <label>Masterkey:</label>
                <input type="password" name="master_nueva" required>
            </div>
            <div>
                <label>PIN de Emergencia:</label>
                <input type="password" name="pin_nuevo" pattern="[0-9]+" required>
            </div>
            <div style="display:flex; gap:10px; justify-content:flex-end; margin-top:10px;">
                <button type="button" onclick="document.getElementById('modalCrear').style.display='none'" style="background:#dc3545;">Cancelar</button>
                <button type="submit">Inicializar Carpeta</button>
            </div>
        </form>
    </div>

    {% if no_configurado %}
    <div class="card" style="border: 2px dashed #ff0055; margin-top: 30px;">
        <h3>🛠️ Inicializar Bóveda Protegida: "{{ boveda_actual }}"</h3>
        <form action="/configurar_boveda" method="POST" style="display:flex; flex-direction:column; gap:12px;">
            <input type="password" name="master_nueva" placeholder="Establecer Masterkey Global" required>
            <input type="password" name="pin_nuevo" placeholder="Establecer PIN Numérico" pattern="[0-9]+" required>
            <button type="submit" style="background:#ff0055;">Registrar Firmas Cifradas</button>
        </form>
    
    {% elif not boveda_actual %}
    <div class="card" style="text-align:center; padding:40px; border:2px dashed var(--borde);">
        <h3>Bienvenido al Almacén Modular</h3>
        <p>Selecciona una base de datos arriba o añade una nueva para desplegar el entorno.</p>
    </div>

    {% else %}
    <div class="card" style="border: 2px solid var(--acento);">
        <form action="/login_master" method="POST" style="display: flex; gap: 15px; align-items: center;">
            <label style="white-space: nowrap; margin-bottom:0; width:auto;"><strong>Masterkey [{{ boveda_actual }}]:</strong></label>
            <input type="password" name="master_key_input" placeholder="Contraseña..." value="{{ master_actual }}" style="flex-grow:1;">
            <button type="submit" style="background:#28a745;">Cargar Llave</button>
            {% if master_actual %}
                <a href="/logout_master" style="color:#dc3545; font-size:0.9em; text-decoration:none; font-weight:bold; margin-left:10px;">Cerrar</a>
            {% endif %}
        </form>
    </div>

    <div class="card">
        <h3>Añadir Entrada en: {{ boveda_actual }}</h3>
        <form action="/add" method="POST">
            <div style="display: flex; gap:15px; margin-bottom: 11px;">
                <div style="flex: 2;">
                    <label>Título / Identificador</label>
                    <input type="text" name="titulo" required>
                </div>
                <div style="flex: 1;">
                    <label>Categoría</label>
                    <input type="text" name="categoria" placeholder="General">
                </div>
            </div>
            <div class="form-group">
                <label>Campos Dinámicos (<a href="#" onclick="agregarCampo(event)">+ Añadir Renglón</a>)</label>
                <div id="contenedorCampos">
                    <div class="campo-dinamico">
                        <input type="text" name="campo_nombre[]" placeholder="Campo" required>
                        <input type="text" name="campo_valor[]" placeholder="Valor" required>
                    </div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top:20px;">
                <label style="display:inline-flex; align-items:center; gap:8px; width:auto;">
                    <input type="checkbox" name="cifrar" value="1" style="width:auto;"> ¿Encriptar campos con Masterkey?
                </label>
                <button type="submit">Guardar Entrada</button>
            </div>
        </form>
    </div>

    <div class="card" style="background: rgba(0,0,0,0.01);">
        <details>
            <summary style="cursor:pointer; font-weight:bold; color: var(--texto-secundario);">⚙️ Controles de Emergencia</summary>
            <div style="margin-top:20px; border-top:1px dashed var(--borde); padding-top:15px;">
                <h4 style="color:#dc3545;">Resetear Masterkey con PIN</h4>
                <form action="/bypass_pin" method="POST" style="display:flex; flex-direction:column; gap:8px; max-width:350px;">
                    <input type="password" name="pin_verificar" placeholder="PIN Secreto" required>
                    <input type="password" name="master_fresca" placeholder="Nueva Masterkey" required>
                    <button type="submit" style="background: #dc3545; color: #fff;">Forzar Reseteo</button>
                </form>
            </div>
        </details>
    </div>

    <h3>Entradas Indexadas ({{ registros | length }})</h3>
    <div style="margin-bottom: 60px;">
        {% for r in registros %}
        <div class="item-lista">
            <div class="item-titulo" onclick="toggleItem(this)">
                <span>📂 {{ r.titulo }} <span class="badge" style="margin-left:10px;">{{ r.categoria }}</span></span>
                {% if r.cifrado %}
                    {% if r.bloqueado %}
                        <span class="badge badge-locked">🔒 Cifrado</span>
                    {% else %}
                        <span class="badge badge-unlocked">🔓 Abierto</span>
                    {% endif %}
                {% else %}
                    <span class="badge">🌐 Plano</span>
                {% endif %}
            </div>
            <div class="item-contenido">
                <a href="/delete/{{ r.id }}" class="btn-delete" onclick="return confirm('¿Seguro que quieres borrar permanentemente este registro?');">🗑️ Borrar</a>
                
                {% if r.bloqueado %}
                    <p style="color:#dc3545; margin:0; font-weight:bold;">⚠️ Introduce tu Masterkey en la barra de arriba para liberar la lectura.</p>
                {% else %}
                    <table style="width:100%; border-collapse: collapse; margin-bottom:12px; margin-top: 15px;">
                        <thead>
                            <tr style="border-bottom: 2px solid var(--borde); text-align:left;">
                                <th style="padding: 6px;">Campo</th>
                                <th style="padding: 6px;">Valor</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for k, v in r.datos.items() %}
                            <tr style="border-bottom: 1px solid var(--borde);">
                                <td style="padding: 6px; font-weight:bold; color: var(--acento); width:35%;">{{ k }}</td>
                                <td style="padding: 6px; font-family: monospace;">{{ v }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    <pre>{{ r.datos | tojson(indent=2) }}</pre>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <script>
        function agregarCampo(e) {
            e.preventDefault();
            const contenedor = document.getElementById('contenedorCampos');
            const nuevaFila = document.createElement('div');
            nuevaFila.className = 'campo-dinamico';
            nuevaFila.innerHTML = `
                <input type="text" name="campo_nombre[]" placeholder="Campo" required>
                <input type="text" name="campo_valor[]" placeholder="Valor" required>
                <button type="button" style="background:#dc3545; padding:4px 8px;" onclick="this.parentElement.remove()">X</button>
            `;
            contenedor.appendChild(nuevaFila);
        }
        function toggleItem(elemento) {
            const contenido = elemento.nextElementSibling;
            if(contenido) {
                contenido.style.display = (contenido.style.display === "block") ? "none" : "block";
            }
        }
        function cambiarTema(tema) {
            document.documentElement.setAttribute('data-theme', tema);
            localStorage.setItem('db-ui-theme', tema);
        }
        const temaActivo = localStorage.getItem('db-ui-theme') || 'default';
        const select = document.getElementById('themeSelect');
        if(select) { select.value = temaActivo; cambiarTema(temaActivo); }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    lista_bovedas = gestor_db.listar_bovedas_disponibles()
    boveda_actual = session.get('boveda_activa', None)
    no_configurado = False
    if boveda_actual and not gestor_db.esta_configurado(boveda_actual):
        no_configurado = True
        
    master_key = session.get(f'master_key_{boveda_actual}', None) if boveda_actual else None
    registros = gestor_db.obtener_registros(boveda_actual, master_key) if boveda_actual else []
    
    return render_template_string(
        HTML_TEMPLATE, 
        registros=registros, 
        master_actual=master_key or "", 
        lista_bovedas=lista_bovedas, 
        boveda_actual=boveda_actual,
        no_configurado=no_configurado
    )

@app.route('/cambiar_boveda', methods=['POST'])
def cambiar_boveda():
    destino = request.form.get('boveda_destino', '').strip()
    session['boveda_activa'] = destino if destino else None
    return redirect(url_for('index'))

@app.route('/crear_boveda', methods=['POST'])
def crear_boveda():
    nombre_db = request.form['nombre_nueva_db'].strip().lower()
    master = request.form['master_nueva']
    pin = request.form['pin_nuevo']
    if not nombre_db:
        flash("❌ Nombre inválido.")
        return redirect(url_for('index'))
    gestor_db.registrar_boveda_nueva(nombre_db, master, pin)
    session['boveda_activa'] = nombre_db
    session[f'master_key_{nombre_db}'] = master
    return redirect(url_for('index'))

@app.route('/configurar_boveda', methods=['POST'])
def configurar_boveda():
    boveda_actual = session.get('boveda_activa', None)
    if not boveda_actual: return redirect(url_for('index'))
    gestor_db.registrar_boveda_nueva(boveda_actual, request.form['master_nueva'], request.form['pin_nuevo'])
    session[f'master_key_{boveda_actual}'] = request.form['master_nueva']
    return redirect(url_for('index'))

@app.route('/login_master', methods=['POST'])
def login_master():
    boveda_actual = session.get('boveda_activa', None)
    if not boveda_actual: return redirect(url_for('index'))
    key_input = request.form['master_key_input']
    if gestor_db.verificar_master(boveda_actual, key_input):
        session[f'master_key_{boveda_actual}'] = key_input
        flash("🔓 Acceso concedido.")
    else:
        flash("❌ Masterkey incorrecta.")
    return redirect(url_for('index'))

@app.route('/logout_master')
def logout_master():
    boveda_actual = session.get('boveda_activa', None)
    if boveda_actual: session.pop(f'master_key_{boveda_actual}', None)
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add():
    boveda_actual = session.get('boveda_activa', None)
    if not boveda_actual: return redirect(url_for('index'))
    
    titulo = request.form['titulo']
    categoria = request.form['categoria'] or "General"
    cifrar = 'cifrar' in request.form
    master_key = session.get(f'master_key_{boveda_actual}', None)
    
    nombres = request.form.getlist('campo_nombre[]')
    valores = request.form.getlist('campo_valor[]')
    campos_dict = {nombres[i]: valores[i] for i in range(len(nombres)) if nombres[i]}
    
    if cifrar and not master_key:
        flash("⚠️ Carga tu Masterkey primero.")
    else:
        gestor_db.guardar_registro(boveda_actual, titulo, categoria, campos_dict, cifrar, master_key)
        flash("💾 Guardado.")
    return redirect(url_for('index'))

@app.route('/delete/<int:id_reg>')
def delete(id_reg):
    """Ruta para procesar la eliminación de un registro."""
    boveda_actual = session.get('boveda_activa', None)
    if not boveda_actual:
        return redirect(url_for('index'))
        
    if gestor_db.eliminar_registro(boveda_actual, id_reg):
        flash("🗑️ El registro ha sido eliminado de la base de datos.")
    else:
        flash("❌ No se pudo eliminar el registro.")
        
    return redirect(url_for('index'))

@app.route('/bypass_pin', methods=['POST'])
def bypass_pin():
    boveda_actual = session.get('boveda_activa', None)
    if not boveda_actual: return redirect(url_for('index'))
    exito, msg = gestor_db.resetear_master_con_pin(boveda_actual, request.form['pin_verificar'], request.form['master_fresca'])
    if exito: session[f'master_key_{boveda_actual}'] = request.form['master_fresca']
    flash(msg)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)