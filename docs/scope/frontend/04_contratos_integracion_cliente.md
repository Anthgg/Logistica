# 04. Contratos de Integración Cliente — API `/api/logistics`

## 1. Cliente HTTP e Interceptores (`apiClient`)

El frontend utilizará una instancia global configurada de `axios` o `fetch` encapsulado que gestionará la seguridad de forma transparente:

```javascript
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api',
  withCredentials: true, // Envía cookies HTTP-only (access_token_cookie) automáticamente
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para Inyectar Header CSRF
apiClient.interceptors.request.use((config) => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
    const csrfToken = getCookie('csrf_access_token');
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }
  }
  return config;
});
```

---

## 2. Interceptor de Respuestas y Re-autenticación (Step-Up)

Cuando una API logística requiere Step-Up o la sesión ha caducado, el interceptor capturará la respuesta antes de enviarla a la vista:

```javascript
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response) {
      const { status, data } = error.response;

      if (status === 401) {
        // Redirigir a login de autenticación continua
        window.location.href = '/login?expired=true';
      } else if (status === 403 && data.code === 'STEP_UP_REQUIRED') {
        // Disparar evento global para abrir el Modal de Re-autenticación (StepUpAuthModal)
        window.dispatchEvent(new CustomEvent('TRIGGER_STEP_UP', { detail: data.details }));
      }
    }
    return Promise.reject(error);
  }
);
```
