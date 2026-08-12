from collections import defaultdict


class DuplicateDetector:
    def __init__(self) -> None:
        self._capture_ids: dict[str, list[str]] = defaultdict(list)

    def add(self, capture_id: str, checksum: str) -> bool:
        duplicated = bool(self._capture_ids[checksum])
        self._capture_ids[checksum].append(capture_id)
        return duplicated

    def duplicate_groups(self) -> dict[str, list[str]]:
        return {
            checksum: capture_ids
            for checksum, capture_ids in self._capture_ids.items()
            if len(capture_ids) > 1
        }
