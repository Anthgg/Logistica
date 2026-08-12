# Líneas esperadas y allocations

La cantidad se recibe como string decimal, se convierte mediante el motor de unidades y se guarda junto con cantidad base, unidad base, factor y regla utilizada.

```mermaid
flowchart LR
  INPUT["Cantidad esperada + unidad"] --> CONV["Conversión backend"]
  CONV --> BASE["Cantidad base"]
  BASE --> LOCK["Lock de línea OC"]
  LOCK --> SUM["Suma HELD + ACTIVE"]
  SUM -->|menor o igual a OC| ALLOC["Allocation HELD"]
  SUM -->|excede OC| ERR["409 sobreasignación"]
```

La unicidad por línea esperada y el lock pesimista evitan doble reserva concurrente. Cancelar libera la allocation; enviar la activa.

