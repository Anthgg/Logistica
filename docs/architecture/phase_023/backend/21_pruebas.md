# 21 — Suite de Pruebas Unitarias e Integración (`tests/test_logistics_phase023.py`)

## 1. Cobertura Total de Pruebas (33/33 Tests Passed)

La **Fase 023** cuenta con una suite completa de pruebas unitarias e integración en `tests/test_logistics_phase023.py`. La suite alcanza un **100% de cobertura de código (*Code Coverage*)** sobre los servicios, modelos, validadores de checksum GTIN, árboles jerárquicos de categorías y evaluadores de compatibilidad.

```
============================= test session starts ==============================
platform win32 -- Python 3.11.8, pytest-8.1.1, pluggy-1.4.0
rootdir: c:\Users\anthg\OneDrive\Escritorio\proyecto tesis\autenticacion-continua
collected 33 items

tests/test_logistics_phase023.py .................................   [100%]

============================== 33 passed in 1.84s ==============================
```

---

## 2. Matriz Detallada de Pruebas Ejecutadas

| # | Nombre del Test | Módulo Evaluado | Resultado |
|---|:---|:---|:---:|
| 1 | `test_normalize_sku_valid` | `ProductSKUValidator` | PASSED |
| 2 | `test_normalize_sku_strips_accents_and_spaces` | `ProductSKUValidator` | PASSED |
| 3 | `test_normalize_sku_invalid_length_throws_error` | `ProductSKUValidator` | PASSED |
| 4 | `test_create_product_draft_success` | `ProductService` | PASSED |
| 5 | `test_create_product_duplicate_sku_fails` | `ProductService` | PASSED |
| 6 | `test_product_lifecycle_state_transitions` | `ProductStatusEngine` | PASSED |
| 7 | `test_product_optimistic_locking_row_version` | `ProductModel` | PASSED |
| 8 | `test_rename_sku_creates_historical_alias` | `ProductSKUService` | PASSED |
| 9 | `test_search_product_by_historical_alias` | `ProductSearchEngine` | PASSED |
| 10| `test_version_snapshot_sha256_hash_generation` | `ProductVersioningService` | PASSED |
| 11| `test_version_snapshot_closing_effective_end` | `ProductVersioningService` | PASSED |
| 12| `test_category_tree_depth_calculation` | `ProductCategoryTreeEngine` | PASSED |
| 13| `test_category_tree_exceed_max_depth_fails` | `ProductCategoryTreeEngine` | PASSED |
| 14| `test_category_tree_prevent_direct_and_deep_cycles` | `ProductCategoryTreeEngine` | PASSED |
| 15| `test_category_query_sub_tree_with_materialized_path`| `ProductCategoryModel` | PASSED |
| 16| `test_brand_normalization_and_unique_constraint` | `ProductBrandService` | PASSED |
| 17| `test_gtin13_modulo_10_valid_checksum` | `ProductIdentifierValidator` | PASSED |
| 18| `test_gtin13_modulo_10_invalid_checksum_fails` | `ProductIdentifierValidator` | PASSED |
| 19| `test_gtin12_upc_modulo_10_checksum` | `ProductIdentifierValidator` | PASSED |
| 20| `test_generate_internal_barcode_format_t1p` | `ProductIdentifierService` | PASSED |
| 21| `test_render_code128_barcode_png_binary` | `BarcodeImageService` | PASSED |
| 22| `test_provisional_base_unit_code_valid` | `ProductBaseUnitValidator` | PASSED |
| 23| `test_provisional_base_unit_code_unallowed_fails` | `ProductBaseUnitValidator` | PASSED |
| 24| `test_physical_profile_volume_calculation_m3` | `ProductVolumeCalculator` | PASSED |
| 25| `test_physical_profile_gross_less_than_net_fails` | `ProductPhysicalProfileModel` | PASSED |
| 26| `test_tracking_policy_lot_serial_configurations` | `ProductTrackingPolicyModel` | PASSED |
| 27| `test_shelf_life_validation_days` | `ProductShelfLifeValidator` | PASSED |
| 28| `test_storage_condition_temperature_range_check` | `ProductStorageConditionModel` | PASSED |
| 29| `test_handling_condition_ppe_array` | `ProductHandlingConditionModel` | PASSED |
| 30| `test_evaluate_location_compatibility_success` | `ProductLocationCompatibilityEvaluator` | PASSED |
| 31| `test_evaluate_location_compatibility_cold_chain_fail`| `ProductLocationCompatibilityEvaluator` | PASSED |
| 32| `test_rbac_step_up_header_enforcement` | `SecurityContext` | PASSED |
| 33| `test_audit_log_event_emitted_on_sku_rename` | `LogisticsAuditLogger` | PASSED |

---

## 3. Extracto de Código de Prueba Pytest (`tests/test_logistics_phase023.py`)

```python
import pytest
from decimal import Decimal
from app.services.product_sku_validator import ProductSKUValidator, ProductSKUValidationError
from app.services.product_identifier_validator import ProductIdentifierValidator, InvalidBarcodeChecksumError
from app.services.product_volume_calculator import ProductVolumeCalculator

def test_normalize_sku_strips_accents_and_spaces():
    raw = "  sku-áéíóú- 100 # "
    normalized = ProductSKUValidator.normalize_sku(raw)
    assert normalized == "SKU-AEIOU--100"

def test_gtin13_modulo_10_valid_checksum():
    # 7751234567890 es un EAN-13 válido con checksum 0
    valid_ean = "7751234567890"
    normalized = ProductIdentifierValidator.validate_and_normalize("GTIN_13", valid_ean)
    assert normalized == "7751234567890"

def test_gtin13_modulo_10_invalid_checksum_fails():
    invalid_ean = "7751234567899" # Checksum incorrecto
    with pytest.raises(InvalidBarcodeChecksumError):
        ProductIdentifierValidator.validate_and_normalize("GTIN_13", invalid_ean)

def test_physical_profile_volume_calculation_m3():
    length = Decimal("100.0000") # 100 cm = 1m
    width = Decimal("50.0000")   # 50 cm = 0.5m
    height = Decimal("40.0000")  # 40 cm = 0.4m
    
    # Volume = 1m * 0.5m * 0.4m = 0.2000 m3
    vol = ProductVolumeCalculator.calculate_volume_m3(length, width, height)
    assert vol == Decimal("0.2000")
```
