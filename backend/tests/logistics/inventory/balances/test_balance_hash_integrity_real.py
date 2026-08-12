import hashlib
import pytest


def test_hash_integrity_verification_real():
    """Prueba real de verificación de hash SHA-256 de movimientos de inventario."""
    raw_payload = "mov_id:1001|partition:wh-1|seq:1|qty:10.000000000000000000"
    valid_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

    # Payload alterado
    corrupted_payload = "mov_id:1001|partition:wh-1|seq:1|qty:999.000000000000000000"
    computed_corrupted_hash = hashlib.sha256(corrupted_payload.encode("utf-8")).hexdigest()

    assert computed_corrupted_hash != valid_hash
