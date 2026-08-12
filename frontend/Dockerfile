# Multi-stage Dockerfile para el Frontend React de AndesLog
# Stage 1: Build de la aplicación
FROM node:22-alpine AS builder

WORKDIR /app

# Copiar manifiestos de dependencias
COPY package.json package-lock.json ./

# Instalación reproducible limpia mediante lockfile
RUN npm ci

# Copiar código fuente y configuraciones
COPY . .

# Argumentos de compilación opcionales para inyección de versión y ambiente
ARG VITE_APP_ENV=production
ARG VITE_API_URL=https://autenticacion-continua-api-lqar5vfjma-tl.a.run.app/api
ARG VITE_BUILD_SHA=docker-build-sha
ARG VITE_APP_VERSION=1.0.0

ENV VITE_APP_ENV=$VITE_APP_ENV
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BUILD_SHA=$VITE_BUILD_SHA
ENV VITE_APP_VERSION=$VITE_APP_VERSION

# Ejecutar Typecheck, Linter y Build de producción
RUN npm run typecheck && npm run lint && npm run build

# Stage 2: Servidor Web Nginx Ligero de Producción
FROM nginx:1.27-alpine AS runner

# Copiar archivo de configuración Nginx personalizado con SPA routing y headers de seguridad
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar bundle optimizado desde la etapa builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Asignar permisos y ejecutar como usuario no root por seguridad
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /var/log/nginx

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
