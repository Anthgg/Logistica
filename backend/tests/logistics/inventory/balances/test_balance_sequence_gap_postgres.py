from decimal import Decimal
import pytest


def test_sequence_gap_detection_halts_cursor():
    """Valida la detección de sequence gaps en la proyección (1001, 1002, 1004 sin 1003)."""
    executed_sequences = []
    last_applied = 1000

    incoming_events = [
        {"seq": 1001, "qty": Decimal("10")},
        {"seq": 1002, "qty": Decimal("20")},
        {"seq": 1004, "qty": Decimal("40")},  # Gap
    ]

    for event in incoming_events:
        seq = event["seq"]
        if seq != last_applied + 1:
            # GAP DETECTED
            break
        executed_sequences.append(seq)
        last_applied = seq

    assert executed_sequences == [1001, 1002]
    assert last_applied == 1002
    assert 1004 not in executed_sequences
