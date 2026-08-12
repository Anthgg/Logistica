import math

import numpy as np

from src.common.config import BehavioralConfig
from src.common.timestamps import ensure_utc


def extract_mouse_features(
    events: list[dict[str, object]],
    duration_seconds: float,
    config: BehavioralConfig,
) -> dict[str, float]:
    mouse = sorted(
        (event for event in events if event.get("type") == "mouse"),
        key=lambda event: ensure_utc(str(event["timestamp"])),
    )
    moves = [
        event
        for event in mouse
        if event.get("event") == "move"
        and isinstance(event.get("normalized_x"), (int, float))
        and isinstance(event.get("normalized_y"), (int, float))
    ]
    distances: list[float] = []
    velocities: list[float] = []
    directions: list[float] = []
    active_seconds = 0.0
    for left, right in zip(moves, moves[1:]):
        dx = float(right["normalized_x"]) - float(left["normalized_x"])
        dy = float(right["normalized_y"]) - float(left["normalized_y"])
        distance = math.hypot(dx, dy)
        delta = (
            ensure_utc(str(right["timestamp"]))
            - ensure_utc(str(left["timestamp"]))
        ).total_seconds()
        distances.append(distance)
        directions.append(math.atan2(dy, dx))
        if delta > 0:
            velocities.append(distance / delta)
            active_seconds += min(delta, config.mouse_idle_threshold_ms / 1000)
    accelerations = [
        right - left for left, right in zip(velocities, velocities[1:])
    ]
    direction_changes = sum(
        abs(right - left) > math.pi / 4
        for left, right in zip(directions, directions[1:])
    )
    x_values = np.asarray([float(event["normalized_x"]) for event in moves])
    y_values = np.asarray([float(event["normalized_y"]) for event in moves])
    direct_distance = (
        math.hypot(x_values[-1] - x_values[0], y_values[-1] - y_values[0])
        if len(moves) > 1
        else 0.0
    )
    total_distance = float(sum(distances))
    movement_count = sum(event.get("event") == "move" for event in mouse)
    click_count = sum(event.get("event") == "click" for event in mouse)
    scroll_count = sum(event.get("event") == "scroll" for event in mouse)
    gaps = [
        (
            ensure_utc(str(right["timestamp"]))
            - ensure_utc(str(left["timestamp"]))
        ).total_seconds()
        for left, right in zip(mouse, mouse[1:])
    ]
    idle_seconds = sum(
        gap
        for gap in gaps
        if gap > config.mouse_idle_threshold_ms / 1000
    )
    return {
        "movement_count": float(movement_count),
        "click_count": float(click_count),
        "scroll_count": float(scroll_count),
        "pointer_down_count": float(
            sum(event.get("event") == "pointerdown" for event in mouse)
        ),
        "pointer_up_count": float(
            sum(event.get("event") == "pointerup" for event in mouse)
        ),
        "total_distance": total_distance,
        "mean_velocity": float(np.mean(velocities)) if velocities else 0.0,
        "velocity_std": float(np.std(velocities)) if velocities else 0.0,
        "maximum_velocity": max(velocities, default=0.0),
        "mean_acceleration": (
            float(np.mean(accelerations)) if accelerations else 0.0
        ),
        "acceleration_std": (
            float(np.std(accelerations)) if accelerations else 0.0
        ),
        "direction_change_count": float(direction_changes),
        "click_rate": click_count / duration_seconds if duration_seconds else 0.0,
        "scroll_rate": scroll_count / duration_seconds if duration_seconds else 0.0,
        "mouse_idle_ratio": (
            max(0.0, min(1.0, idle_seconds / duration_seconds))
            if duration_seconds
            else 1.0
        ),
        "path_straightness": (
            direct_distance / total_distance if total_distance else 0.0
        ),
        "normalized_x_mean": float(np.mean(x_values)) if len(x_values) else np.nan,
        "normalized_x_std": float(np.std(x_values)) if len(x_values) else np.nan,
        "normalized_y_mean": float(np.mean(y_values)) if len(y_values) else np.nan,
        "normalized_y_std": float(np.std(y_values)) if len(y_values) else np.nan,
        "movement_active_time_ratio": (
            max(0.0, min(1.0, active_seconds / duration_seconds))
            if duration_seconds
            else 0.0
        ),
    }
