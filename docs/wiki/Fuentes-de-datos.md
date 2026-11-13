# Fuentes de datos

| Dato | Fuente | Detalle |
|---|---|---|
| Acciones | yfinance (Yahoo Finance) | `ECOPETROL.CL` y `GEB.CL` (Grupo Energía Bogotá), de la Bolsa de Colombia, en COP; `CIB` (Grupo Cibest), `NKE` (Nike) y `NU` (Nu Holdings), de la Bolsa de Nueva York, en USD. Precio de **cierre sin ajustar**, porque los dividendos se registran aparte (el ajustado los contaría dos veces). |
| Dividendos | yfinance (`Ticker.dividends`) | Monto bruto por acción y **fecha ex-dividendo**; Yahoo no trae la fecha de pago. Nu Holdings no paga dividendos. Para algunas acciones de la Bolsa de Colombia Yahoo puede no tener el historial: en ese caso se registran a mano. |
| TRM | datos.gov.co, conjunto `32sa-8pi3` (TRM certificada por la Superintendencia Financiera) | Si falla, respaldo con el dólar de Yahoo `COP=X`. |
| CDT, bonos, TES | Tasa E.A. y vencimiento del título | No cotizan en Yahoo Finance; se valoran con su tasa (ver fórmulas). |
| investing.com | No se usa | Está protegido contra bots (Cloudflare) y sus condiciones de uso prohíben el raspado; un scraper se rompe seguido. |

Al registrar una compra o venta de una acción, el precio se llena solo con el cierre de ese día (o el último
anterior, si fue fin de semana o aún no hay cierre). Se puede cambiar por el precio real de la operación, que
puede ser distinto del cierre. La renta fija no tiene precio de mercado en Yahoo: se escribe el valor invertido por título.

**Dividendos automáticos:** el botón **Traer dividendos (yfinance)** reemplaza los dividendos registrados de cada
acción por los de Yahoo. Cobra un dividendo quien tenía la acción **antes** de la fecha ex-dividendo: si compró ese
mismo día o después, no lo cobra; si vendió antes, tampoco. El pago se registra con la fecha ex-dividendo y el monto
bruto (sin retenciones). Si después se registra otra compra o venta, se vuelve a presionar el botón.
Si Yahoo no tiene dividendos de una acción, se dejan los que estaban registrados.

Una serie (TRM o un ticker) vale, en una fecha, **su último dato con fecha menor o igual**:
los fines de semana y festivos se usa el último cierre, y la TRM del viernes cubre el fin de semana.

## Cómo se actualizan
Pestaña **Valoración** → **Actualizar precios de mercado (yfinance + TRM)**. Pestaña **Dividendos e intereses** → **Traer dividendos (yfinance)**. Todo queda en `datos/mercado.csv` y `datos/portafolio.json`.
