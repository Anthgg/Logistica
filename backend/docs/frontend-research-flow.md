# Contrato frontend: autenticación y recolección para entrenamiento

## Base URL

Producción:

```text
https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app
```

Todas las solicitudes deben usar `credentials: "include"`. Los JWT de acceso y
refresh se entregan en cookies `HttpOnly`; el frontend no debe leerlos ni
guardarlos en `localStorage`.

## Flujo obligatorio

1. `GET /api/auth/csrf`.
2. `POST /api/auth/login` con el valor recibido en `X-CSRF-Token`.
3. `POST /api/research/participants/self-enroll`, sin cuerpo.
4. `POST /api/research/consent` con el UUID del participante devuelto.
5. `POST /api/research/sessions/start`.
6. Enviar capturas y lotes durante la sesión.
7. `POST /api/research/sessions/{session_id}/finish`.

La autoinscripción funciona para cualquier usuario activo, incluido `admin`.
Devuelve `201` al crear el perfil y `200` al reutilizarlo:

```json
{
  "success": true,
  "created": true,
  "participant": {
    "id": "uuid",
    "linked_user_id": "uuid",
    "participant_code": "P-0001",
    "is_active": true
  }
}
```

El frontend debe conservar `participant.id` para consentimiento y sesiones. El
código `P-xxxx` es la identidad seudonimizada que llegará al pipeline; no se
debe sustituir por correo, nombre ni `user.id`.

También puede recuperar el perfil existente con:

```text
GET /api/research/participants/me
```

## Cliente TypeScript mínimo

```ts
const API_URL =
  "https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app";

let csrfToken = "";

async function refreshCsrf(): Promise<void> {
  const response = await fetch(`${API_URL}/api/auth/csrf`, {
    credentials: "include",
  });
  const body = await response.json();
  csrfToken = body.csrf_token;
}

async function api(path: string, init: RequestInit = {}): Promise<Response> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers.set("X-CSRF-Token", csrfToken);
  }
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
}

async function selfEnroll() {
  const response = await api("/api/research/participants/self-enroll", {
    method: "POST",
  });
  if (!response.ok) throw await response.json();
  return response.json();
}

async function acceptConsent(participantId: string) {
  const response = await api("/api/research/consent", {
    method: "POST",
    body: JSON.stringify({
      participant_id: participantId,
      consent_version: "pilot-v1",
      accepted: true,
    }),
  });
  if (!response.ok) throw await response.json();
  return response.json();
}
```

Ante un `401`, el cliente puede ejecutar una sola vez
`POST /api/auth/refresh` con el encabezado CSRF y repetir la solicitud original.
El backend rota los JWT. Si el refresh falla, debe volver a la pantalla de
inicio de sesión.

## Límites

La autoinscripción no acepta datos del participante, no concede consentimiento
y no inicia entrenamiento. Primero deben existir sesiones completas,
consentidas y anotadas. El entrenamiento permanece como proceso backend
controlado y utiliza el participante seudonimizado.

El dominio definitivo del frontend debe configurarse como `FRONTEND_URL` en
Cloud Run. Mientras conserve `http://localhost:5173`, un frontend publicado en
otro dominio será rechazado por CORS.
