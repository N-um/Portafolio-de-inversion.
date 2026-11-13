# Instalación y uso

1. Instalar Python 3.10 o superior (en Windows y macOS ya incluye Tkinter; en Linux: `sudo apt install python3-tk`).
2. Clonar el repositorio, entrar a la carpeta y ejecutar `pip install -r requirements.txt`.
3. Ejecutar `python main.py`.
4. Primer uso: pestaña **Valoración** → **Actualizar precios de mercado (yfinance + TRM)**. Hasta hacerlo, el encabezado muestra "⚠ precios de PRUEBA".

## Pestañas
- **Resumen:** total invertido, valor actual, ganancia, rentabilidad acumulada y E.A., comisiones, distribución renta fija / variable y tabla por activo.
- **Operaciones:** compras y ventas. El precio va en la moneda del activo (USD para Nike y Grupo Cibest). La comisión del bróker (0,2 %) se calcula sola. Para acciones, el precio se llena solo con el cierre de ese día (se puede cambiar por el precio real de la compra). En la compra de renta fija se escribe la tasa E.A. (en %) y el vencimiento (AAAA-MM-DD).
- **Dividendos e intereses:** dividendos (acciones), intereses y pagos de capital (renta fija), en la moneda del activo. **Traer dividendos (yfinance)** calcula los dividendos de las acciones solo: acciones que se tenían antes de la fecha ex-dividendo × dividendo por acción. **Traer dividendos (yfinance)** calcula los dividendos de las acciones solo: acciones que se tenían antes de la fecha ex-dividendo × dividendo por acción.
- **Valoración:** descarga de precios y TRM; precio manual para una acción (vale desde la fecha de corte); valor de cada activo.
- **Valor diario:** escribir *Desde* y *Hasta*, presionar **Calcular**: gráfico y tabla con el valor del portafolio cada día; **Exportar CSV**.

## Compras antiguas
Se pueden registrar operaciones de cualquier fecha. Si es una acción en dólares sin TRM de ese día, el programa ofrece descargar la TRM y los precios desde esa fecha. Luego **Traer dividendos (yfinance)** calcula los dividendos desde esa compra.

## Reglas que valida el programa
- No se puede vender más unidades de las que se tienen en esa fecha.
- La compra de renta fija exige tasa y un vencimiento posterior a la fecha de compra.
- Las acciones solo pagan dividendos; la renta fija paga intereses o capital.
- Un pago no puede ser anterior a la primera compra del activo.
- Una operación o pago en dólares necesita la TRM de esa fecha.
- El precio manual es solo para acciones (la renta fija se valora por tasa).
- Cantidades y precios mayores que cero.

## Fecha de corte
Todo se valora a la fecha de corte (por defecto, hoy). Para valorar a otra fecha:
`python main.py --fecha-corte 2026-11-11`. Lo registrado después de esa fecha no se tiene en cuenta.
