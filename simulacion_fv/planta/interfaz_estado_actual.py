"""
interfaz_estado_actual.py
================================================================
Paso 15: Interfaz de "lectura del estado actual" de la planta.

Esta es la ÚNICA puerta de entrada que, en el futuro, se envolverá
con un servidor Modbus (`simulacion_fv/inversor_modbus/`) y un
publicador MQTT (`simulacion_fv/mqtt_gateway/`), sin tocar nada del
modelo físico ni del MPPT ya construidos y validados (Fases 2 y 3).

`obtener_estado_actual(timestamp)` no recalcula nada: lee los valores
YA CALCULADOS en `datos/processed/potencia_mppt.csv` (Fase 3, Paso 12)
y los traduce al esquema estable definido en el Paso 14
(`docs/05_diseño/esquema_datos_planta.md`).

Esta separación es deliberada: el día que haya hardware real
(Raspberry Pi + sensores), esta función se reemplaza por una que lea
sensores en vez de un CSV, PERO la firma (`obtener_estado_actual`) y
el diccionario que devuelve no cambian — todo lo que consuma esta
interfaz (Modbus, MQTT, dashboard) sigue funcionando sin cambios.

Uso:
    from interfaz_estado_actual import obtener_estado_actual

    estado = obtener_estado_actual("2026-03-01 11:35:00")
    # {'timestamp': '2026-03-01T11:35:00', 'potencia_dc': 149.82, ...}
================================================================
"""

import sys
from pathlib import Path
from datetime import datetime
from functools import lru_cache

import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_SERIE_MPPT = RAIZ_PROYECTO / "datos" / "processed" / "potencia_mppt.csv"

# Tolerancia para considerar que un timestamp solicitado "cae" en un
# instante de la serie simulada (la serie está a resolución de 5 min).
TOLERANCIA_BUSQUEDA = pd.Timedelta(minutes=5)


class EstadoNoDisponibleError(Exception):
    """Se lanza cuando el timestamp solicitado no tiene dato simulado
    cercano dentro de la tolerancia (ej. fuera del rango del dataset)."""
    pass


# =====================================================================
# CARGA DE LA SERIE (con caché simple: el CSV no cambia entre llamadas
# dentro del mismo proceso, así que no tiene sentido releerlo cada vez)
# =====================================================================
@lru_cache(maxsize=1)
def _cargar_serie_mppt(ruta_str: str) -> pd.DataFrame:
    ruta = Path(ruta_str)
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta}. Ejecute primero simular_seguimiento_mppt.py "
            "(Paso 12) para generar la serie de la que esta interfaz lee."
        )
    df = pd.read_csv(ruta, index_col="timestamp", parse_dates=True)
    return df.sort_index()


def _invalidar_cache():
    """Útil solo para pruebas (Paso 16): fuerza a releer el CSV en la
    siguiente llamada, por si el archivo fue regenerado."""
    _cargar_serie_mppt.cache_clear()


# =====================================================================
# FUNCIÓN PRINCIPAL DE LA INTERFAZ (Paso 15)
# =====================================================================
def obtener_estado_actual(timestamp, ruta_serie: Path = RUTA_SERIE_MPPT) -> dict:
    """
    Dado un instante de tiempo, devuelve un diccionario con las
    variables del esquema definido en el Paso 14 (ver
    docs/05_diseño/esquema_datos_planta.md).

    Argumentos:
        timestamp: instante solicitado. Acepta str (ej.
            "2026-03-01 11:35:00"), datetime, o pd.Timestamp.
        ruta_serie: ruta al CSV de la serie MPPT (parametrizable
            para pruebas; por defecto `datos/processed/potencia_mppt.csv`).

    Retorna:
        dict con las claves: timestamp, potencia_dc, voltaje_dc,
        corriente_dc, temperatura_panel, irradiancia.

    Lanza:
        EstadoNoDisponibleError si no hay ningún instante simulado
        dentro de TOLERANCIA_BUSQUEDA del timestamp solicitado.
    """
    ts = pd.Timestamp(timestamp)

    df = _cargar_serie_mppt(str(ruta_serie))

    idx_pos = df.index.get_indexer([ts], method="nearest")[0]
    if idx_pos == -1:
        raise EstadoNoDisponibleError(
            f"No hay datos simulados para {ts} (serie vacía)."
        )

    ts_encontrado = df.index[idx_pos]
    diferencia = abs(ts_encontrado - ts)
    if diferencia > TOLERANCIA_BUSQUEDA:
        raise EstadoNoDisponibleError(
            f"El timestamp solicitado ({ts}) está fuera del rango simulado "
            f"(instante más cercano disponible: {ts_encontrado}, "
            f"diferencia: {diferencia}, tolerancia: {TOLERANCIA_BUSQUEDA})."
        )

    fila = df.iloc[idx_pos]

    P_mppt = float(fila["P_mppt_w"])
    V_mppt = float(fila["V_mppt"])
    corriente_dc = (P_mppt / V_mppt) if V_mppt > 0.0 else 0.0

    return {
        "timestamp": ts_encontrado.isoformat(),
        "potencia_dc": round(P_mppt, 4),
        "voltaje_dc": round(V_mppt, 4),
        "corriente_dc": round(corriente_dc, 4),
        "temperatura_panel": round(float(fila["temperatura_c"]), 4),
        "irradiancia": round(float(fila["irradiancia_wm2"]), 4),
    }


def obtener_serie_completa(ruta_serie: Path = RUTA_SERIE_MPPT) -> list:
    """
    Devuelve la lista completa de estados (uno por instante simulado),
    útil para poblar un histórico o para las pruebas de integración
    del Paso 16, sin tener que llamar a obtener_estado_actual() en un
    bucle instante por instante.
    """
    df = _cargar_serie_mppt(str(ruta_serie))
    return [obtener_estado_actual(ts, ruta_serie=ruta_serie) for ts in df.index]


# =====================================================================
# PRUEBAS BÁSICAS DE LA INTERFAZ (complementan Paso 16)
# =====================================================================
def ejecutar_pruebas_unitarias():
    print("=" * 70)
    print("PRUEBAS DE LA INTERFAZ obtener_estado_actual (Paso 15)")
    print("=" * 70)

    df = _cargar_serie_mppt(str(RUTA_SERIE_MPPT))

    # Prueba 1: timestamp exacto de la serie
    print("\n[Prueba 1] Timestamp exacto")
    ts_exacto = df.index[100]
    estado = obtener_estado_actual(ts_exacto)
    assert set(estado.keys()) == {
        "timestamp", "potencia_dc", "voltaje_dc", "corriente_dc",
        "temperatura_panel", "irradiancia",
    }, f"Claves inesperadas: {estado.keys()}"
    print(f"  ✓ {estado}")

    # Prueba 2: timestamp entre dos instantes (debe redondear al más cercano)
    print("\n[Prueba 2] Timestamp intermedio (redondeo al instante más cercano)")
    ts_intermedio = df.index[50] + pd.Timedelta(minutes=1)
    estado = obtener_estado_actual(ts_intermedio)
    print(f"  Solicitado: {ts_intermedio} → obtenido: {estado['timestamp']}")
    assert estado["timestamp"] == df.index[50].isoformat()
    print("  ✓ Redondeó correctamente al instante más cercano")

    # Prueba 3: coherencia física — potencia = voltaje * corriente
    print("\n[Prueba 3] Coherencia interna: potencia_dc ≈ voltaje_dc * corriente_dc")
    ts_dia = df[df["irradiancia_wm2"] > 100].index[0]
    estado = obtener_estado_actual(ts_dia)
    p_calculada = estado["voltaje_dc"] * estado["corriente_dc"]
    assert abs(p_calculada - estado["potencia_dc"]) < 0.01, (
        f"Inconsistencia: {p_calculada} vs {estado['potencia_dc']}"
    )
    print(f"  ✓ {estado['voltaje_dc']} V × {estado['corriente_dc']} A "
          f"≈ {estado['potencia_dc']} W")

    # Prueba 4: instante nocturno → potencia 0
    print("\n[Prueba 4] Instante nocturno → potencia_dc debe ser 0")
    ts_noche = df[df["irradiancia_wm2"] == 0].index[0]
    estado = obtener_estado_actual(ts_noche)
    assert estado["potencia_dc"] == 0.0
    print(f"  ✓ potencia_dc = {estado['potencia_dc']} W")

    # Prueba 5: timestamp fuera de rango → excepción explícita
    print("\n[Prueba 5] Timestamp muy fuera de rango → EstadoNoDisponibleError")
    ts_fuera_de_rango = df.index[-1] + pd.Timedelta(days=365)
    try:
        obtener_estado_actual(ts_fuera_de_rango)
        raise AssertionError("Debió lanzar EstadoNoDisponibleError")
    except EstadoNoDisponibleError as e:
        print(f"  ✓ Excepción lanzada correctamente: {e}")

    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    ejecutar_pruebas_unitarias()

    print("\n" + "=" * 70)
    print("EJEMPLO DE USO")
    print("=" * 70)
    df = _cargar_serie_mppt(str(RUTA_SERIE_MPPT))
    ts_ejemplo = df[df["irradiancia_wm2"] > 300].index[0]
    print(f"\nobtener_estado_actual('{ts_ejemplo}') →")
    import json
    print(json.dumps(obtener_estado_actual(ts_ejemplo), indent=2, ensure_ascii=False))