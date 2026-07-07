# script de la adquisición de datos de nasa power.

## rango de fechas horarias aceptadas.

La API de nasa power ofrece datos disponibles desde la fecha del 2001/01/01 hasta datos cercanos a tiempo real, NRT.

## Zona horaria.

La zona horaria de la API de nasa power se entrega normalmente en LST (Local Solar Time) por defecto, si se necesita UTC se debe agregar "time-standard": "UTC", o en caso de conservar la hora solar local "time-standard": "LST"

## Unidades.

Las unidades dadas por la API de NASA POWER entrega horarios/promedio horario.

La variable de irradiación solar es la de ALLSKY_SFC_SW_DWN la cual es la adecuada para la irradiación solar de superficie en el cielo completo horizontal y se trabaja en: (Wh/m^2) promedio horario como energía horaria equivalente.

La variable T2M entrega la temperatura de la zona y se da en: °C.

## parametros usados.

Para la zona a realizar pruebas en Bogotá DC.

Latitud: 4.6401.
Longitud: -74.0801.

## ¿Como vienen los datos de NASA POWER?

Los datos de la API de NASA POWER vienen en carpetas, la primera carpeta principal se llama: properties, y dentro de la carpeta principal se encuentra otra carpeta llamada parameter ya por ultimo en la carpeta de parameter se encuentran las dos subcarpetas de ALLSKY_SFC_SW_DWN (Irradiancia) y la de T2M (Temperatura).

Esto significa que el script para sacar los datos tiene que entrar a cada subcarpeta y sacar los datos de la fecha por ejemplo: "2023032108", y juntar la irradiancia con la temperatura de esa misma hora y se tiene que armar la fila uno mismo.

## ¿Cómo viene la fecha y la hora? (Timestamp)

El formato del timestamp viene como un string plano de 10 caracteres con el diseño "YYYYMMDDHH" (Año de 4 dígitos, Mes de 2 dígitos, Día de 2 dígitos y Hora de 2 dígitos).

## Valores faltantes:

La API define mediante un parámetro especifico a los datos cuando no exista una lectura satelital o cuando se consulten fechas futuras de la disponibilidad real de la API de NASA POWER, esos datos faltantes los remplaza con un valor de -999.0 o -999 si el diccionario de python lo aproxima, en el header con el objetivo de indicar que en esa fecha y hora no se encuentran registros de irradiancia o de temperatura.

