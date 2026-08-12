import random

import numpy as np

from src.common.reproducibility import configure_reproducibility


def test_same_seed_reproduces_python_and_numpy() -> None:
    configure_reproducibility(42, deterministic_operations=False)
    first = (random.random(), np.random.random())
    configure_reproducibility(42, deterministic_operations=False)
    second = (random.random(), np.random.random())
    assert first == second
