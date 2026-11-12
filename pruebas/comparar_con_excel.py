"""Compara los resultados del programa con los del Excel de control.

Uso (desde la carpeta del proyecto):
    python pruebas/comparar_con_excel.py [ruta_del_excel]

Lee los datos de las hojas Activos, Operaciones y Pagos del Excel, los carga en un
Portafolio con la misma fecha de corte, y compara cada indicador con el valor que
calculó el Excel. Necesita openpyxl (pip install openpyxl). El Excel debe haberse
guardado después de abrirlo, para que tenga los valores calculados.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openpyxl import load_workbook  # noqa: E402

from activo import Activo  # noqa: E402
from operacion import Operacion  # noqa: E402
from pago import Pago  # noqa: E402
from portafolio import Portafolio  # noqa: E402

RUTA_EXCEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "excel", "Portafolio_control.xlsx")
TOLERANCIA_COP = 0.01       # un centavo
TOLERANCIA_TASA = 1e-6      # 0,0001 puntos porcentuales


def a_fecha(valor):
    return valor.date() if isinstance(valor, datetime) else valor


def filas(hoja, primera=5):
    for fila in hoja.iter_rows(min_row=primera, values_only=True):
        if fila[0] is not None and fila[1] is not None:
            yield fila


def cargar_desde_excel(libro):
    fecha_corte = a_fecha(libro["Resumen"]["C4"].value)
    portafolio = Portafolio(ruta=None, fecha_corte=fecha_corte)
    for nombre, _t, _ti, _c, _s, precio in [f[:6] for f in filas(libro["Activos"])]:
        if precio not in (None, ""):
            portafolio.precios_manuales[nombre] = float(precio)
    for f in filas(libro["Operaciones"]):
        activo = Activo.buscar(f[1])
        portafolio.agregar_operacion(Operacion(
            a_fecha(f[0]), activo.tipo, f[1], f[2], f[3], f[4], f[5] or 0, f[6] or 0, a_fecha(f[7])))
    for f in filas(libro["Pagos"]):
        portafolio.agregar_pago(Pago(a_fecha(f[0]), f[1], f[2], f[3]))
    return portafolio


def comparar(nombre, programa, excel, es_tasa=False):
    if excel == "N/A":
        excel = None
    if programa is None or excel is None:
        ok = programa is None and excel is None
    else:
        ok = abs(programa - excel) <= (TOLERANCIA_TASA if es_tasa else TOLERANCIA_COP)
    fmt = (lambda x: "N/A" if x is None else f"{x * 100:,.6f}%") if es_tasa else \
          (lambda x: "N/A" if x is None else f"{x:,.2f}")
    print(f"  {'OK ' if ok else 'XX '} {nombre:<32} programa={fmt(programa):>20}   excel={fmt(excel):>20}")
    return ok


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else RUTA_EXCEL
    valores = load_workbook(ruta, data_only=True)
    if valores["Resumen"]["C7"].value is None:
        sys.exit("El Excel no tiene valores calculados: ábralo en Excel, guárdelo y vuelva a intentar.")

    portafolio = cargar_desde_excel(valores)
    r = portafolio.resumen()
    hoja = valores["Resumen"]
    print(f"Fecha de corte: {portafolio.fecha_corte}\n\nPortafolio")
    resultados = [
        comparar("Total invertido", r["invertido"], hoja["C7"].value),
        comparar("Ventas netas", r["ventas"], hoja["C8"].value),
        comparar("Dividendos e intereses", r["ingresos"], hoja["C9"].value),
        comparar("Pagos de capital", r["capital"], hoja["C10"].value),
        comparar("Comisiones", r["comisiones"], hoja["C11"].value),
        comparar("Valor actual", r["valor_actual"], hoja["C12"].value),
        comparar("Ganancia total", r["ganancia"], hoja["C13"].value),
        comparar("Ganancia no realizada", r["no_realizada"], hoja["C14"].value),
        comparar("Ganancia realizada", r["realizada"], hoja["C15"].value),
        comparar("Rentabilidad acumulada", r["rent_acumulada"], hoja["C16"].value, True),
        comparar("Rentabilidad E.A.", r["rent_ea"], hoja["C17"].value, True),
        comparar("Renta fija", r["renta_fija"], hoja["C20"].value),
        comparar("Renta variable", r["renta_variable"], hoja["C21"].value),
    ]

    por_activo = valores["Por activo"]
    for fila in por_activo.iter_rows(min_row=5, max_row=14, values_only=True):
        nombre = fila[0]
        if not nombre or nombre not in r["por_activo"]:
            continue
        a = r["por_activo"][nombre]
        print(f"\n{nombre}")
        resultados += [
            comparar("Cantidad", a["cantidad"], fila[3]),
            comparar("Total invertido", a["compras"], fila[4]),
            comparar("Dividendos / intereses", a["pagos"], fila[7]),
            comparar("Valor actual", a["valor"], fila[12]),
            comparar("Ganancia", a["ganancia"], fila[16]),
            comparar("Rentabilidad acumulada", a["rent"], fila[18], True),
            comparar("Rentabilidad E.A.", a["rent_ea"], fila[19], True),
            comparar("Peso", a["peso"], fila[20], True),
        ]

    print(f"\n{sum(resultados)} de {len(resultados)} valores coinciden.")
    sys.exit(0 if all(resultados) else 1)


if __name__ == "__main__":
    main()
