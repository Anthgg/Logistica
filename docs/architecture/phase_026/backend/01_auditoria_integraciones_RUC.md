# 01 — Auditoría de Integraciones Previas y Deslinde Técnico

## 1. Evaluación de Componentes Existentes (`PeruvianRucValidator`)

En la Fase 025 se implementó la clase `PeruvianRucValidator` en `app/modules/logistics/partners/ruc_validator.py`. Tras la auditoría de arquitectura, este componente ha sido clasificado oficialmente como **REUTILIZABLE**.

```python
class PeruvianRucValidator:
    RUC_REGEX = re.compile(r"^(10|15|16|17|20)\d{9}$")
    WEIGHTS = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

    @classmethod
    def validate(cls, ruc: str) -> bool:
        clean_ruc = cls.normalize(ruc)
        if not cls.RUC_REGEX.match(clean_ruc):
            return False
        
        digits = [int(d) for d in clean_ruc]
        checksum = sum(d * w for d, w in zip(digits[:10], cls.WEIGHTS))
        remainder = checksum % 11
        expected_check = 11 - remainder
        if expected_check == 10:
            expected_check = 0
        elif expected_check == 11:
            expected_check = 1

        return digits[10] == expected_check
```

### Clasificación de Prefijos RUC en Perú:
- **10**: Persona Natural con Negocio (DNI + dígito verificador).
- **15 / 16 / 17**: Personas Naturales no domiciliadas o registros especiales.
- **20**: Persona Jurídica (Empresas SAC, SA, SRL, EIRL, Entidades Públicas).

---

## 2. Deslinde Explícito de Web Scraping y Resolución de CAPTCHAs

Queda **estrictamente prohibida** cualquier técnica de automatización de navegadores (*Puppeteer*, *Selenium*, *Playwright*), resolución de CAPTCHA (*2Captcha*, *AntiCaptcha*, redes neuronales OCR local) o raspado web (*scraping*) sobre la plataforma interactiva de Consulta RUC de SUNAT (`e-consultaruc.sunat.gob.pe`).

### Razones Técnicas y Legales de la Prohibición:
1. **Fragilidad de Integración**: Modificaciones continuas en la estructura DOM HTML y en el desafio CAPTCHA imponen mantenimiento reactivo constante y fallos en entornos de producción.
2. **Bloqueo IP y Denegación de Servicio**: La infraestructura de SUNAT bloquea rangos de IP de proveedores cloud (GCP, AWS, Azure) que emiten peticiones automatizadas recurrentes.
3. **Implicancias de Cumplimiento Legal**: El scraping de portales con términos de servicio que prohíben accesos automatizados expone a la organización a contingencias legales y sanciones administrativas.
4. **Disponibilidad Inestable**: El servicio web interactivo de SUNAT sufre interrupciones de alta concurrencia durante cierres tributarios, comprometiendo la latencia del ERP.

---

## 3. Fuentes Oficiales Adoptadas

Para garantizar alta disponibilidad, resiliencia y conformidad legal, la Fase 026 adopta dos canales oficiales de datos:
1. **Padrón Reducido SUNAT (Masivo)**: Descarga periódica versionada de los archivos ZIP publicados por SUNAT (`padron_reducido_ruc.zip`).
2. **Proveedores de Enriquecimiento Autorizados (APIs REST)**: Interfaces HTTP/TLS contra proveedores homologados bajo contrato de nivel de servicio (SLA) para consultas puntuales en tiempo real.
