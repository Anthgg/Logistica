"""Adversarial stress and concurrency test harness for Geocoding Rate Limiter and LRU Cache.

Author: Challenger 1 (Milestone M1)
Focus:
- AsyncRateLimiter interval enforcement under high concurrency burst & task cancellation.
- GeocodingLRUCache thread safety under multi-threaded contention, bounded eviction, TTL expiry, and key canonicalization.
- End-to-end GeocodingService concurrency: cache bypass vs rate limiter throttling.
"""

import asyncio
import concurrent.futures
import random
import threading
import time
from typing import List, Tuple
from unittest.mock import MagicMock

import pytest

from app.modules.logistics.geocoding.base import GeocodeLocationResult
from app.modules.logistics.geocoding.cache import GeocodingLRUCache
from app.modules.logistics.geocoding.rate_limiter import AsyncRateLimiter
from app.modules.logistics.geocoding.service import GeocodingService


# ============================================================================
# 1. AsyncRateLimiter Adversarial Concurrency Tests
# ============================================================================


@pytest.mark.asyncio
async def test_rate_limiter_high_concurrency_burst_intervals():
    """Stress test: 25 concurrent coroutines hitting AsyncRateLimiter simultaneously.

    Verifies that every single consecutive pair of acquisitions is spaced by at least
    min_interval (with a small 2ms tolerance for OS scheduler timer resolution).
    """
    # On Windows, standard asyncio.sleep timer resolution quantizes to ~15.6ms ticks
    min_interval = 0.08  # 80ms interval
    num_tasks = 20
    limiter = AsyncRateLimiter(min_interval_seconds=min_interval)

    timestamps: List[float] = []
    lock = asyncio.Lock()

    async def worker(worker_id: int):
        await limiter.acquire()
        now = time.monotonic()
        async with lock:
            timestamps.append(now)

    # Launch all workers at the exact same instant
    start_time = time.monotonic()
    await asyncio.gather(*(worker(i) for i in range(num_tasks)))
    total_duration = time.monotonic() - start_time

    assert len(timestamps) == num_tasks, f"Expected {num_tasks} timestamps, got {len(timestamps)}"

    sorted_ts = sorted(timestamps)
    intervals: List[float] = []
    violations = []
    tolerance = 0.016  # Windows 15.6ms timer quantum tolerance

    for i in range(1, len(sorted_ts)):
        dt = sorted_ts[i] - sorted_ts[i - 1]
        intervals.append(dt)
        if dt < (min_interval - tolerance):
            violations.append((i, dt, min_interval))

    print(f"\n[RateLimiter Concurrency] Tasks: {num_tasks}, MinInterval: {min_interval*1000:.1f}ms")
    print(f"[RateLimiter Concurrency] Total duration: {total_duration:.4f}s (Min expected: {(num_tasks-1)*min_interval:.4f}s)")
    print(f"[RateLimiter Concurrency] Min interval observed: {min(intervals)*1000:.2f}ms, Max: {max(intervals)*1000:.2f}ms, Avg: {sum(intervals)/len(intervals)*1000:.2f}ms")

    assert not violations, f"Rate limit interval violated in {len(violations)} instances: {violations}"
    assert total_duration >= ((num_tasks - 1) * min_interval - tolerance), (
        f"Total duration {total_duration:.4f}s was less than minimum expected {((num_tasks - 1) * min_interval):.4f}s"
    )


@pytest.mark.asyncio
async def test_rate_limiter_strict_one_second_interval():
    """Empirical verification with standard 1.0s interval for 3 consecutive calls."""
    min_interval = 1.0
    limiter = AsyncRateLimiter(min_interval_seconds=min_interval)

    t0 = time.monotonic()
    await limiter.acquire()
    t1 = time.monotonic()
    await limiter.acquire()
    t2 = time.monotonic()
    await limiter.acquire()
    t3 = time.monotonic()

    d1 = t2 - t1
    d2 = t3 - t2
    total = t3 - t0

    print(f"\n[1.0s Limiter] d1: {d1:.4f}s, d2: {d2:.4f}s, Total: {total:.4f}s")
    assert d1 >= 0.99, f"Interval 1 was {d1:.4f}s (< 0.99s)"
    assert d2 >= 0.99, f"Interval 2 was {d2:.4f}s (< 0.99s)"
    assert total >= 1.98, f"Total duration was {total:.4f}s (< 1.98s)"


@pytest.mark.asyncio
async def test_rate_limiter_task_cancellation_resilience():
    """Verify that cancelling a waiting task does not deadlock or corrupt the limiter."""
    min_interval = 0.05
    limiter = AsyncRateLimiter(min_interval_seconds=min_interval)

    # First acquire
    await limiter.acquire()

    # Launch task that will be cancelled while waiting inside acquire()
    task = asyncio.create_task(limiter.acquire())
    await asyncio.sleep(0.01)  # allow task to enter acquire()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Subsequent task must still be able to acquire without deadlock
    start = time.monotonic()
    await asyncio.wait_for(limiter.acquire(), timeout=1.0)
    elapsed = time.monotonic() - start
    print(f"\n[Cancellation Test] Subsequent acquire succeeded in {elapsed:.4f}s")


# ============================================================================
# 2. GeocodingLRUCache Adversarial Concurrency & Correctness Tests
# ============================================================================


def test_lru_cache_multi_threaded_hammering():
    """Stress test: 20 threads performing 500 concurrent operations each (total 10,000 ops).

    Operations include get, set, clear, stats, and size on a bounded cache (max_entries=30).
    Verifies thread-safety, no race conditions, no KeyErrors, and size <= max_entries.
    """
    max_entries = 30
    cache = GeocodingLRUCache(ttl_seconds=60, max_entries=max_entries)
    num_threads = 20
    ops_per_thread = 500
    errors: List[Exception] = []

    def worker(thread_id: int):
        try:
            for i in range(ops_per_thread):
                op = random.randint(0, 4)
                key = f"key_{random.randint(1, 100)}"
                val = f"val_{thread_id}_{i}"

                if op == 0 or op == 1:
                    # 40% writes
                    cache.set(key, val)
                elif op == 2 or op == 3:
                    # 40% reads
                    cache.get(key)
                elif op == 4:
                    # 20% stats / size check
                    s = cache.size()
                    st = cache.stats()
                    assert s <= max_entries, f"Cache size {s} exceeded max {max_entries}"
                    assert st["size"] <= max_entries
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Encountered {len(errors)} thread errors: {errors[:5]}"
    assert cache.size() <= max_entries, f"Final cache size {cache.size()} exceeded max {max_entries}"

    stats = cache.stats()
    print(f"\n[Cache Multi-Thread Hammer] Hits: {stats['hits']}, Misses: {stats['misses']}, Final Size: {stats['size']}/{max_entries}")


def test_lru_cache_strict_eviction_order():
    """Verify strict LRU eviction order across multiple sequential patterns."""
    cache = GeocodingLRUCache(ttl_seconds=300, max_entries=3)

    # Insert 3 keys: A, B, C (order: [A, B, C])
    cache.set("A", 1)
    cache.set("B", 2)
    cache.set("C", 3)
    assert cache.size() == 3

    # Access A -> order becomes [B, C, A]
    assert cache.get("A") == 1

    # Insert D -> should evict B (least recently used) -> order [C, A, D]
    cache.set("D", 4)
    assert cache.get("B") is None, "Key B should have been evicted"
    assert cache.get("C") == 3
    assert cache.get("A") == 1
    assert cache.get("D") == 4

    # Access C -> order [A, D, C]
    assert cache.get("C") == 3

    # Overwrite A -> order [D, C, A]
    cache.set("A", 10)

    # Insert E -> should evict D -> order [C, A, E]
    cache.set("E", 5)
    assert cache.get("D") is None, "Key D should have been evicted"
    assert cache.get("C") == 3
    assert cache.get("A") == 10
    assert cache.get("E") == 5


def test_lru_cache_ttl_expiration_precision(monkeypatch):
    """Verify TTL boundary conditions: exact TTL, sub-second precision, expired cleanup."""
    cache = GeocodingLRUCache(ttl_seconds=5, max_entries=10)

    simulated_time = 100.0
    monkeypatch.setattr(time, "monotonic", lambda: simulated_time)

    cache.set("key1", "val1")
    cache.set("key2", "val2")

    # Time + 4.99s -> still valid
    simulated_time = 104.99
    assert cache.get("key1") == "val1"
    assert cache.get("key2") == "val2"
    assert cache.stats()["hits"] == 2

    # Time + 5.01s -> expired
    simulated_time = 105.01
    assert cache.get("key1") is None
    assert cache.get("key2") is None
    assert cache.stats()["misses"] == 2
    assert cache.size() == 0, "Expired entries must be removed on get()"


def test_lru_cache_key_canonicalization_adversarial_inputs():
    """Verify key canonicalization with whitespace, unicode, accents, case, and precision."""
    # Search key canonicalization
    assert GeocodingLRUCache.make_search_key("  Av.   Larco \t\n 1234  ", limit=5) == "search:av. larco 1234:5"
    assert GeocodingLRUCache.make_search_key("AV. LARCO 1234", limit=5) == "search:av. larco 1234:5"
    assert GeocodingLRUCache.make_search_key("", limit=3) == "search::3"
    assert GeocodingLRUCache.make_search_key(None, limit=5) == "search::5"  # type: ignore

    # Reverse key canonicalization (5 decimal places rounding)
    # -12.1234549 -> -12.12345
    # -12.1234551 -> -12.12346
    assert GeocodingLRUCache.make_reverse_key(-12.1234549, -77.0123449) == "reverse:-12.12345:-77.01234"
    assert GeocodingLRUCache.make_reverse_key(-12.1234551, -77.0123451) == "reverse:-12.12346:-77.01235"

    # Extreme coordinate bounds
    assert GeocodingLRUCache.make_reverse_key(-90.0, -180.0) == "reverse:-90.00000:-180.00000"
    assert GeocodingLRUCache.make_reverse_key(90.0, 180.0) == "reverse:90.00000:180.00000"
    assert GeocodingLRUCache.make_reverse_key(0.0, 0.0) == "reverse:0.00000:0.00000"


# ============================================================================
# 3. Service Level Integration Stress Test (Cache Hits vs Rate Limiting)
# ============================================================================


@pytest.mark.asyncio
async def test_geocoding_service_concurrent_cache_hits_bypass_rate_limiter():
    """Verify that cached queries return instantly without throttling, while misses are rate limited."""
    mock_provider = MagicMock()
    sample_res = [GeocodeLocationResult(latitude=-12.0, longitude=-77.0, display_name="Test")]
    mock_provider.search = MagicMock(return_value=asyncio.Future())
    mock_provider.search.return_value.set_result(sample_res)

    cache = GeocodingLRUCache(ttl_seconds=300, max_entries=100)
    rate_limiter = AsyncRateLimiter(min_interval_seconds=0.5)
    service = GeocodingService(provider=mock_provider, cache=cache, rate_limiter=rate_limiter)

    # Prime cache
    await service.search_address("Av. Larco 100")
    assert mock_provider.search.call_count == 1

    # Launch 10 concurrent requests for the SAME cached address
    t_start = time.monotonic()
    tasks = [service.search_address("Av. Larco 100") for _ in range(10)]
    results = await asyncio.gather(*tasks)
    elapsed = time.monotonic() - t_start

    print(f"\n[Cached Service Burst] 10 concurrent hits completed in {elapsed*1000:.2f}ms")
    assert elapsed < 0.1, f"10 cache hits took {elapsed:.4f}s; should be < 0.1s without rate limiter delay"
    assert mock_provider.search.call_count == 1
    assert all(r == sample_res for r in results)
    assert cache.stats()["hits"] == 10
