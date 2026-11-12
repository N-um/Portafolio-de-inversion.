# Excel de control

`excel/Portafolio_control.xlsx` hace con fórmulas los mismos cálculos que el programa, para comprobar que el programa calcula bien.

| Hoja | Contenido |
|---|---|
| Instrucciones | Cómo usarlo y reglas de cálculo |
| Resumen | Fecha de corte, comisión del bróker (0,2 %), TRM, indicadores, distribución y tabla por activo |
| Activos | Catálogo (igual al de `activo.py`): ticker de Yahoo y moneda |
| Operaciones | Compras y ventas (en orden de fecha); TRM, comisión y flujo en COP calculados |
| Pagos | Dividendos, intereses y capital; monto en COP calculado |
| Mercado | Cierres de yfinance y TRM (una fila por serie y fecha) |
| Por activo | Cálculo por activo (equivale a la clase `Posicion`) |
| Flujos | Flujos de caja para `TIR.NO.PER` |
| Valor diario | Valor del portafolio cada día entre *Desde* y *Hasta* (hasta 731 días) |

Celdas amarillas = datos; grises = fórmulas.

## Comparación automática
```bash
python pruebas/llenar_excel.py        # copia los datos del programa al Excel
# abrir el Excel y guardarlo
python pruebas/comparar_con_excel.py  # compara totales, activos y cada día
```
Diferencia máxima permitida: 1 centavo en pesos y 0,0001 puntos en tasas. Con los datos de ejemplo coinciden 4.096 de 4.096 valores.
Se probó también con fechas de corte en 2023, 2025, 2027 y 2031, rangos de dos años, precios manuales y títulos vencidos.
