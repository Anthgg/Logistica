# 08. Algoritmo ResolveAuthorizedSigner y Estampa de Firma Visual

## 🧠 Algoritmo de Resolución Dinámica ResolveAuthorizedSigner

Durante el proceso de emisión o previsualización de un documento logístico (Fase 020), el sistema debe determinar qué firmante institucional es legalmente válido para suscribir la transacción.

El algoritmo se implementa en `SignerService.resolve_authorized_signer`:

```python
def resolve_authorized_signer(
    self,
    organization_id: UUID,
    branch_id: UUID | None,
    document_family: str,
    document_type_code: str,
    amount: Decimal | None = None,
    currency_code: str | None = None,
    requested_signer_id: UUID | None = None,
) -> dict[str, Any]:
    now = utc_now()

    # 1. Filtrar firmantes activos en ventana de vigencia
    query = select(AuthorizedSignerModel).where(
        and_(
            AuthorizedSignerModel.organization_id == organization_id,
            AuthorizedSignerModel.status == "ACTIVE",
            AuthorizedSignerModel.valid_from <= now,
            or_(AuthorizedSignerModel.valid_until.is_(None), AuthorizedSignerModel.valid_until >= now),
        )
    )

    if requested_signer_id:
        query = query.where(AuthorizedSignerModel.id == requested_signer_id)

    signers = self.db.scalars(query).all()
    warnings = []
    valid_signer = None

    # 2. Evaluación determinística de alcances
    for s in signers:
        # A. Alcance por Sede
        if not s.can_sign_all_branches and branch_id:
            if s.branch_scope and str(branch_id) not in s.branch_scope:
                warnings.append(f"Firmante '{s.full_name}' no tiene alcance en la sede especificada.")
                continue

        # B. Alcance por Familia Documental
        if s.document_family_scope and document_family.upper() not in s.document_family_scope:
            warnings.append(f"Firmante '{s.full_name}' no tiene alcance en la familia '{document_family}'.")
            continue

        # C. Alcance por Tipo de Documento
        if s.document_type_scope and document_type_code.upper() not in s.document_type_scope:
            warnings.append(f"Firmante '{s.full_name}' no tiene alcance en el tipo '{document_type_code}'.")
            continue

        # D. Límite de Monto
        if amount and s.max_amount:
            if amount > s.max_amount:
                warnings.append(f"Monto de documento ({amount}) excede el límite autorizado del firmante ({s.max_amount}).")
                continue

        valid_signer = s
        break

    if not valid_signer:
        return {
            "signer": None,
            "authorization_status": "NO_AUTHORIZED_SIGNER",
            "signature_asset": None,
            "warnings": warnings or ["No se encontró ningún firmante activo y autorizado para este alcance."],
        }

    # 3. Resolver activo de firma visual asociada
    sig_asset = None
    if valid_signer.signature_asset_id:
        asset = self.db.get(OrganizationAssetModel, valid_signer.signature_asset_id)
        if asset and asset.status == "ACTIVE":
            sig_asset = {
                "asset_id": str(asset.id),
                "filename": asset.filename,
                "file_hash": asset.file_hash,
                "mime_type": asset.mime_type,
            }

    return {
        "signer": {
            "id": str(valid_signer.id),
            "full_name": valid_signer.full_name,
            "position_title": valid_signer.position_title,
            "department": valid_signer.department,
            "authorization_type": valid_signer.authorization_type,
            "document_number_masked": valid_signer.document_number_masked,
        },
        "authorization_status": "AUTHORIZED",
        "signature_asset": sig_asset,
        "warnings": [],
    }
```

---

## 🖼️ Firma Visual y Estampa en Documentos

Cuando la resolución retorna un firmante válido (`authorization_status = "AUTHORIZED"`):

1. **Inclusión de Firma Visual**: Si el firmante cuenta con un activo de firma asignado (`signature_asset_id`), la imagen PNG/JPEG sanitizada se recupera mediante `AssetService.get_asset_content`.
2. **Renderizado en Plantilla PDF**: El motor de la Fase 020 coloca la firma visual, el nombre completo, el cargo, el DNI enmascarado y la referencia de la autorización en la sección del bloque de firmas.
3. **Resguardo de Integridad**: El `file_hash` de la imagen de la firma queda congelado dentro del snapshot documental del PDF emitido.
