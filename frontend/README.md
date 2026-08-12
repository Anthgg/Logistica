# Sistema Logístico con Autenticación Continua

Frontend React de AndesLog Operaciones S.A.C. para la Fase 9B del proyecto
“Modelo de Autenticación Basado en Biometría Facial y Modelado de
Comportamiento de Usuario usando Aprendizaje Profundo para Detección de
Anomalías”.

Esta fase presenta y coordina las decisiones emitidas por el backend de la
Fase 9A. El navegador no calcula identidad, PAD, error conductual, riesgo
combinado, umbrales ni acciones de sesión.

## Alcance de la Fase 9B

- Indicador persistente en todas las rutas privadas.
- Estado de riesgo y nivel de autenticación comunicado por el backend.
- Polling controlado, cancelable y consciente de la visibilidad de la pestaña.
- Evaluación automática solo con IDs confirmados y una combinación nueva.
- Reverificación accesible mediante contraseña actual.
- Restricción visual y guard de operaciones sensibles.
- Manejo central de sesiones restringidas, terminadas y modo degradado.
- Historial administrativo paginado y detalle técnico sanitizado.
- Estado de modelos para `admin` y `supervisor`.
- Integración con `AuthContext` y `ResearchSessionContext`.

No se modifica FastAPI, la base de datos, los modelos de aprendizaje, Docker ni
las migraciones.

## Contrato FastAPI 0.9.1

El frontend usa el contrato 0.9.1 sin adaptadores en el backend:

- todas las rutas salen bajo `/api`, sin barra final;
- todas las solicitudes incluyen cookies y `Accept-Language`;
- el arranque ejecuta, en orden, CSRF, catálogo y usuario actual;
- ninguna consulta protegida se monta antes de terminar ese arranque;
- los `401` concurrentes comparten una única promesa de refresh;
- el catálogo se conserva en memoria por idioma;
- los códigos de estados, prioridades, eventos, recursos, riesgo y acciones
  se conservan para lógica; la interfaz muestra `*_label` o el catálogo;
- envíos consume exclusivamente `{ items, page, page_size, total,
  total_pages }`.

## Estados mostrados

### Niveles de riesgo

| Valor | Etiqueta | Comportamiento |
| --- | --- | --- |
| `low` | Riesgo bajo | Operación normal e indicador discreto |
| `medium` | Riesgo moderado | Aviso no intrusivo y mayor supervisión |
| `high` | Riesgo alto | Banner y reverificación para operaciones sensibles |
| `critical` | Riesgo crítico | Aviso prioritario y reverificación inmediata |
| `unknown` | Riesgo sin determinar | Estado neutral, nunca se interpreta como crítico |

### Niveles de autenticación

| Valor | Significado |
| --- | --- |
| `traditional` | Sesión tradicional |
| `continuously_verified` | Identidad verificada continuamente |
| `verification_required` | Se necesita reverificación |
| `restricted` | Consultas permitidas; operaciones sensibles bloqueadas |
| `terminated` | Sesión finalizada por decisión del backend |

Las acciones `maintain_session`, `increase_monitoring`,
`request_reverification`, `restrict_sensitive_operations` y
`terminate_session` se presentan con lenguaje comprensible. React no las
deduce ni sustituye.

## Arquitectura

```text
src/
├── api/                         # fetch central, CSRF, idioma y contratos
├── components/
│   ├── common/
│   ├── layout/                  # indicador y banners persistentes
│   └── research/
├── contexts/
│   ├── AuthContext.tsx
│   ├── I18nProvider.tsx
│   ├── ResearchSessionContext.tsx
│   └── ContinuousAuthProvider.tsx
├── features/
│   └── continuous-auth/
│       ├── api/
│       ├── components/
│       ├── contexts/
│       ├── hooks/
│       ├── pages/
│       ├── types/
│       └── utils/
├── pages/                       # módulos logísticos existentes
├── research/                    # recolectores separados del riesgo
├── router/
├── test/
└── utils/
```

El `ContinuousAuthProvider` se monta dentro de `ProtectedRoute`, después del
proveedor experimental. Por ello no consulta el estado sin una sesión
autenticada y puede detener inmediatamente cámara, telemetría y colas si el
backend finaliza la sesión.

## Cliente HTTP y seguridad

Todas las funciones de autenticación continua usan el `apiRequest` existente:

- `credentials: "include"` en cada solicitud;
- `GET /api/auth/csrf` y `X-CSRF-Token` para `POST`, `PATCH` y `DELETE`;
- CSRF conservado únicamente en memoria;
- refresh compartido ante `401`;
- `Accept-Language` en todas las solicitudes y lectura de `Content-Language`;
- `AbortSignal`, timeout y errores tipados;
- validación de respuestas `unknown` antes de exponerlas a React.

No se usan `localStorage` ni `sessionStorage` para cookies, tokens, CSRF,
contraseñas, IDs biométricos o telemetría. No se imprimen respuestas sensibles.
Las vistas nunca muestran imágenes, embeddings, plantillas, vectores, pesos,
umbrales, rutas internas ni datos que faciliten evasión.

## Polling

`useContinuousAuthPolling` usa un único `setTimeout` reprogramable:

1. respeta `next_evaluation_after` cuando está presente;
2. usa 10 segundos como intervalo base;
3. duplica el intervalo si no hay sesión experimental;
4. pausa cuando `document.visibilityState === "hidden"`;
5. reanuda al volver a `visible`;
6. evita solicitudes solapadas;
7. cancela solicitudes antiguas con `AbortController`;
8. aplica espera incremental después de errores;
9. se suspende después de tres fallos consecutivos;
10. se detiene al desmontar, cerrar sesión o recibir `terminated`.

El polling solo consulta `GET /continuous-auth/status`. Nunca dispara inferencia
indiscriminadamente.

## Evaluación e integración con el recolector

El recolector continúa siendo responsable de cámara y telemetría. El contexto
experimental expone en memoria:

- `experimentalSessionId`;
- `latestAcceptedFacialCaptureId`;
- `latestBehavioralWindowId`;
- `lastCaptureConfirmedAt`;
- `lastBehaviorBatchConfirmedAt`.

La captura facial utiliza el `id` confirmado por el backend. Un lote conductual
solo habilita `latestBehavioralWindowId` si su respuesta incluye explícitamente
`behavioral_window_id`; el frontend no convierte ni inventa ese identificador.

`POST /continuous-auth/evaluate` se ejecuta únicamente con sesión activa,
intervalo permitido y al menos una fuente confirmada: captura facial o ventana
conductual. La versión 0.9.1 no devuelve `behavioral_window_id` al recibir un
lote, por lo que el frontend nunca lo inventa y puede evaluar con la captura
facial confirmada. El request contiene solo IDs y `evaluation_timestamp`; no
envía ni calcula puntajes.

## Reverificación y operaciones sensibles

El diálogo:

- usa `autocomplete="current-password"`;
- tiene `role="dialog"`, `aria-modal`, trampa de foco, Escape y retorno de foco;
- evita doble envío;
- limpia la contraseña al enviar, cerrar o desmontar;
- usa mensajes sanitizados;
- actualiza el estado después de un éxito.

El guard se aplica a eliminación de clientes y almacenes, movimientos de
inventario, resolución de incidencias, cambios de estado de envíos, gestión de
participantes, retiro de consentimiento y revocación de sesiones. Primero
consulta el estado actual; después deja que el backend vuelva a autorizar la
operación. Un `403` se procesa como estado de seguridad, no como permiso local.

Si se requiere reverificación, la acción no se guarda ni se ejecuta
automáticamente. Después del éxito el usuario debe confirmar otra vez la
operación destructiva visible.

## Sesión restringida, terminada y modo degradado

`restricted` muestra un banner persistente con reverificación, cierre de sesión
y acceso al estado. Las consultas pueden continuar; el backend conserva la
autoridad final.

`terminated` detiene polling, cámara, eventos y colas, limpia CSRF y contexto de
autenticación, y redirige una sola vez a `/login` con el mensaje:
“Tu sesión fue finalizada por seguridad.”

Los fallos de red o de modelos muestran disponibilidad limitada o “Sin
conexión”. No convierten el fallo técnico en riesgo crítico ni afirman que la
identidad falló.

## Rutas

| Ruta | Acceso |
| --- | --- |
| `/security/continuous-auth` | Cualquier usuario autenticado |
| `/admin/continuous-auth/evaluations` | `admin`, `supervisor` |
| `/admin/continuous-auth/evaluations/:evaluationId` | `admin`, `supervisor` |
| `/admin/models/status` | `admin`, `supervisor` |

`RoleRoute` redirige usuarios no autorizados a `/unauthorized` antes de renderizar
el contenido. Dispatcher y warehouse operator no ven accesos administrativos
en el menú.

## Variables

```dotenv
VITE_API_URL=http://localhost:8000/api
VITE_COMPANY_NAME=AndesLog
VITE_APP_NAME=Autenticación Continua
VITE_APP_ENV=development
VITE_CONTINUOUS_AUTH_STATUS_INTERVAL_MS=10000
VITE_CONTINUOUS_AUTH_MAX_FAILURES=3
```

`VITE_API_URL` es la base completa de la API y debe terminar en `/api`, sin
barra final. Los servicios usan rutas como `/auth/me` o `/shipments`; el
cliente rechaza rutas que repitan `/api/api`.

`.env.development` apunta a FastAPI local. `.env.production` apunta al servicio
Cloud Run terminado en `/api`. Vite no contiene un proxy ni una URL de backend
codificada; CORS y cookies deben estar habilitados por el despliegue para los
orígenes autorizados.

## Instalación y comandos

Requiere Node.js 20.19+ o 22.12+.

```bash
cd frontend
npm install
npm run dev
npm run lint
npm run typecheck
npm run test:run
npm run openapi:check
npm run build
```

La aplicación local abre en `http://localhost:5173`.

## Pruebas

Vitest, React Testing Library, user-event y MSW cubren:

- cookies, CSRF, refresh y errores HTTP;
- refresh único para varios `401` concurrentes;
- orden CSRF → catálogo → sesión en el bootstrap;
- catálogo, cambio de idioma, cache y `Content-Language`;
- contrato canónico y paginación de envíos;
- status con y sin autenticación;
- pausa, reanudación, cancelación, no solapamiento y backoff del polling;
- payload de evaluación sin puntajes;
- indicador textual y `aria-live`;
- diálogo y limpieza de contraseña;
- guard seguro, restricted y nueva confirmación;
- terminación y detención del recolector;
- roles y rutas;
- privacidad del recolector y exclusión de texto/contraseñas;
- compilación TypeScript y build Vite.

Los estados simulados se prueban con mocks/MSW. No se modifica PostgreSQL de
producción para provocar riesgo.

## Verificación manual

1. Inicia sesión con una cuenta válida.
2. Abre el dashboard y confirma el indicador del encabezado.
3. Abre **Estado de seguridad**.
4. Inicia una sesión experimental con consentimiento vigente.
5. Espera capturas y lotes confirmados.
6. Confirma que solo se evalúa cuando existe al menos una fuente biométrica o
   conductual confirmada por el backend.
7. Simula `medium` con MSW y comprueba el aviso no intrusivo.
8. Simula `high` y comprueba el banner.
9. Abre la reverificación.
10. Introduce una contraseña incorrecta y revisa el mensaje genérico.
11. Introduce una contraseña correcta y confirma la actualización.
12. Simula `restricted`.
13. Intenta una operación sensible y confirma que no se ejecuta.
14. Reverifica y confirma nuevamente la operación.
15. Simula `terminated`.
16. Comprueba que cámara y telemetría se detienen.
17. Comprueba el retorno a `/login`.
18. Inicia como `admin` o `supervisor`.
19. Abre evaluaciones, aplica filtros y cambia de página.
20. Abre el detalle y verifica que no existe biometría cruda.
21. Abre el estado de modelos.

## Diagnóstico

- **CORS desde localhost:** usa `npm run dev` y abre exactamente
  `http://localhost:5173`; FastAPI debe permitir ese origen y
  `http://localhost:8080`, responder `Access-Control-Allow-Credentials: true` y
  aceptar las cabeceras `X-CSRF-Token`, `Content-Type` y `Accept-Language`.
- **404 en `/continuous-auth/*` o `/models/status`:** la versión desplegada del
  backend no expone todavía los endpoints 9A. El frontend entra en modo
  degradado y no debe simular respuestas.
- **401:** el cliente intenta un refresh compartido; si falla, invalida la
  sesión.
- **403 `SESSION_RESTRICTED`:** se conserva la sesión y se solicita
  reverificación.
- **`SESSION_TERMINATED`:** se detienen los recolectores y se limpia el acceso.
- **Polling suspendido:** usa **Actualizar estado** o una reverificación exitosa
  para reiniciarlo.
- **Sin evaluación automática:** revisa que exista una captura facial aceptada
  o un `behavioral_window_id` real y que `next_evaluation_after` haya vencido.

## Preparación para Fase 9C

La frontera de tipos y validación deja preparado el frontend para ampliar
observabilidad, analítica longitudinal y pruebas de integración con los
contratos definitivos, sin mover al navegador ninguna inferencia ni dato
biométrico sensible.
