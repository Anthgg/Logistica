# 10. Políticas de Presentación de Numeración

## 🔢 Modelo OrganizationNumberingDisplayPolicyModel

El modelo `OrganizationNumberingDisplayPolicyModel` (`organization_numbering_display_policies`) define las reglas de formateo y presentación estética del código visible de un documento en PDF/pantalla, sin alterar la secuencia pura en base de datos ni los talonarios ni correlativos de las Fases 012/013.

```python
class OrganizationNumberingDisplayPolicyModel(Base):
    __tablename__ = "organization_numbering_display_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    branch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("logistics_branches.id", ondelete="SET NULL"), nullable=True
    )
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_types.id", ondelete="CASCADE"), nullable=False
    )
    code_standard_version: Mapped[str] = mapped_column(String(32), default="1.0.0", server_default=text("'1.0.0'"), nullable=False)
    document_site_code_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_site_codes.id", ondelete="SET NULL"), nullable=True
    )

    display_pattern: Mapped[str] = mapped_column(
        String(128), default="{TYPE}-{SITE}-{YEAR}-{SEQUENCE}", server_default=text("'{TYPE}-{SITE}-{YEAR}-{SEQUENCE}'"), nullable=False
    )
    sequence_padding: Mapped[int] = mapped_column(Integer, default=6, server_default=text("6"), nullable=False)

    show_internal_code: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_external_series: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    show_external_number: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", server_default=text("'ACTIVE'"), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
```

---

## 🧩 Parser y Tokens de Formateo de Numeración

El servicio `NumberingPolicyService` utiliza `validate_numbering_display_pattern` para validar y aplicar la sustitución de tokens dinámicos en el patrón de presentación:

### Tokens Permitidos:
* `{TYPE}`: Código corto del tipo de documento (ej. `PED`, `GRE`, `ACT`).
* `{SITE}`: Código corto de la sede / sitio (ej. `LIM`, `AQP`).
* `{YEAR}`: Año de emisión en 4 dígitos (ej. `2026`).
* `{SEQUENCE}`: Correlativo numérico formateado con el relleno especificado (`sequence_padding`).
* `{EXTERNAL_SERIES}`: Serie del comprobante o guía de remisión física (ej. `T001`).
* `{EXTERNAL_NUMBER}`: Correlativo físico del comprobante (ej. `00004589`).

### Ejemplos de Formateo:

| Patrón (`display_pattern`) | Correlativo DB | Padding | Código Resultante |
|---|---|---|---|
| `{TYPE}-{SITE}-{YEAR}-{SEQUENCE}` | `123` | `6` | `PED-LIM-2026-000123` |
| `{SITE}/{TYPE}/{YEAR}/{SEQUENCE}` | `45` | `8` | `AQP/GRE/2026/00000045` |
| `DOC-{YEAR}-{SEQUENCE}` | `7` | `4` | `DOC-2026-0007` |

---

## 🛡️ Desacoplamiento Estricto de la Reserva de Correlativo (Fases 012/013)

Es fundamental destacar que la política de presentación de numeración **NO reserva, consume ni incrementa la secuencia pura en base de datos**.

1. **Relleno Estético Solamente**: El formateo es una transformación puramente de presentación realizada por `NumberingPolicyService.format_display_number`.
2. **Previsualización Segura**: El endpoint `/company-profile/numbering-policies/preview` permite a los administradores probar distintos patrones de visualización en tiempo real sin quemar ni saltear números correlativos de las secuencias operativas del sistema.
