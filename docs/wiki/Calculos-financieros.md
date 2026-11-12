# Cálculos financieros

Todas las cifras en pesos colombianos (COP). La base de días es 365, igual que `TIR.NO.PER` de Excel.

| Concepto | Fórmula |
|---|---|
| Flujo de una compra | −(cantidad × precio + comisión) |
| Flujo de una venta | +(cantidad × precio − comisión) |
| Total invertido | Σ (cantidad × precio + comisión) de las compras |
| Ventas netas | Σ (cantidad × precio − comisión) de las ventas |
| Valor de una acción | precio manual × cantidad, o último precio de operación × cantidad |
| Valor de renta fija | Σ compras·(1+t)^(d/365) − Σ (ventas, intereses, capital)·(1+t)^(d/365); 0 si ya venció |
| Ganancia total | valor actual + ventas netas + dividendos e intereses + capital − total invertido |
| Costo de lo que aún se tiene | cantidad actual × (total invertido / cantidad comprada) − capital devuelto |
| Ganancia no realizada | valor actual − costo de lo que aún se tiene |
| Ganancia realizada | ganancia total − ganancia no realizada |
| Rentabilidad acumulada | ganancia total / total invertido |
| Rentabilidad E.A. | tasa *r* que hace Σ flujo / (1+r)^(días/365) = 0 (incluye el valor actual como último flujo) |

**t** = tasa E.A. del título (se toma de su primera compra) y **d** = días desde el movimiento hasta la fecha de corte (sin pasar del vencimiento).

## Por qué la renta fija se valora así
Si un CDT de tasa 10 % E.A. se valora con esta regla, su rentabilidad E.A. calculada da exactamente 10 %. Si un bono paga un cupón igual a su tasa, después del pago vuelve a valer lo invertido. Así, el valor no se "infla" ni se descuenta dos veces lo que ya se cobró.

## Ejemplo verificable a mano
Compra de 100 acciones a $2.000 con comisión de $600, dividendo de $10.000 y precio actual de $2.200:
- Total invertido = 200.600
- Valor actual = 220.000
- Ganancia = 220.000 + 10.000 − 200.600 = 29.400
- Rentabilidad acumulada = 29.400 / 200.600 = 14,66 %
