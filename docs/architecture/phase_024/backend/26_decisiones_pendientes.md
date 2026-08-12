# 26. Registro de Decisiones de Arquitectura (ADR 024-01 a 024-05)

## ADR 024-01: Uso de Unidades Canónicas por Dimensión para Normalización de Grafos

- **Estatus**: APROBADO
- **Contexto**: Para convertir entre múltiples unidades dentro de una misma dimensión física, definir reglas directas entre todos los pares posibles genera una complejidad $O(N^2)$.
- **Decisión**: Fijar exactamente una unidad canónica por dimensión (`UND`, `KG`, `M`, `M2`, `M3`). Toda conversión entre dos unidades derivadas mapea primero a través de la canónica.
- **Consecuencia**: Reduce la cantidad de reglas de $O(N^2)$ a $O(N)$ y simplifica la administración.

---

## ADR 024-02: Serialización String de Decimales en Payloads JSON REST API

- **Estatus**: APROBADO
- **Contexto**: El estándar JSON no especifica precisión arbitraria para números, y los clientes en JavaScript parsean valores como floats IEEE-754 de 64 bits, causando pérdida de precisión a partir del 15° dígito.
- **Decisión**: Todos los campos numéricos de cantidad y factores en los payloads REST JSON se serializan obligatoriamente como Strings (ej. `"1000.000000000000000000"`).
- **Consecuencia**: Garantiza que la precisión de 18 decimales de PostgreSQL y Python se mantenga intacta en las llamadas frontend y clientes externos.

---

## ADR 024-03: Límite Máximo de 5 Saltos en la Búsqueda de Rutas BFS (`ConversionPathResolver`)

- **Estatus**: APROBADO
- **Contexto**: Búsquedas profundas sin límite en grafos de conversiones pueden causar problemas de latencia o trampas de recursión.
- **Decisión**: Limitar la profundidad máxima de búsqueda en el resolutor BFS a 5 saltos (`max_hops = 5`).
- **Consecuencia**: Suficiente para cubrir cualquier jerarquía real (ej. Pallet -> Caja -> Paquete -> Sub-Empaque -> Unidad Base) mientras se acota el tiempo de computación.

---

## ADR 024-04: Estrategia Voraz `LARGEST_FIRST` para la Descomposición de Empaques

- **Estatus**: APROBADO
- **Contexto**: Al preparar pedidos masivos en unidades base, el almacén requiere determinar cuántos empaques mayores tomar para minimizar la cantidad de bultos a manipular.
- **Decisión**: Adoptar la estrategia algorítmica `LARGEST_FIRST` (Greedy Packaging Decomposition), priorizando los niveles jerárquicos superiores.
- **Consecuencia**: Maximiza la eficiencia operativa del almacén al mover palets y cajas completas antes de recurrir a unidades sueltas.

---

## ADR 024-05: Estrategia de Caché de Rutas de Conversión con Invalidación Total por Modificación

- **Estatus**: APROBADO
- **Contexto**: Calcular rutas BFS en cada transacción de inventario introduce latencias no aceptables para cargas masivas.
- **Decisión**: Implementar una caché en memoria / Redis de rutas evaluadas (`uom:graph_path:*`) con política de invalidación reactiva incondicional al crear o modificar reglas/empaques.
- **Consecuencia**: Garantiza latencias de respuesta $< 15\text{ ms}$ (P99) manteniendo estricta coherencia de datos.
