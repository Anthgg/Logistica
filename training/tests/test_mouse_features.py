from src.behavioral.mouse_features import extract_mouse_features


def _mouse_events():
    return [
        {
            "type": "mouse",
            "event": "move",
            "timestamp": "2026-01-01T12:00:00+00:00",
            "normalized_x": 0.0,
            "normalized_y": 0.0,
        },
        {
            "type": "mouse",
            "event": "move",
            "timestamp": "2026-01-01T12:00:01+00:00",
            "normalized_x": 0.3,
            "normalized_y": 0.4,
        },
    ]


def test_mouse_velocity_is_calculated(config):
    result = extract_mouse_features(_mouse_events(), 10, config.behavioral)
    assert result["mean_velocity"] == 0.5


def test_mouse_distance_is_calculated(config):
    result = extract_mouse_features(_mouse_events(), 10, config.behavioral)
    assert result["total_distance"] == 0.5
