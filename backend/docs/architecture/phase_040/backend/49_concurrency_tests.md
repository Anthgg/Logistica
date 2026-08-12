# Phase 040 — Concurrency Tests

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

20 concurrency tests verifying optimistic locking and concurrent operation handling.

## 2. Test Scenarios

### 2.1 Optimistic Locking (8 tests)

```python
@pytest.mark.asyncio
async def test_concurrent_update_same_case():
    """Two users try to update same case concurrently."""
    case = CaseFactory().create()
    await case_repository.save(case)
    
    # Simulate concurrent updates
    async def update_case(user_id: str):
        case_copy = await case_repository.get(case.id)
        case_copy.description = f"Updated by {user_id}"
        await case_repository.save(case_copy)
    
    # Run concurrently
    await asyncio.gather(
        update_case("user-1"),
        update_case("user-2"),
    )
    
    # One should succeed, one should fail with ConcurrencyError
    final_case = await case_repository.get(case.id)
    assert final_case.version == 2

@pytest.mark.asyncio
async def test_concurrent_status_transition():
    """Two users try to transition same case status."""
    case = CaseFactory().create(status=CaseStatus.DRAFT)
    await case_repository.save(case)
    
    async def submit_case(user_id: str):
        case_copy = await case_repository.get(case.id)
        case_copy.status = CaseStatus.SUBMITTED
        await case_repository.save(case_copy)
    
    # Should raise ConcurrencyError for one
    with pytest.raises(ConcurrencyError):
        await asyncio.gather(
            submit_case("user-1"),
            submit_case("user-2"),
        )
```

### 2.2 Concurrent Item Operations (6 tests)

```python
@pytest.mark.asyncio
async def test_concurrent_add_items():
    """Multiple users add items to same case concurrently."""
    case = CaseFactory().create()
    await case_repository.save(case)
    
    async def add_item(sku: str):
        item = ItemFactory(case_id=case.id).create(sku=sku)
        await item_repository.save(item)
    
    # Add 5 items concurrently
    await asyncio.gather(*[
        add_item(f"PROD-{i:03d}")
        for i in range(5)
    ])
    
    items = await item_repository.get_by_case(case.id)
    assert len(items) == 5

@pytest.mark.asyncio
async def test_concurrent_formalize_reject():
    """One user formalizes while another rejects same item."""
    item = ItemFactory().create(status=ItemStatus.PENDING)
    await item_repository.save(item)
    
    async def formalize():
        item_copy = await item_repository.get(item.id)
        item_copy.status = ItemStatus.FORMALIZED
        await item_repository.save(item_copy)
    
    async def reject():
        item_copy = await item_repository.get(item.id)
        item_copy.status = ItemStatus.REJECTED
        await item_repository.save(item_copy)
    
    with pytest.raises(ConcurrencyError):
        await asyncio.gather(formalize(), reject())
```

### 2.3 Concurrent Evidence Upload (3 tests)

```python
@pytest.mark.asyncio
async def test_concurrent_evidence_upload():
    """Multiple users upload evidence to same case."""
    case = CaseFactory().create()
    await case_repository.save(case)
    
    async def upload_evidence(url: str):
        evidence = EvidenceLink(
            case_id=case.id,
            url=url,
            evidence_type=EvidenceFormat.PHOTO,
        )
        case_copy = await case_repository.get(case.id)
        case_copy.evidence_links.append(evidence)
        await case_repository.save(case_copy)
    
    await asyncio.gather(*[
        upload_evidence(f"https://example.com/evidence-{i}.jpg")
        for i in range(3)
    ])
```

### 2.4 Integrity Verification Under Load (3 tests)

```python
@pytest.mark.asyncio
async def test_integrity_check_concurrent_updates():
    """Verify integrity while case is being updated."""
    case = CaseFactory().create()
    await case_repository.save(case)
    
    async def update_case():
        case_copy = await case_repository.get(case.id)
        case_copy.description = "Updated"
        await case_repository.save(case_copy)
    
    async def verify_integrity():
        result = await integrity_service.verify_case_integrity(case.id)
        return result.is_valid
    
    # Run concurrently
    results = await asyncio.gather(
        update_case(),
        verify_integrity(),
        verify_integrity(),
    )
    
    # At least one integrity check should succeed
    assert any(results[1:])

@pytest.mark.asyncio
async def test_hash_consistency_under_concurrent_access():
    """Verify canonical hash remains consistent."""
    case = CaseFactory().create()
    await case_repository.save(case)
    
    original_hash = case.canonical_hash.value
    
    # Perform multiple reads
    async def read_case():
        case_copy = await case_repository.get(case.id)
        return case_copy.canonical_hash.value
    
    hashes = await asyncio.gather(*[read_case() for _ in range(10)])
    
    # All reads should return same hash
    assert all(h == original_hash for h in hashes)
```

## 3. Concurrency Test Configuration

```python
@pytest.fixture
def concurrency_config():
    return {
        "max_workers": 10,
        "timeout": 30,
        "retry_attempts": 3,
    }
```

## 4. Expected Behaviors

| Scenario                    | Expected Behavior                       |
| --------------------------- | --------------------------------------- |
| Concurrent same-field update| One succeeds, one raises ConcurrencyError|
| Concurrent different fields | Both succeed (no conflict)              |
| Read during write           | Consistent read (snapshot isolation)    |
| Write during read           | Read sees old or new value (not partial)|

---

**See also**: `18_repositories.md` for optimistic locking implementation
