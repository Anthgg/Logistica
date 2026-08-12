# Phase 040 — Integration Tests

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

54 integration tests covering API endpoints, database operations, and external services.

## 2. API Endpoint Tests (30 tests)

### 2.1 Case Endpoints (12 tests)

```python
@pytest.mark.asyncio
async def test_create_case_api():
    async with httpx.AsyncClient(app=app) as client:
        response = await client.post(
            "/api/v1/reception-differences/cases",
            json={
                "reception_id": "REC-001",
                "category": "DAMAGED",
                "description": "Test case",
                "items": [
                    {
                        "sku": "PROD-001",
                        "item_type": "PRODUCT",
                        "expected_qty": "100.000",
                        "received_qty": "95.000",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "DETECTED"

@pytest.mark.asyncio
async def test_list_cases_api():
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get(
            "/api/v1/reception-differences/cases",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "items" in response.json()

@pytest.mark.asyncio
async def test_submit_case_api():
    async with httpx.AsyncClient(app=app) as client:
        response = await client.post(
            f"/api/v1/reception-differences/cases/{case_id}/submit",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "SUBMITTED"
```

### 2.2 Item Endpoints (8 tests)

```python
@pytest.mark.asyncio
async def test_add_item_api():
    async with httpx.AsyncClient(app=app) as client:
        response = await client.post(
            f"/api/v1/reception-differences/cases/{case_id}/items",
            json={
                "sku": "PROD-002",
                "item_type": "PRODUCT",
                "expected_qty": "50.000",
                "received_qty": "48.000",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

@pytest.mark.asyncio
async def test_formalize_item_api():
    async with httpx.AsyncClient(app=app) as client:
        response = await client.post(
            f"/api/v1/reception-differences/cases/{case_id}/items/{item_id}/formalize",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
```

### 2.3 Error Handling Tests (10 tests)

```python
@pytest.mark.asyncio
async def test_case_not_found_api():
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get(
            "/api/v1/reception-differences/cases/nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_unauthorized_api():
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get(
            "/api/v1/reception-differences/cases",
        )
        assert response.status_code == 401
```

## 3. Database Tests (15 tests)

```python
@pytest.mark.asyncio
async def test_case_crud():
    # Create
    case = CaseFactory().create()
    await case_repository.save(case)
    
    # Read
    fetched = await case_repository.get(case.id)
    assert fetched is not None
    assert fetched.id == case.id
    
    # Update
    case.status = CaseStatus.SUBMITTED
    await case_repository.save(case)
    
    updated = await case_repository.get(case.id)
    assert updated.status == CaseStatus.SUBMITTED
    
    # Delete
    await case_repository.delete(case.id)
    deleted = await case_repository.get(case.id)
    assert deleted is None

@pytest.mark.asyncio
async def test_tenant_isolation():
    case_tenant1 = CaseFactory(tenant_id="tenant-1").create()
    case_tenant2 = CaseFactory(tenant_id="tenant-2").create()
    
    await case_repository.save(case_tenant1)
    await case_repository.save(case_tenant2)
    
    # Tenant 1 should only see their cases
    cases_tenant1 = await case_repository.list(tenant_id="tenant-1")
    assert len(cases_tenant1) == 1
    assert cases_tenant1[0].tenant_id == "tenant-1"
```

## 4. External Service Tests (9 tests)

```python
@pytest.mark.asyncio
async def test_notification_service():
    service = NotificationService(...)
    await service.notify_case_submitted(case)
    # Verify notification was sent
    assert notification_sent == True

@pytest.mark.asyncio
async def test_pdf_generation():
    generator = DIFGenerator()
    path = generator.generate(case, "test.pdf")
    assert os.path.exists(path)
```

## 5. Test Fixtures

```python
@pytest.fixture
async def test_case():
    case = CaseFactory().create()
    await case_repository.save(case)
    return case

@pytest.fixture
async def test_token():
    return create_test_token(user_id="user-123", tenant_id="tenant-001")
```

---

**See also**: `49_concurrency_tests.md` for concurrency tests
