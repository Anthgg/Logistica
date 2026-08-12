# 08 — `InventoryPosition`

Las posiciones son **dimensiones**, no cantidades.

`dimension_key` = SHA-256 sobre canonical JSON de los componentes que
definen una dimensión:

- organization_id, branch_id, warehouse_id, warehouse_location_id
- boundary_type ∈ `INTERNAL_LOCATION / INTERNAL_STAGING / INTERNAL_QUARANTINE / INTERNAL_TRANSIT / EXTERNAL_SUPPLIER / EXTERNAL_CUSTOMER / EXTERNAL_CARRIER / EXTERNAL_UNKNOWN / SYSTEM_OPENING_BALANCE / SYSTEM_COMPENSATION`
- product_id, product_version_id
- ownership_type, owner_business_partner_id
- availability_state ∈ `AVAILABLE / RESERVED / BLOCKED / NOT_AVAILABLE / PENDING_PUTAWAY / PICKED_FUTURE / DISPATCHED_FUTURE / IN_TRANSIT / UNKNOWN`
- quality_state ∈ `NOT_ASSESSED / QUARANTINE / APPROVED / REJECTED / DAMAGED / EXPIRED / CONDITIONAL / UNKNOWN`
- transit_state ∈ `NOT_IN_TRANSIT / INBOUND_STAGING / INTERNAL_TRANSFER / BETWEEN_WAREHOUSES / OUTBOUND_STAGING / EXTERNAL_TRANSIT`
- damage_state ∈ `NORMAL / DAMAGED / SUSPECTED_DAMAGE / REWORK_FUTURE / UNKNOWN`
- expiration_state ∈ `NOT_APPLICABLE / VALID / NEAR_EXPIRATION / EXPIRED / UNKNOWN`
- tracking_reference_type / tracking_reference_hash / handling_unit_reference_hash

Las posiciones con la misma `dimension_key` reusan la misma fila.
