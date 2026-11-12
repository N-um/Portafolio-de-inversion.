# Cálculos financieros

Notación: *q* = cantidad, *P* = precio unitario en la moneda del activo, *c* = 0,2 % (comisión),
*TRM(d)* = TRM del día *d* (vale 1 para activos en COP), *t* = tasa E.A. del título,
*V* = fecha de vencimiento, *F* = fecha de corte. Todo resultado queda en pesos (COP).

### Operaciones y pagos

| # | Concepto | Fórmula |
|---|---|---|
| 1 | Monto de una operación | `q × P` |
| 2 | Comisión del bróker | `c × q × P` (c = 0,2 % en compras y en ventas) |
| 3 | Flujo de una compra (COP) | `−(q × P + comisión) × TRM(fecha)` |
| 4 | Flujo de una venta (COP) | `+(q × P − comisión) × TRM(fecha)` |
| 5 | Flujo de un pago (COP) | `+monto × TRM(fecha del pago)` |
| 6 | TRM del día *d* | último valor de la serie TRM con fecha ≤ *d* |

### Totales

| # | Concepto | Fórmula |
|---|---|---|
| 7 | Total invertido | `Σ (q × P + comisión) × TRM(fecha)` de las compras |
| 8 | Ventas netas | `Σ (q × P − comisión) × TRM(fecha)` de las ventas |
| 9 | Comisiones pagadas | `Σ comisión × TRM(fecha)` |
| 10 | Dividendos e intereses | `Σ monto × TRM(fecha)` de pagos tipo Dividendo e Interés |
| 11 | Pagos de capital | `Σ monto` de pagos tipo Capital (dinero que vuelve, no ganancia) |
| 12 | Cantidad actual | `Σ q compras − Σ q ventas` (con fecha ≤ *F*) |

### Valoración a la fecha *F*

| # | Concepto | Fórmula |
|---|---|---|
| 13 | Valor de una acción | `q actual × último cierre (≤ F) × TRM(F)`; sin cierre: último precio de operación |
| 14 | Valor de renta fija vigente | `Σ compras_i · (1+t)^((min(F,V) − d_i)/365) − Σ cobros_j · (1+t)^((min(F,V) − d_j)/365)` |
| 15 | Valor de renta fija vencida (*F* ≥ *V*) | `0` (el capital y los intereses se registran como pagos) |
| 16 | Valor actual del portafolio | `Σ valor de cada activo` |
| 17 | Participación renta fija / variable | `valor del grupo / valor actual` |

En la fórmula 14, *compras* = q × P en COP (sin comisión), *cobros* = ventas, intereses y capital,
y *d* = fecha de cada movimiento. Cada peso invertido crece a la tasa del título y cada peso
cobrado deja de crecer el día en que se cobra. Con esta regla, un CDT al 10 % E.A. sin comisión rinde
exactamente 10 % E.A., y un bono cuyo cupón es igual a la tasa vuelve a valer lo invertido después de
pagarlo. La tasa y el vencimiento se toman de la primera compra del título.

### Resultados

| # | Concepto | Fórmula |
|---|---|---|
| 18 | Ganancia total | `valor actual + ventas netas + dividendos e intereses + capital − total invertido` |
| 19 | Costo de lo que aún se tiene | `q actual × (total invertido / q comprada) − capital` (0 si el título venció) |
| 20 | Ganancia no realizada | `valor actual − costo de lo que aún se tiene` |
| 21 | Ganancia realizada | `ganancia total − ganancia no realizada` |
| 22 | Rentabilidad acumulada | `ganancia total / total invertido` |
| 23 | Rentabilidad E.A. | la tasa *r* que cumple `Σ flujo_k / (1+r)^((d_k − d_0)/365) = 0` con los flujos 3, 4 y 5 más el valor actual en *F* (= `TIR.NO.PER` / `XIRR` de Excel) |
| 24 | Peso de un activo | `valor del activo / valor actual del portafolio` |
| 25 | Días al vencimiento | `max(0, V − F)` |

### Valor diario

| # | Concepto | Fórmula |
|---|---|---|
| 26 | Valor del portafolio el día *d* | fórmulas 13 a 16 con *F* = *d*: cantidades a ese día, último cierre ≤ *d*, `TRM(d)` y renta fija causada hasta *d* |
| 27 | Rango | cada día calendario desde la fecha inicial hasta la final, sin pasar de la fecha de corte |

Lo registrado con fecha posterior a la fecha de corte no se tiene en cuenta en ningún cálculo.
