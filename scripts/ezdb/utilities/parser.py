import json
import os

def consola_parser():
    # Limpiamos la pantalla al arrancar para dejar la terminal impecable
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("\033[94m+--------------------------------------------------+")
    print("|                  JSON PARSER                     |")
    print("|  Introduce el string JSON o escribe 'salir'      |")
    print("+--------------------------------------------------+\033[0m")

    while True:
        try:
            # Capturamos la línea mediante input directo
            linea = input("\n\033[94mjson_parser>>\033[0m ").strip()

            # Condición de salida rápida
            if linea.lower() in ['salir', 'exit', 'quit']:
                print("\n\033[93m[!] Saliendo del parser. Terminal liberada.\033[0m\n")
                break

            # Si el usuario le da a enter sin escribir nada, saltamos el ciclo
            if not linea:
                continue

            # Procesamos el string introducido
            data = json.loads(linea)
            
            print("-" * 40)
            # Recorremos y numeramos los campos mapeados
            for indice, (campo, valor) in enumerate(data.items(), start=1):
                # Imprime "Campo X: nombre -> valor" con colores ANSI
                print(f"  \033[96mCampo {indice}:\033[0m \033[95m{campo}\033[0m -> \033[92m{valor}\033[0m")
            print("-" * 40)

        except json.JSONDecodeError as e:
            # Captura si metes algo que no sea JSON estructurado válido
            print(f"\n\033[91m[-] Error de sintaxis JSON:\033[0m {e}")
            print("\033[93m[!] Asegúrate de usar comillas dobles para las llaves y valores.\033[0m")
            
        except KeyboardInterrupt:
            # Por si te da el reflejo de hacker de presionar CTRL+C para cerrar el script
            print("\n\n\033[93m[!] Interrupción detectada. Saliendo...\033[0m\n")
            break

if __name__ == "__main__":
    consola_parser()