"""Compara los resultados del programa con los del Excel de control.

Uso (desde la carpeta del proyecto):
    python pruebas/comparar_con_excel.py [ruta_del_excel]

Lee los datos de las hojas Operaciones, Pagos y Mercado del Excel, los carga en un
Portafolio con la misma fecha de corte, y compara cada indicador, cada activo y cada día
de la hoja "Valor diario" con lo que calculó el Excel. Necesita openpyxl.
El Excel debe haberse abierto y guardado (para que tenga los valores calculados).
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openpyxl import load_workbook  # noqa: E402

from activo import Activo  # noqa: E402
from mercado import Mercado  # noqa: E402
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
    resumen = libro["Resumen"]
    if abs(resumen["C5"].value - Operacion.TASA_COMISION) > 1e-12:
        sys.exit(f"La comisión del Excel ({resumen['C5'].value}) no es la del programa ({Operacion.TASA_COMISION}).")
    mercado = Mercado()
    for f in filas(libro["Mercado"]):
        mercado.agregar(f[1], a_fecha(f[0]), f[2], f[3])
    portafolio = Portafolio(fecha_corte=a_fecha(resumen["C4"].value), mercado=mercado)
    for f in filas(libro["Operaciones"]):
        activo = Activo.buscar(f[1])
        portafolio.agregar_operacion(Operacion(a_fecha(f[0]), activo.tipo, f[1], f[2], f[3], f[4],
                                               f[5] or 0, a_fecha(f[6])))
    for f in filas(libro["Pagos"]):
        portafolio.agregar_pago(Pago(a_fecha(f[0]), f[1], f[2], f[3]))
    return portafolio


class Comparador:
    def __init__(self):
        self.total = 0
        self.fallas = 0

    def __call__(self, nombre, programa, excel, es_tasa=False, mostrar=True):
        if excel in ("N/A", ""):
            excel = None
        if programa is None or excel is None:
            ok = programa is None and excel is None
        else:
            ok = abs(programa - excel) <= (TOLERANCIA_TASA if es_tasa else TOLERANCIA_COP)
        self.total += 1
        self.fallas += 0 if ok else 1
        if mostrar or not ok:
            fmt = (lambda x: "N/A" if x is None else f"{x * 100:,.6f}%") if es_tasa else \
                  (lambda x: "N/A" if x is None else f"{x:,.2f}")
            print(f"  {'OK ' if ok else 'XX '} {nombre:<34} programa={fmt(programa):>20}   excel={fmt(excel):>20}")
        return ok


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else RUTA_EXCEL
    valores = load_workbook(ruta, data_only=True)
    hoja = valores["Resumen"]
    if hoja["C10"].value is None:
        sys.exit("El Excel no tiene valores calculados: ábralo en Excel, guárdelo y vuelva a intentar.")
    celda = {str(f[1]).strip(): f[2] for f in hoja.iter_rows(min_row=4, max_row=30, values_only=True) if f[1]}

    portafolio = cargar_desde_excel(valores)
    r = portafolio.resumen()
    comparar = Comparador()
    print(f"Fecha de corte: {portafolio.fecha_corte}   Comisión: {Operacion.TASA_COMISION:.2%}\n\nPortafolio")
    comparar("TRM a la fecha de corte", r["trm"], celda["TRM a la fecha de corte"])
    for clave, etiqueta in (("invertido", "Total invertido"), ("ventas", "Ventas netas recibidas"),
                            ("ingresos", "Dividendos e intereses"), ("capital", "Pagos de capital"),
                            ("comisiones", "Comisiones pagadas"), ("valor_actual", "Valor actual del portafolio"),
                            ("ganancia", "Ganancia / pérdida total"), ("no_realizada", "Ganancia no realizada"),
                            ("realizada", "Ganancia realizada"), ("renta_fija", "Renta fija"),
                            ("renta_variable", "Renta variable")):
        comparar(etiqueta, r[clave], celda[etiqueta])
    comparar("Rentabilidad acumulada", r["rent_acumulada"], celda["Rentabilidad acumulada"], True)
    comparar("Rentabilidad E.A.", r["rent_ea"], celda["Rentabilidad efectiva anual (E.A.)"], True)

    for fila in valores["Por activo"].iter_rows(min_row=5, max_row=14, values_only=True):
        nombre = fila[0]
        if not nombre or nombre not in r["por_activo"]:
            continue
        a = r["por_activo"][nombre]
        print(f"\n{nombre}")
        comparar("Cantidad", a["cantidad"], fila[5])
        comparar("Total invertido", a["compras"], fila[6])
        comparar("Dividendos / intereses", a["pagos"], fila[9])
        comparar("Valor actual", a["valor"], fila[17])
        comparar("Ganancia", a["ganancia"], fila[21])
        comparar("Rentabilidad acumulada", a["rent"], fila[23], True)
        comparar("Rentabilidad E.A.", a["rent_ea"], fila[24], True)
        comparar("Peso", a["peso"], fila[25], True)

    diario = valores["Valor diario"]
    nombres = [diario.cell(7, c).value for c in range(3, 13)]
    excel_dias = [f for f in diario.iter_rows(min_row=8, values_only=True) if f[0] not in (None, "")]
    antes = comparar.total, comparar.fallas
    if excel_dias:
        programa_dias = portafolio.valor_diario(a_fecha(excel_dias[0][0]), a_fecha(excel_dias[-1][0]))
        if len(programa_dias) != len(excel_dias):
            print(f"\nXX Valor diario: el programa tiene {len(programa_dias)} días y el Excel {len(excel_dias)}")
            comparar.fallas += 1
        for p, e in zip(programa_dias, excel_dias):
            dia = p["fecha"].isoformat()
            if p["fecha"] != a_fecha(e[0]):
                print(f"XX fechas distintas: {p['fecha']} / {e[0]}")
                comparar.fallas += 1
                break
            comparar(f"{dia} TRM", p["trm"], e[1], mostrar=False)
            for k, nombre in enumerate(nombres):
                if nombre:
                    comparar(f"{dia} {nombre}", p["por_activo"].get(nombre, 0.0), e[2 + k], mostrar=False)
            comparar(f"{dia} Renta variable", p["renta_variable"], e[12], mostrar=False)
            comparar(f"{dia} Renta fija", p["renta_fija"], e[13], mostrar=False)
            comparar(f"{dia} Total", p["total"], e[14], mostrar=False)
        print(f"\nValor diario del {excel_dias[0][0]:%Y-%m-%d} al {excel_dias[-1][0]:%Y-%m-%d}: "
              f"{len(excel_dias)} días, {comparar.total - antes[0] - (comparar.fallas - antes[1])} de "
              f"{comparar.total - antes[0]} valores coinciden.")

    print(f"\nTOTAL: {comparar.total - comparar.fallas} de {comparar.total} valores coinciden.")
    sys.exit(0 if comparar.fallas == 0 else 1)


if __name__ == "__main__":
    main()
