# Phase 040 — API Contract

| Field     | Value                                    |
| --------- | ---------------------------------------- |
| Phase     | 040                                      |
| Module    | Reception Differences                    |
| Version   | 1.0.0                                    |
| Date      | 2026-08-02                               |

## 1. Overview

OpenAPI 3.0 contract for the Reception Differences API.

## 2. Base Information

```yaml
openapi: 3.0.3
info:
  title: Reception Differences API
  description: API for managing reception difference cases
  version: 1.0.0
servers:
  - url: https://api.example.com/api/v1
    description: Production
  - url: https://staging-api.example.com/api/v1
    description: Staging
```

## 3. Security Scheme

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    
  schemas:
    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: object
            timestamp:
              type: string
              format: date-time
            request_id:
              type: string
```

## 4. Idempotency

All POST endpoints support idempotency via `Idempotency-Key` header:

```yaml
parameters:
  - name: Idempotency-Key
    in: header
    required: false
    schema:
      type: string
      format: uuid
    description: Unique key for idempotent request
```

## 5. Rate Limiting

| Endpoint Type        | Rate Limit        |
| -------------------- | ----------------- |
| Read (GET)           | 100 req/min       |
| Write (POST/PUT)     | 50 req/min        |
| Delete               | 20 req/min        |
| Bulk operations      | 10 req/min        |

## 6. Pagination

All list endpoints support:

```yaml
parameters:
  - name: page
    in: query
    schema:
      type: integer
      default: 1
      minimum: 1
  - name: size
    in: query
    schema:
      type: integer
      default: 20
      minimum: 1
      maximum: 100
```

## 7. Filtering

```yaml
parameters:
  - name: status
    in: query
    schema:
      $ref: '#/components/schemas/CaseStatus'
  - name: severity
    in: query
    schema:
      $ref: '#/components/schemas/Severity'
  - name: category
    in: query
    schema:
      $ref: '#/components/schemas/DifferenceCategory'
```

## 8. Error Responses

```yaml
responses:
  400:
    description: Bad request
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/ErrorResponse'
  401:
    description: Unauthorized
  403:
    description: Forbidden
  404:
    description: Not found
  409:
    description: Conflict
  422:
    description: Validation error
  429:
    description: Rate limit exceeded
  500:
    description: Internal server error
```

## 9. Content Types

| Request             | Response            |
| ------------------- | ------------------- |
| `application/json`  | `application/json`  |
| `multipart/form-data`| `application/pdf`  |

---

**See also**: `51_api_endpoints.md` for endpoint reference
