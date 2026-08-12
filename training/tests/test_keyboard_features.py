from src.behavioral.keyboard_features import extract_keyboard_features


def _keyboard_events():
    return [
        {
            "type": "keyboard",
            "dwell_time_ms": 100.0,
            "flight_time_ms": 40.0,
            "interval_from_previous_ms": 100.0,
            "category": "alphanumeric",
        },
        {
            "type": "keyboard",
            "dwell_time_ms": 200.0,
            "flight_time_ms": 60.0,
            "interval_from_previous_ms": 300.0,
            "category": "correction",
            "is_backspace": True,
        },
    ]


def test_dwell_is_calculated(config):
    result = extract_keyboard_features(_keyboard_events(), 10, config.behavioral)
    assert result["dwell_mean"] == 150.0
    assert result["dwell_median"] == 150.0


def test_flight_is_calculated(config):
    result = extract_keyboard_features(_keyboard_events(), 10, config.behavioral)
    assert result["flight_mean"] == 50.0


def test_keyboard_ratios_are_calculated(config):
    result = extract_keyboard_features(_keyboard_events(), 10, config.behavioral)
    assert result["correction_ratio"] == 0.5
    assert result["typing_event_rate"] == 0.2
