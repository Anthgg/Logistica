# 04 — Ciclo de Vida de StepUpChallenge

## Ciclo de Estados
```mermaid
stateDiagram-v2
    [*] --> PENDING: create_challenge()
    PENDING --> PROCESSING: submit_factor()
    PROCESSING --> PASSED: complete_challenge() [Todos los factores OK]
    PROCESSING --> FAILED: submit_factor() [Fallo biométrico o PAD attack]
    PENDING --> EXPIRED: TTL alcanzado (120s)
    PROCESSING --> LOCKED: Intentos excede MAX_ATTEMPTS (3)
    PASSED --> CONSUMED: Proof consumido
```

## Límites e Intentos
* **TTL por defecto:** 120 segundos.
* **Máximo de intentos:** 3. Superar este límite transiciona el desafío a `LOCKED` y eleva el nivel de riesgo de la sesión.
