"""Catálogos de referencia: países y zonas horarias — Fase 005.1.

`country_code` y `timezone` eran texto libre, así que nada impedía guardar `Peru`,
`PE`, `pe` o `Perú` como si fueran valores distintos. Aquí quedan acotados.

Son datos inmutables y no dependen del tenant, así que viven como constantes y se
sirven por endpoint en vez de ocupar tablas: no hay nada que administrar, ninguna
migración que mantener y el frontend sigue teniendo una sola fuente de verdad.
Cuando el negocio abra países nuevos, se amplía esta lista.

Los tipos de almacén también se sirven desde aquí, porque hoy la misma lista está
escrita tres veces: en el validador de este módulo, en el de F022 y en el frontend.
"""

from __future__ import annotations

#: ISO 3166-1 alpha-2. Se persiste el código; el nombre es solo para mostrar.
COUNTRIES: list[dict[str, str]] = [
    {"code": "PE", "name": "Perú"},
    {"code": "AR", "name": "Argentina"},
    {"code": "BO", "name": "Bolivia"},
    {"code": "BR", "name": "Brasil"},
    {"code": "CL", "name": "Chile"},
    {"code": "CO", "name": "Colombia"},
    {"code": "EC", "name": "Ecuador"},
    {"code": "MX", "name": "México"},
    {"code": "PY", "name": "Paraguay"},
    {"code": "UY", "name": "Uruguay"},
    {"code": "VE", "name": "Venezuela"},
    {"code": "ES", "name": "España"},
    {"code": "US", "name": "Estados Unidos"},
]

#: Zonas IANA de los países soportados. `country_code` permite que el frontend
#: ofrezca primero las del país elegido sin inventar el filtro por su cuenta.
TIMEZONES: list[dict[str, str]] = [
    {"code": "America/Lima", "name": "Lima", "country_code": "PE"},
    {"code": "America/Argentina/Buenos_Aires", "name": "Buenos Aires", "country_code": "AR"},
    {"code": "America/La_Paz", "name": "La Paz", "country_code": "BO"},
    {"code": "America/Sao_Paulo", "name": "São Paulo", "country_code": "BR"},
    {"code": "America/Santiago", "name": "Santiago", "country_code": "CL"},
    {"code": "America/Bogota", "name": "Bogotá", "country_code": "CO"},
    {"code": "America/Guayaquil", "name": "Guayaquil", "country_code": "EC"},
    {"code": "America/Mexico_City", "name": "Ciudad de México", "country_code": "MX"},
    {"code": "America/Asuncion", "name": "Asunción", "country_code": "PY"},
    {"code": "America/Montevideo", "name": "Montevideo", "country_code": "UY"},
    {"code": "America/Caracas", "name": "Caracas", "country_code": "VE"},
    {"code": "Europe/Madrid", "name": "Madrid", "country_code": "ES"},
    {"code": "America/New_York", "name": "Nueva York", "country_code": "US"},
    {"code": "UTC", "name": "UTC", "country_code": ""},
]

#: Tipos de almacén de la superficie estructural F004. Los códigos son los que el
#: validador ya aceptaba; aquí solo se les añade la etiqueta humana.
WAREHOUSE_TYPES: list[dict[str, str]] = [
    {"code": "general", "name": "General"},
    {"code": "receiving", "name": "Recepción"},
    {"code": "dispatch", "name": "Despacho"},
    {"code": "quarantine", "name": "Cuarentena"},
    {"code": "returns", "name": "Devoluciones"},
    {"code": "transit", "name": "Tránsito"},
]

COUNTRY_CODES = frozenset(item["code"] for item in COUNTRIES)
TIMEZONE_CODES = frozenset(item["code"] for item in TIMEZONES)
WAREHOUSE_TYPE_CODES = frozenset(item["code"] for item in WAREHOUSE_TYPES)
