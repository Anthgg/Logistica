# 04. Perfiles Especializados por Rol

## Diseño de Perfiles Relacionales 1:1

Para evitar la contaminación del modelo maestro `BusinessPartnerModel` con atributos heterogéneos que solo aplican a ciertos roles comerciales, la arquitectura implementa **Perfiles Relacionales 1:1** vinculados a `BusinessPartnerRoleModel`.

Esta técnica garantiza una estructura de datos normalizada de Tercera Forma Normal (3NF), donde los campos específicos de compras no ensucian los datos de transportistas o clientes.

---

## 1. Perfil de Proveedor (`SupplierProfileModel`)

Contiene los parámetros comerciales, financieros y logísticos requeridos para la negociación y emisión de Órdenes de Compra (PO).

```python
class PaymentCondition(str, Enum):
    CASH = "CASH"
    NET_15 = "NET_15"
    NET_30 = "NET_30"
    NET_60 = "NET_60"
    NET_90 = "NET_90"

class SupplierProfileModel(Base):
    __tablename__ = "business_partner_supplier_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("business_partner_roles.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    payment_condition = Column(SQLEnum(PaymentCondition), nullable=False, default=PaymentCondition.NET_30)
    currency_code = Column(String(3), nullable=False, default="PEN") # ISO 4217
    default_incoterm = Column(String(3), nullable=True) # FOB, CIF, DDP, EXW
    
    default_lead_time_days = Column(Integer, nullable=False, default=7)
    minimum_order_value = Column(Numeric(12, 2), nullable=False, default=0.00)
    requires_purchase_order = Column(Boolean, nullable=False, default=True)
    
    withholding_agent = Column(Boolean, nullable=False, default=False) # Agente de Retención IGV
    detraction_account = Column(String(30), nullable=True) # Cuenta Banco de la Nación (Detracciones)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

---

## 2. Perfil de Cliente (`CustomerProfileModel`)

Administra la política de crédito, límites de endeudamiento y categoría comercial para operaciones de venta.

```python
class RiskCategory(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class CustomerProfileModel(Base):
    __tablename__ = "business_partner_customer_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("business_partner_roles.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    credit_limit = Column(Numeric(12, 2), nullable=False, default=0.00)
    credit_days = Column(Integer, nullable=False, default=0)
    currency_code = Column(String(3), nullable=False, default="PEN")
    
    risk_category = Column(SQLEnum(RiskCategory), nullable=False, default=RiskCategory.MEDIUM)
    price_list_id = Column(UUID(as_uuid=True), nullable=True) # Referencia a lista de precios
    
    allow_overcredit = Column(Boolean, nullable=False, default=False)
    sales_rep_user_id = Column(UUID(as_uuid=True), nullable=True) # Vendedor asignado

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

---

## 3. Perfil de Transportista (`CarrierProfileModel`)

Almacena la habilitación regulatoria ante el Ministerio de Transportes y Comunicaciones (MTC) y capacidades operativas para despachos logísticos.

```python
class FleetType(str, Enum):
    OWNED = "OWNED"
    THIRD_PARTY = "THIRD_PARTY"
    HYBRID = "HYBRID"

class CarrierProfileModel(Base):
    __tablename__ = "business_partner_carrier_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("business_partner_roles.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    mtc_registration_code = Column(String(50), nullable=False) # Código Registro MTC Perú
    mtc_license_expiration = Column(Date, nullable=True)
    
    fleet_type = Column(SQLEnum(FleetType), nullable=False, default=FleetType.OWNED)
    max_payload_tonnage = Column(Numeric(8, 2), nullable=False, default=0.00)
    
    permits_hazardous_materials = Column(Boolean, nullable=False, default=False) # IQBF / MATPEL
    tracking_api_url = Column(String(255), nullable=True) # Integración GPS webservice

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

---

## Estrategia de Acceso a Datos (Eager Loading)

Al consultar un socio de negocio a través del `BusinessPartnerRepository`, el ORM aplica `joinedload` selectivo según las opciones enviadas en el Request (`include_profiles=true`):

```python
stmt = (
    select(BusinessPartnerModel)
    .options(
        selectinload(BusinessPartnerModel.roles)
        .joinedload(BusinessPartnerRoleModel.supplier_profile),
        selectinload(BusinessPartnerModel.roles)
        .joinedload(BusinessPartnerRoleModel.customer_profile),
        selectinload(BusinessPartnerModel.roles)
        .joinedload(BusinessPartnerRoleModel.carrier_profile)
    )
    .filter(BusinessPartnerModel.id == partner_id)
)
```

Esto garantiza que el payload JSON devuelto al cliente contenga únicamente los bloques de perfil correspondientes a los roles efectivamente activos en el socio.
