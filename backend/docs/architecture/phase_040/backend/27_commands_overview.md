# Phase 040 — Commands Overview

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

The module implements 4 command types following the CQRS pattern. Commands represent write operations that modify system state.

## 2. Command Types

| Command                    | Description                          | Trigger              |
| -------------------------- | ------------------------------------ | -------------------- |
| `FormalizeCandidates`      | Formalize candidate items            | API / Batch job      |
| `SubmitCase`               | Submit case for review               | API                  |
| `IssueDocument`            | Generate and issue DIF document      | API / Auto           |
| `CloseCase`                | Close resolved case                  | API                  |

## 3. Command Pattern

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Command:
    """Base command class."""
    command_id: str
    timestamp: datetime
    user_id: str
    tenant_id: str

@dataclass
class CommandResult:
    """Base command result."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
```

## 4. Command Bus

```python
class CommandBus:
    """Command dispatcher."""
    
    def __init__(self):
        self.handlers = {}
    
    def register(
        self,
        command_type: type,
        handler: Callable,
    ) -> None:
        """Register command handler."""
        self.handlers[command_type] = handler
    
    async def dispatch(self, command: Command) -> CommandResult:
        """Dispatch command to handler."""
        handler = self.handlers.get(type(command))
        
        if handler is None:
            raise ValueError(f"No handler for {type(command)}")
        
        return await handler(command)
```

## 5. Registration

```python
command_bus = CommandBus()
command_bus.register(FormalizeCandidates, formalize_candidates_handler)
command_bus.register(SubmitCase, submit_case_handler)
command_bus.register(IssueDocument, issue_document_handler)
command_bus.register(CloseCase, close_case_handler)
```

## 6. Idempotency

All commands include `command_id` for idempotent execution:

```python
async def execute_with_idempotency(
    command: Command,
    handler: Callable,
) -> CommandResult:
    """Execute command with idempotency check."""
    existing = await idempotency_store.get(command.command_id)
    
    if existing:
        return existing
    
    result = await handler(command)
    
    await idempotency_store.save(command.command_id, result)
    
    return result
```

---

**See also**: `32_queries_overview.md` for query pattern
