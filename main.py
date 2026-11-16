"""Archivo principal: carga los datos guardados y abre la interfaz.

    python main.py                          # valora a la fecha de hoy
    python main.py --fecha-corte 2026-11-11 # valora a una fecha fija (para comparar con el Excel)
"""
import argparse
import os
from datetime import date

from Interfaz import Interfaz
from portafolio import Portafolio

RUTA_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos", "portafolio.json")


def main():
    parser = argparse.ArgumentParser(description="Seguimiento de portafolio de inversión")
    parser.add_argument("--fecha-corte", type=date.fromisoformat, default=None,
                        help="fecha de valoración AAAA-MM-DD (por defecto, hoy)")
    parser.add_argument("--datos", default=RUTA_DATOS, help="archivo JSON con las operaciones")
    args = parser.parse_args()

    portafolio = Portafolio.cargar(args.datos, args.fecha_corte)
    Interfaz(portafolio).ejecutar()


if __name__ == "__main__":
    main()
