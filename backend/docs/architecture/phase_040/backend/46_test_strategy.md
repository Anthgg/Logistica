# Phase 040 — Test Strategy

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

219 tests covering unit, integration, and concurrency scenarios.

## 2. Test Distribution

| Category            | Count  | Coverage  |
| ------------------- | ------ | --------- |
| Unit Tests          | 145    | 92%       |
| Integration Tests   | 54     | 85%       |
| Concurrency Tests   | 20     | 100%      |
| **Total**           | **219**| **89%**   |

## 3. Test Structure

```
tests/
├── unit/
│   ├── domain/
│   │   ├── test_enums.py
│   │   ├── test_errors.py
│   │   ├── test_services.py
│   │   ├── test_severity_policy.py
│   │   └── test_transitions.py
│   ├── application/
│   │   ├── test_case_service.py
│   │   ├── test_item_service.py
│   │   └── test_formalization_service.py
│   └── infrastructure/
│       ├── test_repositories.py
│       └── test_pdf_generator.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_external_services.py
└── concurrency/
    ├── test_concurrent_updates.py
    └── test_optimistic_locking.py
```

## 4. Testing Tools

| Tool              | Purpose                              |
| ----------------- | ------------------------------------ |
| `pytest`          | Test framework                       |
| `pytest-asyncio`  | Async test support                   |
| `pytest-cov`      | Coverage reporting                   |
| `httpx`           | HTTP client for API tests            |
| `factory_boy`     | Test data factories                  |
| `faker`           | Fake data generation                 |

## 5. Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/concurrency/ -v
```

## 6. Coverage Targets

| Module                | Target    |
| --------------------- | --------- |
| Domain Layer          | 95%       |
| Application Layer     | 90%       |
| Infrastructure Layer  | 85%       |
| Presentation Layer    | 80%       |
| **Overall**           | **89%**   |

## 7. Test Data Management

```python
# Factory for test cases
class CaseFactory:
    def __init__(self, tenant_id: str = "test-tenant"):
        self.tenant_id = tenant_id
    
    def create(self, **kwargs) -> CaseAggregate:
        return CaseAggregate(
            id=uuid4(),
            tenant_id=self.tenant_id,
            status=kwargs.get("status", CaseStatus.DETECTED),
            severity=kwargs.get("severity", Severity.LOW),
            category=kwargs.get("category", DifferenceCategory.QUANTITY_SHORTAGE),
            ...
        )
```

## 8. CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    pytest tests/ -v --cov=app --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

---

**See also**: `47_unit_tests.md` for unit test details
