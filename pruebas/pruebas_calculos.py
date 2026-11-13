"""Pruebas de los cálculos con casos que se pueden verificar a mano.

Uso:  python -m unittest discover -s pruebas -p "pruebas_*.py"
"""
import json
import os
import sys
import types
import unittest
from datetime import date
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mercado import Mercado  # noqa: E402
from operacion import Operacion  # noqa: E402
from pago import Pago  # noqa: E402
from portafolio import Portafolio  # noqa: E402
from rentabilidad import Rentabilidad  # noqa: E402

RV, RF = "Renta variable", "Renta fija"


def portafolio_con_trm(fecha_corte, trm=4000.0):
    mercado = Mercado()
    mercado.agregar(Mercado.TRM, date(2020, 1, 1), trm, "prueba")
    return Portafolio(fecha_corte=fecha_corte, mercado=mercado)


class PruebasCalculos(unittest.TestCase):

    def test_tir_de_un_anio(self):
        # Invertir 100 y recibir 110 a los 365 días = 10 % E.A.
        tasa = Rentabilidad.efectiva_anual([(date(2025, 1, 1), -100), (date(2026, 1, 1), 110)])
        self.assertAlmostEqual(tasa, 0.10, places=9)

    def test_tir_sin_flujo_positivo(self):
        self.assertIsNone(Rentabilidad.efectiva_anual([(date(2025, 1, 1), -100)]))

    def test_comision_automatica(self):
        op = Operacion(date(2025, 1, 1), RV, "Ecopetrol", "Compra", 100, 2000)
        self.assertAlmostEqual(op.comision, 400)            # 0,2 % de 200.000
        self.assertAlmostEqual(op.flujo_caja, -200_400)

    def test_cdt_rinde_su_tasa_menos_la_comision(self):
        p = Portafolio(fecha_corte=date(2026, 7, 1))
        p.agregar_operacion(Operacion(date(2026, 1, 1), RF, "CDT Bancolombia", "Compra", 1,
                                      1_000_000, 0.12, date(2027, 1, 1)))
        r = p.resumen()
        dias = (date(2026, 7, 1) - date(2026, 1, 1)).days
        self.assertAlmostEqual(r["valor_actual"], 1_000_000 * 1.12 ** (dias / 365), places=6)
        esperado = (r["valor_actual"] / 1_002_000) ** (365 / dias) - 1   # pagó 1.002.000 con la comisión
        self.assertAlmostEqual(r["rent_ea"], esperado, places=9)

    def test_bono_con_cupon_vuelve_a_su_valor(self):
        # Con un cupón igual a la tasa, después de pagarlo el título vale lo invertido.
        p = Portafolio(fecha_corte=date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RF, "Bono Ecopetrol", "Compra", 1,
                                      1_000_000, 0.10, date(2030, 1, 1)))
        p.agregar_pago(Pago(date(2026, 1, 1), "Bono Ecopetrol", "Interés", 100_000))
        self.assertAlmostEqual(p.resumen()["valor_actual"], 1_000_000, places=6)

    def test_titulo_vencido_vale_cero(self):
        p = Portafolio(fecha_corte=date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RF, "CDT Davivienda", "Compra", 1,
                                      1_000_000, 0.10, date(2025, 7, 1)))
        self.assertEqual(p.resumen()["valor_actual"], 0)

    def test_accion_en_pesos_con_dividendo(self):
        p = Portafolio(fecha_corte=date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RV, "Ecopetrol", "Compra", 100, 2000))
        p.agregar_pago(Pago(date(2025, 6, 1), "Ecopetrol", "Dividendo", 10_000))
        p.actualizar_precio("Ecopetrol", 2200)
        r = p.resumen()
        self.assertAlmostEqual(r["invertido"], 200_400)                    # 100 x 2.000 + 0,2 %
        self.assertAlmostEqual(r["valor_actual"], 220_000)                 # 100 x 2.200
        self.assertAlmostEqual(r["ganancia"], 220_000 + 10_000 - 200_400)  # 29.600
        self.assertAlmostEqual(r["no_realizada"], 220_000 - 200_400)
        self.assertAlmostEqual(r["realizada"], 10_000)

    def test_accion_en_dolares_usa_la_trm_de_cada_dia(self):
        mercado = Mercado()
        mercado.agregar(Mercado.TRM, date(2025, 1, 1), 4000, "prueba")
        mercado.agregar(Mercado.TRM, date(2025, 6, 1), 4200, "prueba")
        mercado.agregar("NKE", date(2025, 12, 31), 80, "prueba")
        p = Portafolio(fecha_corte=date(2026, 1, 1), mercado=mercado)
        p.agregar_operacion(Operacion(date(2025, 1, 2), RV, "Nike", "Compra", 10, 70))
        p.agregar_pago(Pago(date(2025, 7, 1), "Nike", "Dividendo", 4))
        r = p.resumen()
        self.assertAlmostEqual(r["invertido"], 10 * 70 * 1.002 * 4000)   # TRM del día de compra
        self.assertAlmostEqual(r["ingresos"], 4 * 4200)                  # TRM del día del pago
        self.assertAlmostEqual(r["valor_actual"], 10 * 80 * 4200)        # cierre del 31-dic x TRM vigente

    def test_sin_trm_no_registra_dolares(self):
        p = Portafolio(fecha_corte=date(2026, 1, 1))
        with self.assertRaises(ValueError):
            p.agregar_operacion(Operacion(date(2025, 1, 2), RV, "Nike", "Compra", 1, 70))

    def test_valor_diario_igual_a_valorar_cada_dia(self):
        p = portafolio_con_trm(date(2025, 3, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 10), RV, "Nike", "Compra", 2, 100))
        p.mercado.agregar("NKE", date(2025, 2, 3), 110, "prueba")
        dias = p.valor_diario(date(2025, 1, 9), date(2025, 12, 31))   # se corta en la fecha de corte
        self.assertEqual(len(dias), 52)
        self.assertEqual(dias[0]["total"], 0)                            # antes de comprar
        self.assertAlmostEqual(dias[1]["total"], 2 * 100 * 4000)         # sin cierre: precio de compra
        self.assertAlmostEqual(dias[-1]["total"], 2 * 110 * 4000)        # último cierre conocido

    def test_precio_sugerido(self):
        p = portafolio_con_trm(date(2026, 1, 1))
        p.mercado.agregar("NKE", date(2025, 3, 7), 71.5, "yfinance")       # viernes
        self.assertEqual(p.precio_sugerido("Nike", date(2025, 3, 9)),     # domingo: último cierre
                         (date(2025, 3, 7), 71.5, "yfinance"))
        self.assertIsNone(p.precio_sugerido("Nike", date(2025, 3, 6)))     # antes del primer dato
        self.assertIsNone(p.precio_sugerido("CDT Bancolombia", date(2025, 3, 9)))  # renta fija

    def test_no_vende_mas_de_lo_que_tiene(self):
        p = portafolio_con_trm(date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RV, "Nike", "Compra", 10, 400))
        with self.assertRaises(ValueError):
            p.agregar_operacion(Operacion(date(2025, 2, 1), RV, "Nike", "Venta", 11, 400))

    def test_ignora_lo_posterior_a_la_fecha_de_corte(self):
        p = Portafolio(fecha_corte=date(2025, 6, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RV, "Ecopetrol", "Compra", 10, 2000))
        p.agregar_operacion(Operacion(date(2025, 7, 1), RV, "Ecopetrol", "Compra", 10, 2500))
        self.assertAlmostEqual(p.resumen()["invertido"], 20_040)

    def test_tipo_de_pago_coherente(self):
        p = Portafolio(fecha_corte=date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RV, "Ecopetrol", "Compra", 1, 2000))
        with self.assertRaises(ValueError):
            p.agregar_pago(Pago(date(2025, 3, 1), "Ecopetrol", "Interés", 1000))


class PruebasDividendos(unittest.TestCase):

    def test_cobra_solo_lo_que_tenia_antes_de_la_fecha_ex(self):
        p = portafolio_con_trm(date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 10), RV, "Nike", "Compra", 10, 70))
        p.agregar_operacion(Operacion(date(2025, 3, 3), RV, "Nike", "Compra", 5, 70))   # el mismo día ex: no cobra
        p.agregar_operacion(Operacion(date(2025, 9, 1), RV, "Nike", "Venta", 15, 75))
        por_accion = {date(2024, 12, 2): 0.40,     # antes de comprar: nada
                      date(2025, 3, 3): 0.40,      # 10 acciones
                      date(2025, 6, 2): 0.40,      # 15 acciones
                      date(2025, 12, 1): 0.41}     # ya vendió todo: nada
        pagos = p.dividendos_automaticos("Nike", por_accion)
        self.assertEqual([(x.fecha, x.monto) for x in pagos],
                         [(date(2025, 3, 3), 4.0), (date(2025, 6, 2), 6.0)])

    def test_reemplaza_los_dividendos_y_deja_si_yahoo_no_tiene(self):
        p = portafolio_con_trm(date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 10), RV, "Nike", "Compra", 10, 70))
        p.agregar_operacion(Operacion(date(2025, 1, 10), RV, "Ecopetrol", "Compra", 100, 2000))
        p.agregar_pago(Pago(date(2025, 4, 1), "Nike", "Dividendo", 3.4))            # escrito a mano
        p.agregar_pago(Pago(date(2025, 4, 1), "Ecopetrol", "Dividendo", 10_000))     # escrito a mano
        datos = {"NKE": {date(2025, 3, 3): 0.40}, "ECOPETROL.CL": {}}
        with mock.patch.object(Mercado, "descargar_dividendos", side_effect=lambda t: datos[t]):
            mensaje = p.traer_dividendos()
        self.assertEqual(sorted((x.activo, x.fecha, x.monto) for x in p.pagos),
                         [("Ecopetrol", date(2025, 4, 1), 10_000), ("Nike", date(2025, 3, 3), 4.0)])
        self.assertIn("Nike: 1 dividendos", mensaje)

    def test_lee_el_historial_de_yfinance(self):
        import pandas as pd
        serie = pd.Series([0.37, 0.40], index=pd.DatetimeIndex(["2024-12-02", "2025-03-03"], tz="America/New_York"))
        falso = types.SimpleNamespace(Ticker=lambda t: types.SimpleNamespace(dividends=serie))
        with mock.patch.dict(sys.modules, {"yfinance": falso}):
            self.assertEqual(Mercado.descargar_dividendos("NKE"), {date(2024, 12, 2): 0.37, date(2025, 3, 3): 0.40})


class PruebasDescargas(unittest.TestCase):
    """Simula las respuestas de datos.gov.co y de yfinance (sin internet)."""

    def test_trm_oficial(self):
        respuesta = json.dumps([
            {"valor": "4100.50", "vigenciadesde": "2025-01-03T00:00:00.000"},
            {"valor": "4120.00", "vigenciadesde": "2025-01-04T00:00:00.000"},   # vale sáb., dom. y lun.
            {"valor": "4090.10", "vigenciadesde": "2025-01-07T00:00:00.000"}]).encode()
        archivo = mock.MagicMock()
        archivo.__enter__.return_value.read.return_value = respuesta
        mercado = Mercado()
        with mock.patch("urllib.request.urlopen", return_value=archivo):
            fuente = mercado.descargar_trm(date(2025, 1, 1), date(2025, 1, 31))
        self.assertIn("datos.gov.co", fuente)
        self.assertEqual(mercado.trm(date(2025, 1, 6)), 4120.00)
        self.assertEqual(mercado.trm(date(2025, 1, 31)), 4090.10)

    def test_cierres_de_yfinance_sin_ajustar_y_conserva_manuales(self):
        import pandas as pd
        indice = pd.DatetimeIndex(["2025-01-02", "2025-01-03"], name="Date")
        columnas = pd.MultiIndex.from_product([["Adj Close", "Close"], ["CIB", "NKE"]], names=["Price", "Ticker"])
        tabla = pd.DataFrame([[30, 70, 31, 71], [32, 72, 33, 73]], index=indice, columns=columnas, dtype=float)
        falso = types.SimpleNamespace(download=mock.Mock(return_value=tabla))
        mercado = Mercado()
        mercado.agregar("NKE", date(2025, 1, 3), 99, Mercado.MANUAL)
        with mock.patch.dict(sys.modules, {"yfinance": falso}):
            faltan = mercado.descargar_precios(["CIB", "NKE", "ECOPETROL.CL"], date(2025, 1, 1), date(2025, 1, 3))
        self.assertEqual(faltan, ["ECOPETROL.CL"])
        self.assertEqual(mercado.dato("CIB", date(2025, 1, 5))[1:], (33.0, "yfinance"))   # Close, no Adj Close
        self.assertEqual(mercado.dato("NKE", date(2025, 1, 3))[1:], (99.0, Mercado.MANUAL))
        self.assertFalse(falso.download.call_args.kwargs["auto_adjust"])


if __name__ == "__main__":
    unittest.main()
