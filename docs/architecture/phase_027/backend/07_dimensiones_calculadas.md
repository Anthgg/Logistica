# Dimensiones Vehiculares y Cálculo Geométrico

## 1. Modelo `VehicleDimensionsModel`

El modelo `VehicleDimensionsModel` (`app/models/logistics/vehicle_dimensions.py`) almacena la geometría tridimensional de la unidad. Separa las dimensiones métricas exteriores (para restricciones de paso por túneles, balanzas y peajes) de las dimensiones interiores de la furgón o furgoneta (para empaquetamiento de carga de la plataforma).

```python
class VehicleDimensionsModel(Base, TimestampMixin):
    __tablename__ = "logistics_vehicle_dimensions"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("logistics_vehicles.id"), nullable=False, unique=True)
    
    # Dimensiones Exteriores (en metros)
    overall_length: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    overall_width: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    overall_height: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    
    # Dimensiones Interiores del Compartimento de Carga (en metros)
    cargo_length: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    cargo_width: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    cargo_height: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    
    # Volumen Calculado Automáticamente (m3)
    calculated_internal_volume: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    reported_volume: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    
    dimension_unit_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("logistics_units_of_measure.id"), nullable=False)
```

---

## 2. Cálculo Automático de Volumen Interno vs Reportado

Cuando se ingresan o modifican las dimensiones del compartimento de carga (`cargo_length`, `cargo_width`, `cargo_height`), el sistema calcula automáticamente el volumen interior prismático libre:

$$\text{Calculated Internal Volume} = \text{cargo\_length} \times \text{cargo\_width} \times \text{cargo\_height}$$

```python
from decimal import Decimal

class VehicleDimensionsService:
    @classmethod
    def calculate_volume(cls, length: Decimal | None, width: Decimal | None, height: Decimal | None) -> Decimal | None:
        if length is None or width is None or height is None:
            return None
        return (length * width * height).round(4)
```

### Discrepancias Geométricas (Factor de Forma):
En carrocerías no perfectamente cúbicas (ej: cisternas, cisternas trapezoidales o furgones acholanados), el volumen útil real puede ser menor al prisma rectangular.
* El campo `calculated_internal_volume` almacena la multiplicación teórica exacta.
* El campo `reported_volume` almacena el volumen certificado por la ficha técnica del fabricante o la homologación del MTC.
* Si $\text{reported\_volume} > \text{calculated\_internal_volume}$, la API emite una advertencia de auditoría por incoherencia geométrica.
