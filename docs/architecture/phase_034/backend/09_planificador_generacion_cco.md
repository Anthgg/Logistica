# 09 — Planificador de Generación desde CCO (`PurchaseOrderGenerationPlanner`)

---

## 1. Integración con Cuadro Comparativo de Ofertas (CCO - Fase 033)

El proceso de aprovisionamiento en la plataforma sigue el flujo formal:
$$\text{Requisición} \longrightarrow \text{Solicitud Cotización (RFP/RFQ)} \longrightarrow \text{Evaluación CCO (Fase 033)} \longrightarrow \text{Órdenes de Compra (Fase 034)}$$

Cuando una evaluación CCO concluye y se registra la decisión de adjudicación en estado `RECORDED`, el motor puro **`PurchaseOrderGenerationPlanner`** procesa la matriz de adjudicación para convertirla en un plan de generación de Órdenes de Compra borrador.

---

## 2. Lógica de Agrupación por Tupla `(Supplier, Currency)`

Un solo Cuadro Comparativo de Ofertas (CCO) puede adjudicar diferentes ítems a múltiples proveedores ganadores o en distintas monedas (e.g. Ítems 1 y 2 a *Proveedor A* en `PEN`, Ítem 3 a *Proveedor B* en `USD`).

El `PurchaseOrderGenerationPlanner` aplica un algoritmo determinista de agrupamiento:

```mermaid
flowchart TD
    CCO[Decisión CCO Registrada - State: RECORDED] --> Extract[Extraer Líneas Adjudicadas]
    Extract --> Group{Agrupar por Supplier ID y Currency Code}
    
    Group -->|Supplier A + PEN| PO1[Plan Orden de Compra 1 - Proveedor A (PEN)]
    Group -->|Supplier B + USD| PO2[Plan Orden de Compra 2 - Proveedor B (USD)]
    Group -->|Supplier B + PEN| PO3[Plan Orden de Compra 3 - Proveedor B (PEN)]
```

---

## 3. Detección de Bloqueos e Inconsistencias (`Blocking Issues`)

Antes de proceder a la creación en base de datos, el planificador ejecuta un chequeo de pre-condiciones. Si detecta alguna anomalía, suspende la generación y retorna una lista detallada de `blocking_issues`:

### Reglas de Validación del Planificador:
1. **Estado CCO Inválido**: La decisión CCO debe estar estrictamente en estado `RECORDED`. Si está en borrador o anulada, se genera un bloqueo.
2. **Proveedor no Asignado o Inactivo**: Si una línea adjudicada carece de un `supplier_id` válido o el proveedor está suspendido.
3. **Líneas Ya Adjudicadas en su Totalidad**: Verificación en `po_purchase_order_source_allocations` para evitar la doble emisión de órdenes sobre el mismo ítem CCO.
4. **Moneda Faltante o Inconsistente**: Si la cotización adjudicada carece de código ISO de moneda.

---

## 4. Estructura del Servicio Dominio Puro

```python
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

@dataclass(frozen=True)
class CcoLineAwardInput:
    cco_decision_id: UUID
    cco_item_id: UUID
    supplier_id: UUID
    item_id: Optional[UUID]
    description: str
    awarded_quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    currency_code: str
    tax_rate: Decimal

@dataclass
class GenerationGroupPlan:
    supplier_id: UUID
    currency_code: str
    lines: List[CcoLineAwardInput] = field(default_factory=list)
    estimated_total: Decimal = Decimal("0.00")

@dataclass
class PlannerOutput:
    plans: List[GenerationGroupPlan]
    blocking_issues: List[str]
    is_valid: bool
```

### Implementación del Algoritmo de Agrupación:

```python
class PurchaseOrderGenerationPlanner:
    def plan_from_cco(
        self, 
        cco_status: str, 
        awarded_lines: List[CcoLineAwardInput]
    ) -> PlannerOutput:
        blocking_issues: List[str] = []
        
        # Validar estado CCO
        if cco_status != "RECORDED":
            blocking_issues.append(f"CCO decision status must be 'RECORDED', got '{cco_status}'")
            return PlannerOutput(plans=[], blocking_issues=blocking_issues, is_valid=False)

        groups: Dict[tuple[UUID, str], List[CcoLineAwardInput]] = {}
        
        for line in awarded_lines:
            if line.awarded_quantity <= Decimal("0"):
                blocking_issues.append(f"Line item {line.cco_item_id} has non-positive awarded quantity: {line.awarded_quantity}")
                continue
                
            key = (line.supplier_id, line.currency_code.upper())
            if key not in groups:
                groups[key] = []
            groups[key].append(line)

        plans: List[GenerationGroupPlan] = []
        for (supplier_id, currency), lines in groups.items():
            est_total = sum(l.awarded_quantity * l.unit_price for l in lines)
            plans.append(GenerationGroupPlan(
                supplier_id=supplier_id,
                currency_code=currency,
                lines=lines,
                estimated_total=est_total
            ))

        return PlannerOutput(
            plans=plans,
            blocking_issues=blocking_issues,
            is_valid=len(blocking_issues) == 0
        )
```
