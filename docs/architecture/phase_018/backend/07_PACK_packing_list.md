# PACK — Packing List (Phase 018)

## Propósito
Representar la consolidación física de los artículos dentro de unidades logísticas de despacho (cajas, pallets, contenedores).

## Jerarquía de Packing
```mermaid
graph TD
    PALLET[Pallet PLT-001] --> BOX1[Caja BOX-001]
    PALLET --> BOX2[Caja BOX-002]
    BOX1 --> ProdA[Producto A x10]
    BOX1 --> ProdB[Producto B x5]
    BOX2 --> ProdC[Producto C x100]
```

## Validación
- Evita referencias cíclicas de padres e hijos mediante `PackageHierarchyValidator`.
- Asegura que el peso bruto sea mayor o igual al peso neto.
