# Phase 040 — Queries Overview

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The module implements 2 query types following the CQRS pattern. Queries represent read-only operations.

## 2. Query Types

| Query              | Description                          | Returns           |
| ------------------ | ------------------------------------ | ----------------- |
| `GetCase`          | Get single case by ID                | CaseAggregate     |
| `ListCases`        | List cases with filters/pagination   | List[CaseAggregate] |

## 3. Query Pattern

```python
@dataclass
class Query:
    """Base query class."""
    query_id: str
    tenant_id: str

@dataclass
class QueryResult:
    """Base query result."""
    data: Any
    total: Optional[int] = None
```

## 4. Query Bus

```python
class QueryBus:
    """Query dispatcher."""
    
    def __init__(self):
        self.handlers = {}
    
    def register(
        self,
        query_type: type,
        handler: Callable,
    ) -> None:
        """Register query handler."""
        self.handlers[query_type] = handler
    
    async def dispatch(self, query: Query) -> QueryResult:
        """Dispatch query to handler."""
        handler = self.handlers.get(type(query))
        
        if handler is None:
            raise ValueError(f"No handler for {type(query)}")
        
        return await handler(query)
```

## 5. Registration

```python
query_bus = QueryBus()
query_bus.register(GetCase, get_case_handler)
query_bus.register(ListCases, list_cases_handler)
```

## 6. Caching

| Query     | Cache Strategy        | TTL      |
| --------- | --------------------- | -------- |
| `GetCase` | Read-through          | 5 min    |
| `ListCases`| Cache-aside          | 1 min    |

---

**See also**: `33_get_case.md`, `34_list_cases.md` for query details
