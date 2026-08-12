# 07. Gestión de Direcciones de Socios de Negocio

## Especificación del Modelo `BusinessPartnerAddressModel`

Un socio de negocio puede registrar múltiples sedes, almacenes, fiscalías o puntos de entrega. El modelo `BusinessPartnerAddressModel` (tabla `business_partner_addresses`) administra la ubicación geográfica, ubigeo estandarizado y datos de geolocalización.

---

## Definición del Esquema SQL / SQLAlchemy

```python
class AddressType(str, Enum):
    FISCAL = "FISCAL"          # Dirección de domicilio fiscal (Ficha RUC)
    OPERATIONAL = "OPERATIONAL"# Planta, oficina administrativa o almacén
    DELIVERY = "DELIVERY"      # Punto de entrega / despacho de mercadería
    REGISTERED = "REGISTERED"  # Dirección registral / legal secundaria

class BusinessPartnerAddressModel(Base):
    __tablename__ = "business_partner_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_partner_id = Column(UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    
    address_type = Column(SQLEnum(AddressType), nullable=False, default=AddressType.OPERATIONAL)
    is_primary = Column(Boolean, nullable=False, default=False)
    
    address_line1 = Column(String(255), nullable=False) # Av./Calle/Jr. y número
    address_line2 = Column(String(255), nullable=True)  # Dpto, Int, Manzana, Lote
    urbanization = Column(String(100), nullable=True)   # Urbanización / Res.
    
    ubigeo_code = Column(String(6), nullable=True)     # Ubigeo INEI (6 dígitos: Dep/Prov/Dist)
    department = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    country_code = Column(String(2), nullable=False, default="PE")
    
    latitude = Column(Numeric(10, 8), nullable=True)    # Coordenada WGS84 GPS
    longitude = Column(Numeric(11, 8), nullable=True)   # Coordenada WGS84 GPS
    
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

---

## Reglas de Negocio del Flag `is_primary`

Para garantizar la consistencia en la generación de comprobantes de pago y órdenes logísticas:

1. **Una sola Dirección Primaria por Tipo:** Solo una dirección puede tener `is_primary = True` simultáneamente por cada `address_type` dentro del mismo socio.
2. **Conmutación Automática (Triggers / Service Logic):** Si se inserta o actualiza una dirección con `is_primary = True`, las demás direcciones del mismo tipo en el mismo socio son conmutadas automáticamente a `is_primary = False`.

### Código de Conmutación en Service

```python
async def set_primary_address(self, partner_id: uuid.UUID, address_id: uuid.UUID, address_type: AddressType):
    # Resetear is_primary a False en todas las direcciones del mismo tipo
    await self.db.execute(
        update(BusinessPartnerAddressModel)
        .where(
            BusinessPartnerAddressModel.business_partner_id == partner_id,
            BusinessPartnerAddressModel.address_type == address_type
        )
        .values(is_primary=False)
    )
    # Marcar la dirección objetivo como primaria
    await self.db.execute(
        update(BusinessPartnerAddressModel)
        .where(BusinessPartnerAddressModel.id == address_id)
        .values(is_primary=True)
    )
```

---

## Ubigeo INEI y Georreferenciación GPS

### Estrategia de Ubigeo Peruano (INEI - 6 Dígitos)
* **Formato:** `DDPRDI` (2 dígitos Departamento, 2 dígitos Provincia, 2 dígitos Distrito).
* **Ejemplo:** `150101` (15: Lima, 01: Lima, 01: Lima Cercado).
* **Integración Logística:** Permite calcular fletes en la Fase 061 (Despacho) mediante zonificación geográfica estandarizada.

### Coordenadas GPS (WGS84)
* `latitude` (Ej. `-12.04637400`) y `longitude` (Ej. `-77.04279300`).
* Permite a la aplicación móvil de transportistas de la Fase 061 ejecutar la navegación paso a paso hacia el almacén del proveedor o punto de despacho del cliente.
