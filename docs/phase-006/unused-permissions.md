# Permisos sin uso aparente

## Qué significa «usado»

Un permiso está en uso si alguna de estas cosas es cierta:

- lo exige un guard: `require_permission`, `require_capability`;
- lo consulta el código: `has_permission`, `has_any_permission`;
- lo concede algún rol en la matriz.

La auditoría inicial de F006 miró solo `require_permission` y contó **262 permisos sin
uso aparente**. Con las cinco vías reales quedan **11**. Los 251 restantes siempre
estuvieron vivos; el detector miraba por una rendija.

Ese mismo sesgo tuvo consecuencias reales: dos permisos consultados con
`has_permission` no existían en el catálogo, así que la comprobación devolvía siempre
`False` y la capacidad —ver datos sensibles en documentos de entrega y transporte— era
inalcanzable para cualquier rol. Fallaba cerrado, que es lo correcto, pero en silencio.

## Clasificación actual

| Estado | Cantidad |
|---|---:|
| `ACTIVE_USED` | 332 |
| `ACTIVE_ASSIGNED` | 212 |
| `ORPHAN_CANDIDATE` | 11 |

## Los 11 candidatos

```
logistics.deliveries.manual_close          critical
logistics.documents.download_bulk          high
logistics.notifications.configure          medium
logistics.proof_of_delivery.invalidate     critical
logistics.proof_of_download.download       low
logistics.reports.export_sensitive         critical
logistics.returns.close                    high
logistics.returns.create                   medium
logistics.returns.receive                  medium
logistics.routes.override                  critical
logistics.trips.close                      critical
```

Corresponden a funciones que aún no existen: devoluciones, viajes, prueba de entrega,
exportaciones masivas. **No se borran.** Un permiso declarado sin implementación es una
intención registrada; borrarlo pierde esa información y no gana nada, porque un permiso
que nadie tiene no autoriza nada.

`logistics.proof_of_download.download` parece una errata de `proof_of_delivery`. Se deja
como está: el código es un identificador estable y renombrarlo rompería cualquier
asignación que lo use. Si la función se implementa, el código correcto se declara nuevo
y este se deprecia.

## Lo que no se hizo

No hay borrado automático de permisos sin uso. Un catálogo que se poda solo acaba
eliminando la capacidad que alguien iba a implementar la semana siguiente.
