# 10. Talonarios PDF

El sistema permite la pre-generación y descarga de talonarios multipágina para casos de contingencia física sin conectividad.

## Reglas de Generación
- Se reserva un rango continuo de números de serie marcando su estado como `RESERVED`.
- El PDF resultante compila una portada y una página por cada número reservado.
- Cada página del talonario lleva impresa la marca de agua en fondo `FORMATO NO EMITIDO - NÚMERO RESERVADO`.
- Si el talonario se vence sin usar, los números se marcan colectivamente como `VOIDED`.
