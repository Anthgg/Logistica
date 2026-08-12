# 09 — Redes, Certificados y Dominio de Cookies

## Mapeo de Dominios y Cookies HTTP-Only

```mermaid
graph TD
    User[Navegador del Usuario] --> |HTTPS / Secure Cookies| Frontend[proyecto-t1-web-production]
    User --> |HTTPS / Secure Cookies| API[autenticacion-continua-api]

    subgraph CookieDomain ["Dominio de Cookies Cifradas"]
        CK1[session_token: Secure, HttpOnly, SameSite=Strict]
        CK2[csrf_token: Secure, SameSite=Strict]
    end
```

## Compatibilidad de Cookies
* **`COOKIE_SECURE=true`**: Exigido en `production` y `staging` para requerir canal seguro HTTPS.
* **`SESSION_COOKIE_SAMESITE="strict"`**: Previene ataques CSRF inter-sitio.
