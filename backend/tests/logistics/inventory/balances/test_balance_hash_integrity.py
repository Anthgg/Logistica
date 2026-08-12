import hashlib
import pytest


class HashIntegrityVerifier:
    """Valida la integridad de la cadena de hash del ledger MOV antes de proyecciones."""

    @staticmethod
    def verify_hash(raw_payload: str, expected_hash: str) -> bool:
        computed = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
        if computed != expected_hash:
            raise ValueError(f"HASH_MISMATCH: Computed {computed} does not match expected {expected_hash}.")
        return True


def test_hash_integrity_valid():
    payload = "mov:1001|partition:wh-1|seq:1"
    expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert HashIntegrityVerifier.verify_hash(payload, expected) is True


def test_hash_integrity_mismatch():
    payload = "mov:1001|partition:wh-1|seq:1"
    tampered_payload = "mov:1001|partition:wh-1|seq:1|tampered"
    expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        HashIntegrityVerifier.verify_hash(tampered_payload, expected)
