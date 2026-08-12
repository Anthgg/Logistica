# 08. Gestión de Contactos de Socios de Negocio

## Especificación del Modelo `BusinessPartnerContactModel`

Para habilitar la comunicación operativa entre el personal de compras, tesorería y despacho con los socios de negocio, la entidad `BusinessPartnerContactModel` (tabla `business_partner_contacts`) gestiona el directorio de ejecutivos y representantes de la contraparte.

---

## Definición del Esquema SQL / SQLAlchemy

```python
class ContactType(str, Enum):
    PURCHASES = "PURCHASES"    # Ejecutivo de Ventas / Proveedor de Compras
    SALES = "SALES"            # Comprador del Cliente
    LOGISTICS = "LOGISTICS"    # Despachador, Almacenero, Coordinador de Flota
    FINANCE = "FINANCE"        # Pagos, Tesorería, Facturación
    MANAGEMENT = "MANAGEMENT"  # Gerencia General, Apoderados
    LEGAL = "LEGAL"            # Asesor Legal / Representante Jurídico

class BusinessPartnerContactModel(Base):
    __tablename__ = "business_partner_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_partner_id = Column(UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    
    contact_type = Column(SQLEnum(ContactType), nullable=False, default=ContactType.LOGISTICS)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    job_title = Column(String(100), nullable=True) # Ej. "Jefe de Logística"
    
    email = Column(String(255), nullable=False)
    phone_number = Column(String(30), nullable=True)
    mobile_number = Column(String(30), nullable=True)
    whatsapp_enabled = Column(Boolean, nullable=False, default=False)
    
    is_primary = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
```

---

## Canales de Comunicación y Enrutamiento Notificaciones

Cada módulo funcional del ERP utiliza el tipo de contacto específico para el envío automatizado de notificaciones y documentos en PDF/XML:

| Módulo ERP | Tipo de Contacto Destinatario (`contact_type`) | Documento / Notificación Enviada |
|------------|-----------------------------------------------|----------------------------------|
| **Compras (Fase 031)** | `PURCHASES` | Envío de Órdenes de Compra (PO) y Solicitudes de Cotización (RFQ). |
| **Recepción (Fase 041)** | `LOGISTICS` | Confirmación de Citas de Entrega y Notificación de Rechazo de Lotes. |
| **Ventas / Cobranza** | `FINANCE` | Recordatorios de Vencimiento de Facturas y Comprobantes de Retención. |
| **Despacho (Fase 061)** | `LOGISTICS` | Guías de Remisión Electrónicas (GRE) para Transportistas. |

---

## Validación de Formato de Canales Directos

El `BusinessPartnerContactService` valida los canales antes del guardado:

1. **Email Standard (RFC 5322):** Formato estricto de correo electrónico.
2. **Teléfono Móvil (E.164):** Formato internacional de número telefónico (ej. `+51999888777`).
3. **Bandera `whatsapp_enabled`:** Utilizada por el motor de mensajería para notificaciones automáticas de estado de despacho vía WhatsApp Business API.
