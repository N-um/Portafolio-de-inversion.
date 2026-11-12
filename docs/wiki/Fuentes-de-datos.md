# Fuentes de datos

| Dato | Fuente | Detalle |
|---|---|---|
| Acciones | yfinance (Yahoo Finance) | `ECOPETROL.CL` (Bolsa de Colombia, COP), `CIB` (Grupo Cibest, NYSE, USD), `NKE` (Nike, NYSE, USD). Precio de **cierre sin ajustar**, porque los dividendos se registran aparte (el ajustado los contaría dos veces). |
| TRM | datos.gov.co, conjunto `32sa-8pi3` (TRM certificada por la Superintendencia Financiera) | Si falla, respaldo con el dólar de Yahoo `COP=X`. |
| CDT, bonos, TES | Tasa E.A. y vencimiento del título | No cotizan en Yahoo Finance; se valoran con su tasa (ver fórmulas). |
| investing.com | No se usa | Está protegido contra bots (Cloudflare) y sus condiciones de uso prohíben el raspado; un scraper se rompe seguido. |

Una serie (TRM o un ticker) vale, en una fecha, **su último dato con fecha menor o igual**:
los fines de semana y festivos se usa el último cierre, y la TRM del viernes cubre el fin de semana.

## Cómo se actualizan
Pestaña **Valoración** → **Actualizar precios de mercado (yfinance + TRM)**. Descarga desde 10 días antes de la primera operación hasta la fecha de corte, reemplaza los datos descargados antes (también los de PRUEBA) y conserva los precios manuales. Todo queda en `datos/mercado.csv` (columnas fecha, serie, valor, fuente).
