# Inventario de Dependencias y Versiones · Fase 001

## 1. Backend (`Anthgg/Logistica`)

- **Runtime:** Python 3.11.15 (Linux Debian Bookworm container)
- **Framework Principal:** FastAPI 0.115.6 / Starlette 0.41.3
- **ASGI Server:** Uvicorn 0.34.0 (con standard extras)
- **ORM & BD:** SQLAlchemy 2.0.36, psycopg 3.2.4 (psycopg-binary, psycopg-pool)
- **Migraciones:** Alembic 1.14.1
- **Validación:** Pydantic 2.10.4, pydantic-settings 2.7.0, email-validator 2.2.0
- **Seguridad & Criptografía:** cryptography 44.0.0, argon2-cffi 23.1.0, PyJWT 2.10.1, bcrypt 4.2.1, passlib 1.7.4
- **Testing:** pytest 9.1.1, pytest-asyncio 1.4.0, anyio 4.14.2, httpx 0.28.1

---

## 2. Frontend (`Anthgg/LogisticaF`)

- **Runtime:** Node.js v20+ / npm
- **Framework & UI:** React 19.0.0, React DOM 19.0.0
- **Lenguaje & Tipado:** TypeScript 5.7.3
- **Bundler & Dev Server:** Vite 6.0.7, @vitejs/plugin-react 4.3.4
- **Routing:** React Router DOM 7.1.1
- **State Management:** Zustand 5.0.3
- **Icons & UI Utilities:** Lucide React 0.469.0, clsx 2.1.1, tailwind-merge 2.6.0
- **Testing & Quality:** Vitest 2.1.8, @testing-library/react 16.1.0, jsdom 25.0.1, oxlint 0.15.6

---

## 3. Estado de Vulnerabilidades y Licencias

- No se detectaron vulnerabilidades críticas ni dependencias obsoletas que afecten la seguridad de la Fase 001.
- Licenciamiento: Compatible 100% con proyectos de código abierto (MIT / Apache 2.0 / BSD-3).
