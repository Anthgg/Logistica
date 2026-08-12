from copy import deepcopy

from src.behavioral.event_validator import validate_batch


def test_valid_batch_is_accepted(valid_batch, config):
    result = validate_batch(valid_batch, config.behavioral)
    assert result.valid
    assert result.events


def _forbidden(valid_batch, config, key):
    batch = deepcopy(valid_batch)
    batch["payload"][0][key] = "never copied"
    return validate_batch(batch, config.behavioral)


def test_key_property_is_rejected(valid_batch, config):
    assert "FORBIDDEN_TEXTUAL_DATA_DETECTED" in _forbidden(
        valid_batch, config, "key"
    ).rejection_reasons


def test_code_property_is_rejected(valid_batch, config):
    assert "FORBIDDEN_TEXTUAL_DATA_DETECTED" in _forbidden(
        valid_batch, config, "code"
    ).rejection_reasons


def test_text_property_is_rejected(valid_batch, config):
    assert "FORBIDDEN_TEXTUAL_DATA_DETECTED" in _forbidden(
        valid_batch, config, "text"
    ).rejection_reasons


def test_password_property_is_rejected(valid_batch, config):
    assert "FORBIDDEN_TEXTUAL_DATA_DETECTED" in _forbidden(
        valid_batch, config, "password"
    ).rejection_reasons


def test_out_of_range_coordinate_is_rejected(valid_batch, config):
    batch = deepcopy(valid_batch)
    mouse = next(event for event in batch["payload"] if event["type"] == "mouse")
    mouse["normalized_x"] = 1.5
    assert "VALUE_OUT_OF_RANGE" in validate_batch(
        batch, config.behavioral
    ).rejection_reasons


def test_duplicate_event_is_detected(valid_batch, config):
    batch = deepcopy(valid_batch)
    duplicate = deepcopy(batch["payload"][0])
    batch["payload"].append(duplicate)
    assert "DUPLICATE_EVENT" in validate_batch(
        batch, config.behavioral
    ).rejection_reasons


def test_duplicate_batch_is_detected(valid_batch, config):
    seen: set[str] = set()
    assert validate_batch(
        valid_batch, config.behavioral, seen_batch_ids=seen
    ).valid
    assert "DUPLICATE_BATCH" in validate_batch(
        valid_batch, config.behavioral, seen_batch_ids=seen
    ).rejection_reasons


def test_forbidden_batch_does_not_copy_payload(valid_batch, config):
    result = _forbidden(valid_batch, config, "typed_text")
    assert result.events == []
