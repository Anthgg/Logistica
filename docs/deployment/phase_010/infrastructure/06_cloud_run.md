# 06 — Configuración de Contenedores Cloud Run

## Especificación Técnica de Servicios

```mermaid
graph TD
    subgraph StagingRun ["Cloud Run Staging"]
        STG_API[proyecto-t1-api-staging / 1 vCPU / 1 GiB / Max: 5]
        STG_WEB[proyecto-t1-web-staging / SPA Static]
    end

    subgraph ProdRun ["Cloud Run Production"]
        PROD_API[autenticacion-continua-api / 2 vCPU / 2 GiB / Min: 1 / Max: 20]
        PROD_WEB[proyecto-t1-web-production / SPA Static]
    end
```

## Configuración Producción (`autenticacion-continua-api`)
* **Región:** `southamerica-west1`
* **CPU / RAM:** 2 vCPU / 2 GiB RAM
* **Min Instances:** 1 (Instancia tibia para evitar latencia de cold start)
* **Max Instances:** 20 (Límite presupuestario estricto)
* **Concurrencia:** 80 peticiones simultáneas por instancia
* **Puerto:** 8080
