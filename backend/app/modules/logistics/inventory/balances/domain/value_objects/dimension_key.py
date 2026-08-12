import hashlib


class DimensionKeyBuilder:
    """Construye una clave canónica e inmutable SHA-256 a partir de la tupla dimensional."""

    @staticmethod
    def build(
        organization_id: str,
        branch_id: str,
        warehouse_id: str | None,
        warehouse_location_id: str | None,
        product_id: str,
        product_version_id: str | None,
        availability_state: str,
        quality_state: str,
        transit_state: str,
        damage_state: str,
        expiration_state: str,
        ownership_type: str = "OWNED",
        owner_business_partner_id: str | None = None,
    ) -> str:
        parts = [
            str(organization_id),
            str(branch_id),
            str(warehouse_id or ""),
            str(warehouse_location_id or ""),
            str(product_id),
            str(product_version_id or ""),
            str(availability_state).upper(),
            str(quality_state).upper(),
            str(transit_state).upper(),
            str(damage_state).upper(),
            str(expiration_state).upper(),
            str(ownership_type).upper(),
            str(owner_business_partner_id or ""),
        ]
        raw_key = "|".join(parts)
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
