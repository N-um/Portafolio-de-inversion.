# Seguimiento de portafolio de inversión

Programa en Python con interfaz gráfica (Tkinter) para registrar y evaluar un portafolio de
**renta variable** (acciones) y **renta fija** (CDT, bonos y TES). Calcula la rentabilidad
acumulada y la **rentabilidad efectiva anual (E.A.)** teniendo en cuenta comisiones,
dividendos, intereses, pagos de capital y la valoración de cada activo.

Los resultados se pueden comprobar contra el **Excel de control** (`excel/Portafolio_control.xlsx`),
que hace los mismos cálculos con fórmulas.

![Pantalla de resumen](docs/img/interfaz_resumen.png)

## Qué hace

| Requisito | Dónde |
|---|---|
| Registrar compras y ventas (fecha, cantidad, precio, comisión) de acciones, CDT, bonos y TES | Pestaña **Operaciones** |
| Registrar dividendos, intereses y pagos de capital | Pestaña **Dividendos e intereses** |
| Actualizar la valoración (precio de mercado o tasa, plazo y vencimiento del título) | Pestaña **Valoración** |
| Total invertido, valor actual, ganancia, comisiones, rentabilidad acumulada y E.A. | Pestaña **Resumen** |
| Distribución renta fija / renta variable y por activo | Pestaña **Resumen** |

## Cómo ejecutarlo

Requiere Python 3.10 o superior. La interfaz solo usa la librería estándar.

```bash
python main.py                            # valora a la fecha de hoy
python main.py --fecha-corte 2026-11-11   # valora a una fecha fija
```

Los datos se guardan solos en `datos/portafolio.json`, que ya trae un portafolio de ejemplo.

## Cómo se calcula

- **Flujo de caja:** compra = −(cantidad × precio + comisión); venta = +(cantidad × precio − comisión); dividendos, intereses y capital = +monto.
- **Valor de una acción:** precio de mercado manual × cantidad; si no hay precio manual, se usa el último precio de operación.
- **Valor de renta fija:** cada peso invertido crece a la tasa E.A. del título hasta la fecha de corte, y cada peso recibido deja de crecer desde el día en que se recibió:
  `Σ compras·(1+t)^(días/365) − Σ cobros·(1+t)^(días/365)`. Después del vencimiento vale 0.
- **Ganancia total** = valor actual + ventas netas + dividendos e intereses + capital recibido − total invertido.
- **Rentabilidad acumulada** = ganancia total / total invertido.
- **Rentabilidad E.A.** = TIR no periódica (la función `TIR.NO.PER` / `XIRR` de Excel) de todos los flujos más el valor actual a la fecha de corte.

El detalle está en la [wiki](../../wiki) (copia en `docs/wiki/`).

## Comprobar contra el Excel

```bash
pip install openpyxl
python pruebas/comparar_con_excel.py                       # compara 69 valores, uno por uno
python -m unittest discover -s pruebas -p "pruebas_*.py"   # casos verificables a mano
```

## Estructura (una clase por archivo)

| Archivo | Clase | Responsabilidad |
|---|---|---|
| `main.py` | — | Archivo principal: carga los datos y abre la interfaz |
| `Interfaz.py` | `Interfaz` | Ventana con las 4 pestañas |
| `portafolio.py` | `Portafolio` | Guarda operaciones, pagos y precios; valida; arma el resumen |
| `posicion.py` | `Posicion` | Resultados de un activo a la fecha de corte |
| `rentabilidad.py` | `Rentabilidad` | Rentabilidad acumulada y E.A. (TIR) |
| `activo.py` | `Activo` | Catálogo de instrumentos |
| `operacion.py` | `Operacion` | Una compra o venta |
| `pago.py` | `Pago` | Un dividendo, interés o pago de capital |

![Diagrama UML](docs/img/uml_clases.png)

## Equipo

Proyecto de clase. Ramas: `main`, `David` (interfaz), `Cris`, `Sebas` (modelo de cálculo, Excel de control y documentación).
