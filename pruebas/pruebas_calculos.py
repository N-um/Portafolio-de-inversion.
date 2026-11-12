"""Pruebas de los cálculos con casos que se pueden verificar a mano.

Uso:  python -m unittest discover -s pruebas -p "pruebas_*.py"
"""
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operacion import Operacion  # noqa: E402
from pago import Pago  # noqa: E402
from portafolio import Portafolio  # noqa: E402
from rentabilidad import Rentabilidad  # noqa: E402

RV, RF = "Renta variable", "Renta fija"


class PruebasCalculos(unittest.TestCase):

    def test_tir_de_un_anio(self):
        # Invertir 100 y recibir 110 a los 365 días = 10 % E.A.
        tasa = Rentabilidad.efectiva_anual([(date(2025, 1, 1), -100), (date(2026, 1, 1), 110)])
        self.assertAlmostEqual(tasa, 0.10, places=9)

    def test_tir_sin_flujo_positivo(self):
        self.assertIsNone(Rentabilidad.efectiva_anual([(date(2025, 1, 1), -100)]))

    def test_cdt_rinde_su_tasa(self):
        p = Portafolio(fecha_corte=date(2026, 7, 1))
        p.agregar_operacion(Operacion(date(2026, 1, 1), RF, "CDT Bancolombia", "Compra", 1,
                                      1_000_000, 0, 0.12, date(2027, 1, 1)))
        r = p.resumen()
        dias = (date(2026, 7, 1) - date(2026, 1, 1)).days
        self.assertAlmostEqual(r["valor_actual"], 1_000_000 * 1.12 ** (dias / 365), places=6)
        self.assertAlmostEqual(r["rent_ea"], 0.12, places=9)

    def test_bono_con_cupon_vuelve_a_su_valor(self):
        # Con un cupón igual a la tasa, después de pagarlo el título vale lo invertido.
        p = Portafolio(fecha_corte=date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RF, "Bono Ecopetrol", "Compra", 1,
                                      1_000_000, 0, 0.10, date(2030, 1, 1)))
        p.agregar_pago(Pago(date(2026, 1, 1), "Bono Ecopetrol", "Interés", 100_000))
        self.assertAlmostEqual(p.resumen()["valor_actual"], 1_000_000, places=6)

    def test_titulo_vencido_vale_cero(self):
        p = Portafolio(fecha_corte=date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RF, "CDT Davivienda", "Compra", 1,
                                      1_000_000, 0, 0.10, date(2025, 7, 1)))
        self.assertEqual(p.resumen()["valor_actual"], 0)

    def test_accion_comisiones_y_dividendo(self):
        p = Portafolio(fecha_corte=date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RV, "Ecopetrol", "Compra", 100, 2000, 600))
        p.agregar_pago(Pago(date(2025, 6, 1), "Ecopetrol", "Dividendo", 10_000))
        p.actualizar_precio("Ecopetrol", 2200)
        r = p.resumen()
        self.assertEqual(r["invertido"], 200_600)                      # 100 x 2.000 + 600
        self.assertEqual(r["valor_actual"], 220_000)                   # 100 x 2.200
        self.assertEqual(r["ganancia"], 220_000 + 10_000 - 200_600)    # 29.400
        self.assertAlmostEqual(r["rent_acumulada"], 29_400 / 200_600)
        self.assertEqual(r["no_realizada"], 220_000 - 200_600)
        self.assertEqual(r["realizada"], 10_000)

    def test_no_vende_mas_de_lo_que_tiene(self):
        p = Portafolio(fecha_corte=date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RV, "Nike", "Compra", 10, 400_000))
        with self.assertRaises(ValueError):
            p.agregar_operacion(Operacion(date(2025, 2, 1), RV, "Nike", "Venta", 11, 400_000))

    def test_ignora_lo_posterior_a_la_fecha_de_corte(self):
        p = Portafolio(fecha_corte=date(2025, 6, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RV, "Nike", "Compra", 10, 400_000))
        p.agregar_operacion(Operacion(date(2025, 7, 1), RV, "Nike", "Compra", 10, 500_000))
        self.assertEqual(p.resumen()["invertido"], 4_000_000)

    def test_tipo_de_pago_coherente(self):
        p = Portafolio(fecha_corte=date(2026, 1, 1))
        p.agregar_operacion(Operacion(date(2025, 1, 1), RV, "Nike", "Compra", 1, 400_000))
        with self.assertRaises(ValueError):
            p.agregar_pago(Pago(date(2025, 3, 1), "Nike", "Interés", 1000))


if __name__ == "__main__":
    unittest.main()
