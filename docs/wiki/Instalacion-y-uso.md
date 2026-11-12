# Instalación y uso

1. Instalar Python 3.10 o superior (en Windows y macOS ya incluye Tkinter; en Linux: `sudo apt install python3-tk`).
2. Clonar el repositorio y entrar a la carpeta.
3. Ejecutar `python main.py`.

## Pestañas
- **Resumen:** total invertido, valor actual, ganancia, rentabilidad acumulada y E.A., comisiones, distribución renta fija / variable y tabla por activo.
- **Operaciones:** registrar compras y ventas. En la compra de renta fija se escribe la tasa E.A. (en %) y el vencimiento (AAAA-MM-DD).
- **Dividendos e intereses:** registrar dividendos (acciones), intereses y pagos de capital (renta fija).
- **Valoración:** escribir el precio de mercado de un activo o volver a la valoración automática.

## Reglas que valida el programa
- No se puede vender más unidades de las que se tienen en esa fecha.
- La compra de renta fija exige tasa y un vencimiento posterior a la fecha de compra.
- Las acciones solo pagan dividendos; la renta fija paga intereses o capital.
- Un pago no puede ser anterior a la primera compra del activo.
- Cantidades y precios mayores que cero; comisiones no negativas.

## Fecha de corte
Todo se valora a la fecha de corte (por defecto, hoy). Para valorar a otra fecha:
`python main.py --fecha-corte 2026-11-11`. Lo registrado después de esa fecha no se tiene en cuenta.
