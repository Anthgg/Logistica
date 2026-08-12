# 05. Autenticación y Seguridad en la UI — Proyecto T1

## 1. Integración con `/auth/me` y Contexto de Sesión

Al cargar la aplicación, el `AuthProvider` consultará la sesión actual invocado la API protegida existente:

```text
GET /api/auth/me
Response:
{
  "id": "uuid-user-123",
  "email": "operador@andeslog.pe",
  "full_name": "Juan Pérez",
  "role": "ACT_DES",
  "continuous_auth_status": {
    "score": 0.94,
    "confidence_level": "HIGH",
    "last_evaluation": "2026-07-26T05:00:00Z"
  }
}
```

El estado de confianza biométrica se mostrará en el Header con un indicador de pulso (Verde = Confianza Alta > 0.85, Amarillo = Precaución 0.60-0.84, Rojo = Riesgo < 0.60).

---

## 2. Guardas de Ruta Basadas en Roles (RBAC Guards)

Las rutas de la SPA estarán protegidas por el componente `ProtectedRoute`:

```jsx
<Route 
  path="/logistics/inventory/adjustments" 
  element={
    <ProtectedRoute allowedRoles={['ACT_ADM', 'ACT_GER']}>
      <InventoryAdjustmentsView />
    </ProtectedRoute>
  } 
/>
```

---

## 3. Modal de Re-autenticación Step-Up (`StepUpAuthModal`)

Cuando una acción sensible requiere Step-Up, la UI mostrará una ventana modal bloqueante:
- **Paso 1:** Muestra la acción que se intenta realizar (ej: *"Ajuste manual de inventario de 500 unidades en Almacén Central"*).
- **Paso 2:** Opción de verificación por código OTP enviado al smartphone registrado del usuario O verificación facial rápida (Webcam).
- **Paso 3:** Al superar la prueba, el cliente reintenta automáticamente la petición fallida adjuntando el token de verificación concedido.
