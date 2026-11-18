import os

from portafolio import Portafolio
from interfaz import Interfaz


def main():
    portafolio = Portafolio()
    if os.path.exists(Portafolio.ARCHIVO):
        portafolio.cargar()
    else:
        portafolio.cargar_ejemplo()
    Interfaz(portafolio).ejecutar()


if __name__ == "__main__":
    main()
