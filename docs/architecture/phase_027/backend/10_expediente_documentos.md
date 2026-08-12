# Expediente Documental de Vehículos

## 1. Servicio `VehicleDocumentService`

El cumplimiento regulatorio en el transporte terrestre peruano exige que cada vehículo en circulación cuente con un expediente legal al día. 

El servicio `VehicleDocumentService` (`app/services/logistics/vehicle_document_service.py`) gestiona los documentos habilitantes, el control de fechas de caducidad, la vigencia temporal y el almacenamiento de metadatos asociados a las pólizas y certificados.

---

## 2. Tipos de Documentos Vehiculares (`VehicleDocumentType`)

```python
class VehicleDocumentType(str, enum.Enum):
    SOAT = "SOAT"                               # Seguro Obligatorio de Accidentes de Tránsito
    TECHNICAL_INSPECTION = "TECHNICAL_INSPECTION" # Inspección Técnica Vehicular (CITV - MTC)
    PROPERTY_CARD = "PROPERTY_CARD"             # Tarjeta de Propiedad Vehicular (SUNARP)
    MTC_PERMIT = "MTC_PERMIT"                   # Permiso de Operación Especial de Transporte (MTC)
    HAZMAT_PERMIT = "HAZMAT_PERMIT"             # Permiso de Transporte de Materiales Peligrosos
    INSURANCE_POLICY = "INSURANCE_POLICY"       # Póliza de Seguro de Carga / Todo Riesgo
```

---

## 3. Modelo `VehicleDocumentModel`

```python
class VehicleDocumentModel(Base, TimestampMixin, AuditMixin):
    __tablename__ = "logistics_vehicle_documents"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("logistics_vehicles.id"), nullable=False, index=True)
    
    document_type: Mapped[VehicleDocumentType] = mapped_column(Enum(VehicleDocumentType), nullable=False)
    document_number: Mapped[str] = mapped_column(String(64), nullable=False) # Nro de póliza o certificado
    
    issuer: Mapped[str] = mapped_column(String(128), nullable=False) # Aseguradora / Entidad emisora (ej: Rimac, La Positiva, FARENET)
    
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True) # NULL para tarjetas indeterminadas
    
    is_lifetime: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Archivo adjunto
    file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_hash_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    verification_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False) # PENDING, VERIFIED, REJECTED
```

---

## 4. Gestión de Expiración y Alertas Preventivas

El servicio evalúa periódicamente (o bajo demanda en las consultas API) el estado de vencimiento de cada documento:

```python
class VehicleDocumentService:
    @classmethod
    def evaluate_document_status(cls, doc: VehicleDocumentModel, ref_date: date) -> str:
        if doc.is_lifetime or doc.expiration_date is None:
            return "VALID"
            
        days_until_expiration = (doc.expiration_date - ref_date).days
        
        if days_until_expiration < 0:
            return "EXPIRED"
        elif days_until_expiration <= 15: # Ventana de advertencia preventiva (15 días)
            return "EXPIRING_SOON"
        else:
            return "VALID"
```

### Reglas de Expiración:
* **EXPIRED**: `expiration_date < fecha_actual`. El documento perdió validez jurídica.
* **EXPIRING_SOON**: `0 <= expiration_date - fecha_actual <= 15 días`. Se gatilla una alerta preventiva a operaciones sin bloquear aún la unidad.
* **VALID**: Documento vigente con más de 15 días de margen.
