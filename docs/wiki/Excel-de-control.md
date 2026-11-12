# Excel de control

`excel/Portafolio_control.xlsx` hace con fórmulas los mismos cálculos que el programa. Sirve para comprobar que el programa calcula bien.

| Hoja | Contenido |
|---|---|
| Instrucciones | Cómo usarlo y reglas de cálculo |
| Resumen | Fecha de corte, indicadores, distribución y tabla por activo |
| Activos | Catálogo (igual al de `activo.py`) y precio de mercado manual |
| Operaciones | Compras y ventas (en orden de fecha) |
| Pagos | Dividendos, intereses y capital |
| Por activo | Cálculo por activo (equivale a la clase `Posicion`) |
| Flujos | Flujos de caja para `TIR.NO.PER` |

Celdas amarillas = datos; grises = fórmulas.

## Comparación automática
```bash
pip install openpyxl
python pruebas/comparar_con_excel.py
```
El script lee los datos del Excel, los carga en el programa con la misma fecha de corte y compara 69 valores (totales y por activo). Diferencia máxima permitida: 1 centavo en valores y 0,0001 puntos porcentuales en tasas.
Se probó con 9 fechas de corte distintas (antes de algunas compras, con títulos vencidos, con y sin precios manuales) y todos los valores coincidieron.
