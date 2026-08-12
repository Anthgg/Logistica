# 10. Algoritmo de Prevención de Ciclos y Detección de Ambigüedades

## 1. Prevención de Ciclos Infinitos en Grafo

Un ciclo en el grafo de conversiones ocurre si una unidad $A$ puede derivar en $B$, $B$ en $C$ y $C$ retorna a $A$ con factores inconsistentes. Esto provocaría loops infinitos de recursión y corrupción de inventario.

### Algoritmo de Prevención de Ciclos (DFS Visited Set):

```python
def validate_no_cycles(graph: Dict[UUID, List[Edge]], start_unit_id: UUID):
    visited = set()
    rec_stack = set()

    def dfs(node: UUID):
        visited.add(node)
        rec_stack.add(node)

        for edge in graph.get(node, []):
            neighbor = edge.to_unit_id
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                # ¡Ciclo detectado!
                return True

        rec_stack.remove(node)
        return False

    if dfs(start_unit_id):
        raise CycleDetectedException(
            f"Ciclo detectado en la configuración de conversiones a partir de {start_unit_id}"
        )
```

---

## 2. Detección de Rutas Ambiguas (`409 CONVERSION_PATH_AMBIGUOUS`)

Una **ambigüedad** se produce cuando existen dos rutas independientes distintas para ir de la Unidad $A$ a la Unidad $B$, pero los factores acumulados de ambas rutas difieren significativamente en un valor superior a $\epsilon = 10^{-12}$.

```mermaid
graph TD
    A["Unidad A"] -->|Ruta 1: Factor 100| B["Unidad B"]
    A -->|Ruta 2 (Vía X): Factor 10 x 9.8 = 98| B
```

### Regla de Control de Ambigüedad:
Si el resolutor detecta dos rutas alternativas $R_1$ y $R_2$ con factores $F_1$ y $F_2$:

$$|F_1 - F_2| > 10^{-12}$$

El motor **aborta la conversión**, rechaza la transacción y emite una excepción de dominio mapeada a HTTP 409:

```json
{
  "error_code": "CONVERSION_PATH_AMBIGUOUS",
  "message": "Se detectaron rutas de conversión ambiguas con factores en conflicto para la unidad Origen y Destino.",
  "details": {
    "from_unit": "CAJA_SPECIAL",
    "to_unit": "UND",
    "path_1_factor": "24.000000000000000000",
    "path_2_factor": "25.000000000000000000",
    "difference": "1.000000000000000000"
  }
}
```

---

## 3. Estrategia de Resolución al Crear o Editar Reglas

Cada vez que se registra o modifica una regla en `unit_conversion_rules` o `product_packaging_definitions`:
1. Se construye en memoria el nuevo grafo resultante con la arista candidata.
2. Se ejecuta el detector de ciclos (`validate_no_cycles`).
3. Se ejecutan pruebas de consistencia entre todos los pares alcanzables (`validate_ambiguity`).
4. Solo si ambas verificaciones pasan con éxito, la transacción SQL realiza el `COMMIT`.
