import sys
import os
import time

# =========================================================
# CONFIGURACIÓN DEL SISTEMA
# =========================================================
DEBUG_MODE = 0  # 1 = Detalles técnicos | 0 = Interfaz limpia

class InterpreteSimple:
    def __init__(self):
        self.variables = {}
        self.modulos_cargados = {}
        if DEBUG_MODE == 1:
            print("[DEBUG]: Intérprete Ezcript inicializado correctamente.")

    def log_debug(self, mensaje):
        """Muestra mensajes técnicos solo si DEBUG_MODE está activo"""
        if DEBUG_MODE == 1:
            print(f"[DEBUG]: {mensaje}")

    def manejar_error_y_cerrar(self, mensaje):
        print(f"\n[Error en Ezcript]: {mensaje}")
        print("El programa se cerrará en: ", end="")
        for i in range(5, 0, -1):
            print(f"{i}... ", end="", flush=True)
            time.sleep(1)
        print("Adiós.")
        sys.exit(1)

    def ejecutar_linea(self, linea):
        linea_limpia = linea.strip()
        
        # Ignorar líneas vacías o comentarios
        if not linea_limpia or linea_limpia.startswith("#"):
            return

        # =========================================================
        # 1. MOTOR DE CÁLCULO (Prioridad máxima)
        # =========================================================
        # Detecta "calc " en cualquier posición tras quitar espacios
        if linea_limpia.startswith("calc ") or " = calc " in linea_limpia:
            self.log_debug(f"Comando CALC detectado en línea: '{linea_limpia}'")
            
            var_destino = None
            operacion = ""
            
            if " = calc " in linea_limpia:
                partes = linea_limpia.split(" = calc ", 1)
                var_destino = partes[0].strip()
                operacion = partes[1].strip()
            else:
                operacion = linea_limpia.split("calc ", 1)[1].strip()

            # Reemplazo de variables
            for nombre, valor in self.variables.items():
                if nombre in operacion:
                    operacion = operacion.replace(nombre, str(valor))
            
            self.log_debug(f"Operación final a calcular: {operacion}")
            try:
                resultado = eval(operacion)
                if var_destino:
                    self.variables[var_destino] = str(resultado)
                    self.log_debug(f"Variable persistente '{var_destino}' actualizada a: {resultado}")
                else:
                    print(resultado)
            except Exception as e:
                self.manejar_error_y_cerrar(f"Error matemático: {e}")
            return

        # =========================================================
        # 2. COMANDOS NATIVOS
        # =========================================================
        if linea_limpia == "exit":
            self.log_debug("Ejecutando exit.")
            sys.exit(0)

        if linea_limpia == "pause":
            input("Presione una tecla para continuar . . .")
            return

        if linea_limpia.startswith("print "):
            contenido = linea_limpia.split(" ", 1)[1].strip().strip('""\'\'')
            # Control de cierre de ExtendedScript
            if not contenido: 
                sys.exit(0)
            print(self.variables.get(contenido, contenido))
            return

        if " = input" in linea_limpia:
            partes = linea_limpia.split(" = input", 1)
            nombre_var = partes[0].strip()
            pregunta = partes[1].strip().strip('()""\'\'')
            self.variables[nombre_var] = input(pregunta)
            self.log_debug(f"Input capturado para variable '{nombre_var}'")
            return

        # =========================================================
        # 3. EXTENDEDSCRIPT / ASIGNACIÓN
        # =========================================================
        if "=" in linea_limpia:
            partes = linea_limpia.split("=", 1)
            nombre_var = partes[0].strip()
            valor_var = partes[1].strip().strip('""\'\'')
            self.variables[nombre_var] = valor_var
            self.log_debug(f"Asignación ExtendedScript: {nombre_var} = {valor_var}")
            return

        self.manejar_error_y_cerrar(f"Comando desconocido o mal formado: '{linea_limpia}'")

    def ejecutar_archivo(self, ruta_archivo):
        if not os.path.exists(ruta_archivo):
            self.manejar_error_y_cerrar(f"No se encuentra el archivo script: {ruta_archivo}")
        
        self.log_debug(f"Cargando archivo: {ruta_archivo}")
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            for num, linea in enumerate(archivo, 1):
                try:
                    self.ejecutar_linea(linea)
                except Exception as e:
                    self.manejar_error_y_cerrar(f"Fallo en línea {num}: {e}")