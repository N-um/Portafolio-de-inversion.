"""Copia los datos del programa al Excel de control (hojas Operaciones, Pagos y Mercado).

Uso (desde la carpeta del proyecto):
    python pruebas/llenar_excel.py [ruta_del_excel]

Solo escribe en las celdas de datos (amarillas); las fórmulas no se tocan. Después:
abrir el Excel, guardarlo (Excel recalcula todo al abrir) y correr
    python pruebas/comparar_con_excel.py
Necesita openpyxl.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openpyxl import load_workbook  # noqa: E402

from portafolio import Portafolio  # noqa: E402

CARPETA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_EXCEL = os.path.join(CARPETA, "excel", "Portafolio_control.xlsx")
RUTA_DATOS = os.path.join(CARPETA, "datos", "portafolio.json")

# hoja: (primera fila, última fila, número de columnas de datos)
CAPACIDAD = {"Operaciones": (5, 64, 7), "Pagos": (5, 104, 4), "Mercado": (5, 8004, 4)}


def escribir(hoja, filas):
    primera, ultima, columnas = CAPACIDAD[hoja.title]
    if len(filas) > ultima - primera + 1:
        sys.exit(f"La hoja {hoja.title} admite {ultima - primera + 1} filas y hay {len(filas)}.")
    for r in range(primera, ultima + 1):
        valores = filas[r - primera] if r - primera < len(filas) else [None] * columnas
        for c, valor in enumerate(valores, start=1):
            hoja.cell(r, c).value = valor


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else RUTA_EXCEL
    portafolio = Portafolio.cargar(RUTA_DATOS)
    libro = load_workbook(ruta)
    escribir(libro["Operaciones"], [
        [o.fecha, o.activo, o.tipo_operacion, o.cantidad, o.precio, o.tasa or None, o.vencimiento]
        for o in portafolio.operaciones_ordenadas()])
    escribir(libro["Pagos"], [[p.fecha, p.activo, p.tipo, p.monto] for p in portafolio.pagos_ordenados()])
    escribir(libro["Mercado"], [list(f) for f in portafolio.mercado.filas()])
    libro.calculation.fullCalcOnLoad = True
    libro.save(ruta)
    print(f"Listo: {len(portafolio.operaciones)} operaciones, {len(portafolio.pagos)} pagos y "
          f"{len(portafolio.mercado.filas())} datos de mercado copiados a {ruta}.\n"
          "Abra el Excel, guárdelo y ejecute: python pruebas/comparar_con_excel.py")


if __name__ == "__main__":
    main()
