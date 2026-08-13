import pytest


class SequenceGapDetector:
    """Verifica la continuidad de la secuencia del ledger (1001, 1002, 1003...)."""

    @staticmethod
    def validate_sequence(last_applied_sequence: int, incoming_sequence: int) -> bool:
        if incoming_sequence != last_applied_sequence + 1:
            raise ValueError(
                f"SEQUENCE_GAP_DETECTED: Expected sequence {last_applied_sequence + 1}, "
                f"but received sequence {incoming_sequence}. Cursor halted."
            )
        return True


def test_sequence_continuation_success():
    assert SequenceGapDetector.validate_sequence(1001, 1002) is True


def test_sequence_gap_failure():
    with pytest.raises(ValueError, match="SEQUENCE_GAP_DETECTED"):
        SequenceGapDetector.validate_sequence(1001, 1004)
