# Phase 040 — Unit Tests

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

145 unit tests covering domain, application, and infrastructure layers.

## 2. Domain Layer Tests (58 tests)

### 2.1 Enum Tests (8 tests)

```python
def test_case_status_values():
    assert CaseStatus.DETECTED.value == "DETECTED"
    assert CaseStatus.CLOSED.value == "CLOSED"

def test_case_status_is_terminal():
    assert CaseStatus.CLOSED.is_terminal()
    assert CaseStatus.CANCELLED.is_terminal()
    assert not CaseStatus.DRAFT.is_terminal()
```

### 2.2 Error Tests (12 tests)

```python
def test_case_not_found_error():
    error = CaseNotFoundError("case-123")
    assert error.error_code == "CASE_NOT_FOUND"
    assert error.status_code == 404

def test_invalid_transition_error():
    error = InvalidTransitionError(
        current=CaseStatus.CLOSED,
        target=CaseStatus.SUBMITTED,
        allowed=[],
    )
    assert error.status_code == 422
```

### 2.3 Service Tests (25 tests)

```python
def test_canonical_hash_diff():
    case = CaseFactory().create()
    hash1 = canonical_hash_diff(case)
    hash2 = canonical_hash_diff(case)
    assert hash1.value == hash2.value

def test_require_case_transition_valid():
    assert require_case_transition(
        CaseStatus.DRAFT,
        CaseStatus.SUBMITTED,
        ["operator"],
    )

def test_require_case_transition_invalid():
    with pytest.raises(InvalidTransitionError):
        require_case_transition(
            CaseStatus.CLOSED,
            CaseStatus.SUBMITTED,
            ["operator"],
        )

def test_strict_decimal_diff():
    diff, impact = strict_decimal_diff(
        Quantity(Decimal("100")),
        Quantity(Decimal("95")),
        MonetaryAmount(Decimal("25.50")),
    )
    assert diff == Quantity(Decimal("5"))
    assert impact == MonetaryAmount(Decimal("127.50"))
```

### 2.4 Severity Policy Tests (13 tests)

```python
def test_calculate_severity_low():
    severity = calculate_severity(
        MonetaryAmount(Decimal("50")),
        DifferenceCategory.QUANTITY_SHORTAGE,
        1,
    )
    assert severity == Severity.LOW

def test_calculate_severity_critical():
    severity = calculate_severity(
        MonetaryAmount(Decimal("15000")),
        DifferenceCategory.DAMAGED,
        5,
    )
    assert severity == Severity.CRITICAL
```

## 3. Application Layer Tests (52 tests)

### 3.1 Case Service Tests (20 tests)

```python
@pytest.mark.asyncio
async def test_create_case():
    service = CaseService(
        case_repository=MockCaseRepository(),
        ...
    )
    case = await service.create_case(
        CreateCaseDTO(...),
        user_id="user-123",
        tenant_id="tenant-001",
    )
    assert case.status == CaseStatus.DETECTED

@pytest.mark.asyncio
async def test_submit_case():
    case = CaseFactory().create(status=CaseStatus.DRAFT)
    service = CaseService(...)
    result = await service.submit_case(
        case.id,
        user_id="user-123",
        tenant_id="tenant-001",
    )
    assert result.status == CaseStatus.SUBMITTED
```

### 3.2 Item Service Tests (18 tests)

```python
@pytest.mark.asyncio
async def test_add_item():
    service = ItemService(...)
    item = await service.add_item(
        case_id="case-123",
        dto=AddItemDTO(sku="PROD-001", ...),
        user_id="user-123",
    )
    assert item.status == ItemStatus.PENDING

@pytest.mark.asyncio
async def test_formalize_item():
    item = ItemFactory().create(status=ItemStatus.PENDING)
    service = ItemService(...)
    result = await service.formalize_item(
        item.id,
        user_id="user-123",
        tenant_id="tenant-001",
    )
    assert result.status == ItemStatus.FORMALIZED
```

### 3.3 Formalization Service Tests (14 tests)

```python
@pytest.mark.asyncio
async def test_formalize_candidates_success():
    service = FormalizationService(...)
    result = await service.formalize_candidates(
        case_id="case-123",
        candidates=[CandidateItemDTO(...)],
        user_id="user-123",
        tenant_id="tenant-001",
    )
    assert result.formalized == 1
    assert result.rejected == 0

@pytest.mark.asyncio
async def test_formalize_candidates_partial_failure():
    service = FormalizationService(...)
    result = await service.formalize_candidates(
        case_id="case-123",
        candidates=[valid_candidate, invalid_candidate],
        user_id="user-123",
        tenant_id="tenant-001",
    )
    assert result.formalized == 1
    assert result.rejected == 1
```

## 4. Infrastructure Tests (35 tests)

### 4.1 Repository Tests (25 tests)

```python
@pytest.mark.asyncio
async def test_case_repository_get():
    repo = CaseRepositoryImpl(session)
    case = await repo.get(case_id)
    assert case is not None

@pytest.mark.asyncio
async def test_case_repository_tenant_isolation():
    repo = CaseRepositoryImpl(session)
    case = await repo.get(case_id)
    # Should not find case from different tenant
    assert case is None
```

### 4.2 PDF Generator Tests (10 tests)

```python
def test_dif_generator_creates_pdf():
    generator = DIFGenerator()
    case = CaseFactory().create()
    path = generator.generate(case, "test.pdf")
    assert os.path.exists(path)
```

## 5. Mock Objects

```python
class MockCaseRepository:
    def __init__(self):
        self.cases = {}
    
    async def get(self, case_id):
        return self.cases.get(case_id)
    
    async def save(self, case):
        self.cases[case.id] = case
```

---

**See also**: `48_integration_tests.md` for integration tests
