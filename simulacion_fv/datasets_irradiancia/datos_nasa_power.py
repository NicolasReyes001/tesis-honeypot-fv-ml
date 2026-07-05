import requests # type: ignore
import json
import os
import sys  
import time
from datetime import datetime

from pathlib import Path

# 1. Ubicamos la raíz del proyecto (tesis-honeypot-fv-ml)
# __file__ es este script. .resolve().parents[1] sube los niveles necesarios hasta la raíz
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

# 2. Definimos la ruta destino dentro de 'datos/raw/'
CARPETA_OUTPUTS = RAIZ_PROYECTO / "datos" / "raw" / "outputs_nasa"

LATITUD = 4.64
LONGITUD = -74.08

# La API recibe datos desde 2001/01/01 y con formato: YYYYMMDD (año, mes, dia).
# A dia de hoy 2026/07/04 hay datos hasta el 2026/03/30, de ahi en adelante los datos se remplazan por -999.
# Con la que estamos usando es: 20230321 o lo que es 2023/03/21.
FECHA_INICIO = "20230321"
FECHA_FIN = "20230321"

VARIABLES = ["ALLSKY_SFC_SW_DWN", "T2M"]

API_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"

def construir_parametros():

    # Parámetros de la petición

    params = {
        "parameters": ",".join(VARIABLES),
        "community": "RE",
        "latitude": LATITUD,
        "longitude": LONGITUD,
        "start": FECHA_INICIO,
        "end": FECHA_FIN,
        "format": "JSON"
    }

    # verificar que los parámetros se construyeron correctamente.

    # print("\n--- [PASO 1] Parámetros de la petición construidos ---")
    # print(json.dumps(params, indent=4))
    # print(params)

    return params

def ejecutar_peticion(params):
    """
    Realiza la petición HTTP a la API de NASA POWER.
    Cumple con el requisito de incluir al menos un reintento automático 
    con espera en caso de fallos de red o errores del servidor, y usa timeout.
    """
    print("\n--- [PASO 2] Realizando petición a la API de NASA POWER ---")
    
    intentos_maximos = 2
    espera_segundos = 5  # Tiempo a esperar antes de volver a intentar
    
    for intento in range(1, intentos_maximos + 1):
        try:
            print(f"Intento {intento} de {intentos_maximos}...")
            
            # [MEJORA 6]: Agregamos timeout=20 para evitar bloqueos infinitos
            response = requests.get(API_URL, params=params, timeout=20)
            
            # Si el código HTTP es 200, la petición fue exitosa
            if response.status_code == 200:
                print("¡Petición exitosa! Datos recibidos correctamente.")
                datos = response.json()
                return datos, response
            
            # Si el servidor responde pero con un error (ej. 500, 503, 404)
            print(f"[ADVERTENCIA] El servidor respondió con código de error HTTP: {response.status_code}")
            
        except requests.exceptions.Timeout:
            print(f"[ADVERTENCIA] El servidor tardó demasiado en responder (Timeout de 20s alcanzado).")
        except requests.exceptions.RequestException as e:
            print(f"[ADVERTENCIA] Error de conexión/red: {e}")
            
        # Si no fue el último intento, esperamos antes de volver a probar
        if intento < intentos_maximos:
            print(f"Esperando {espera_segundos} segundos antes del reintento automático...")
            time.sleep(espera_segundos)
            print("-" * 40)
            
    # Si el bucle termina, significa que todos los intentos fallaron
    print("\n[ERROR] Se agotaron los intentos disponibles y no se pudo obtener respuesta válida.")
    return None, None
    
def guardar_json_crudo(datos):
    print("\n--- [PASO 3] Guardando JSON crudo en el disco ---")
    if datos is None:
        print("[ERROR] No hay datos válidos para guardar en el archivo JSON.")
        return None

    # Definimos el nombre del archivo y combinamos con la ruta absoluta de pathlib
    nombre_archivo = f"datos_crudos_{LATITUD}_{LONGITUD}_{FECHA_INICIO}_{FECHA_FIN}.json"
    ruta_completa = CARPETA_OUTPUTS / nombre_archivo

    # Creamos la estructura de carpetas de forma segura si no existe (incluyendo subcarpetas si faltan)
    CARPETA_OUTPUTS.mkdir(parents=True, exist_ok=True)

    # Al usar pathlib, abrimos el archivo directamente pasando la ruta completa como string o path object
    with open(ruta_completa, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)
        
    print(f"¡Archivo guardado exitosamente en: {ruta_completa}")
    return str(ruta_completa)


def guardar_metadatos(response, params):
    print("\n--- [PASO 4] Guardando archivo de metadatos ---")
    if response is None:
        print("[ERROR] No se pueden generar metadatos porque la petición falló.")
        return None

    # Definimos el nombre del archivo txt
    nombre_metadatos = f"metadatos_{FECHA_INICIO}_{FECHA_FIN}.txt"
    ruta_completa = CARPETA_OUTPUTS / nombre_metadatos

    # Doble seguridad para asegurar que la carpeta exista
    CARPETA_OUTPUTS.mkdir(parents=True, exist_ok=True)

    momento_descarga = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(ruta_completa, "w", encoding="utf-8") as archivo:
        archivo.write("==================================================\n")
        archivo.write("       BITÁCORA DE DESCARGA - NASA POWER          \n")
        archivo.write("==================================================\n\n")
        
        archivo.write(f"Fecha y hora de ejecución: {momento_descarga}\n")
        archivo.write(f"Código de respuesta HTTP: {response.status_code}\n")
        archivo.write(f"Tiempo de respuesta del servidor: {response.elapsed.total_seconds()} segundos\n\n")

        archivo.write("--- PARÁMETROS USADOS ---\n")
        archivo.write(f"Latitud: {LATITUD}\n")
        archivo.write(f"Longitud: {LONGITUD}\n")
        archivo.write(f"Fecha de inicio: {FECHA_INICIO}\n")
        archivo.write(f"Fecha de fin: {FECHA_FIN}\n\n")

        archivo.write("--- VARIABLES USADAS ---\n")
        archivo.write(f"Variables: {', '.join(VARIABLES)}\n")

        archivo.write("--- PARÁMETROS CONFIGURADOS EN LA PETICIÓN ---\n")
        archivo.write(json.dumps(params, indent=4) + "\n\n")
        
        archivo.write("--- URL EXACTA SOLICITADA ---\n")
        archivo.write(f"{response.url}\n\n")
        
        archivo.write("--- INFORMACIÓN ADICIONAL DEL SERVIDOR (HEADERS) ---\n")
        archivo.write(f"Servidor: {response.headers.get('Server', 'Desconocido')}\n")
        archivo.write(f"Tipo de contenido: {response.headers.get('Content-Type', 'Desconocido')}\n")
        archivo.write(f"Tamaño de la respuesta: {response.headers.get('Content-Length', 'Desconocido')} bytes\n")
        
    print(f"¡Archivo de metadatos guardado exitosamente en: {ruta_completa}")
    return str(ruta_completa)

def variables_reales(datos):

    irradiancia_original = datos["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    # print("Irradiancia original:")
    # print(irradiancia_original)

    temperatura_original = datos["properties"]["parameter"]["T2M"]
    # print("Temperatura original:")
    # print(temperatura_original)

    # Variables nuevas para contar los datos faltantes por cada parámetro

    horas_faltantes_irr = 0
    horas_faltantes_temp = 0

    # Nuevos diccionarios donde SOLO guardaremos los datos que de verdad existen
    irradiancia_limpia = {}
    temperatura_limpia = {}

    for timestamp, valor in irradiancia_original.items():
        if valor == -999:
            horas_faltantes_irr += 1
        else:
            irradiancia_limpia[timestamp] = valor

    for timestamp, valor in temperatura_original.items():
        if valor == -999:
            horas_faltantes_temp += 1
        else:
            temperatura_limpia[timestamp] = valor  
    # DATOS REALES:
    print("\n================ REPORTE DE CALIDAD DE DATOS ================")
    print(f"Horas faltantes de Irradiancia: {horas_faltantes_irr}")
    print(f"Horas faltantes de Temperatura: {horas_faltantes_temp}")
    print("=============================================================\n")

    print("Datos de irradiancia solar (Wh/m^2):")
    if irradiancia_limpia:
        print(json.dumps(irradiancia_limpia, indent=4))
    else:
        print("No hay datos de irradiancia solar disponibles.")

    print("\n Datos reales de temperatura (°C):")
    if temperatura_limpia:
        print(json.dumps(temperatura_limpia, indent=4))
    else:
        print("No hay datos de temperatura disponibles.")
    
    return irradiancia_limpia, temperatura_limpia

def numero_registros(irradiancia_limpia, temperatura_limpia):
    
    horas_sincronizadas = set(irradiancia_limpia.keys()) & set(temperatura_limpia.keys())
    irradiancia_final = {}
    temperatura_final = {}

    for timestamp in sorted(horas_sincronizadas):
        irradiancia_final[timestamp] = irradiancia_limpia[timestamp]
        temperatura_final[timestamp] = temperatura_limpia[timestamp]

    descartados_irr = len(irradiancia_limpia) - len(irradiancia_final)
    descartados_temp = len(temperatura_limpia) - len(temperatura_final)

    print("\n================ REPORTE DE SINCRONIZACIÓN ================")
    print(f"Total de horas utilizables a la par: {len(irradiancia_final)}")
    print(f"Datos de Irradiancia descartados por no tener temperatura par: {descartados_irr}")
    print(f"Datos de Temperatura descartados por no tener irradiancia par: {descartados_temp}")
    print("=============================================================\n")

    # Imprimimos los diccionarios ya perfectamente acoplados
    print("--- Datos Finales de Irradiancia Sincronizados ---")
    print(json.dumps(irradiancia_final, indent=4))

    print("\n--- Datos Finales de Temperatura Sincronizados ---")
    print(json.dumps(temperatura_final, indent=4))

    return irradiancia_final, temperatura_final, horas_sincronizadas

def aplanar_datos(irradiancia_final, temperatura_final, horas_sincronizadas):

    dataset_plano = []
    for timestamp in sorted(horas_sincronizadas):
        fecha_objeto = datetime.strptime(timestamp, "%Y%m%d%H")
        fecha_formateada = fecha_objeto.strftime("%Y-%m-%d %H:00")

        fila = {
        "Fecha/Hora": fecha_formateada,
        "Irradiancia (Wh/m^2)": irradiancia_final[timestamp],
        "Temperatura (°C)": temperatura_final[timestamp]
        }

        dataset_plano.append(fila)

    # =====================================================================
    # IMPRESIÓN EN FORMATO TABLA
    # =====================================================================
    print("\n================ DATASET PLANO Y SINCRONIZADO ================")
    # Encabezados de la tabla
    print(f"{'Fecha / Hora':<20} | {'Irradiancia (Wh/m^2)':<22} | {'Temperatura (°C)':<16}")
    print("-" * 65)
    
    # Imprimimos cada fila plana alineada
    for registro in dataset_plano:
        print(f"{registro['Fecha/Hora']:<20} | {registro['Irradiancia (Wh/m^2)']:<22} | {registro['Temperatura (°C)']:<16}")
    print("==============================================================\n")

    # Si necesitas ver el JSON aplanado puro:
    # print(json.dumps(dataset_plano, indent=4))

def descargar_datos():
    pass


if __name__ == "__main__":

    params = construir_parametros()

    datos_crudos, response_objeto = ejecutar_peticion(params)

    if datos_crudos is None:
        print("\nNo fue posible descargar los datos. Finalizando el programa.")
        sys.exit(1)

    ruta_json = guardar_json_crudo(datos_crudos)

    ruta_metadatos = guardar_metadatos(response_objeto, params)

    irr_limpia, temp_limpia = variables_reales(datos_crudos)

    irr_final, temp_final, horas_sincronizdas = numero_registros(irr_limpia, temp_limpia)

    aplanar_datos(irr_final, temp_final, horas_sincronizdas)

    descargar_datos()  