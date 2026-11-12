class Activo:
    """Un instrumento del catálogo: una acción (renta variable) o un título de renta fija.

    El catálogo es fijo y es el mismo que aparece en la hoja "Activos" del Excel de control.
    """

    RENTA_FIJA = "Renta fija"
    RENTA_VARIABLE = "Renta variable"

    def __init__(self, nombre, ticker, tipo, clase, sector, color):
        if tipo not in (Activo.RENTA_FIJA, Activo.RENTA_VARIABLE):
            raise ValueError(f"Tipo de activo desconocido: {tipo}")
        self.nombre = nombre
        self.ticker = ticker
        self.tipo = tipo      # Renta fija / Renta variable
        self.clase = clase    # Acción, CDT, Bono o TES
        self.sector = sector
        self.color = color    # color usado en los gráficos de la interfaz

    @property
    def es_renta_fija(self):
        return self.tipo == Activo.RENTA_FIJA

    def __repr__(self):
        return f"Activo({self.nombre!r}, {self.clase})"

    @staticmethod
    def catalogo():
        return [
            Activo("Ecopetrol", "ECOPETROL", Activo.RENTA_VARIABLE, "Acción", "Energía", "#F18F01"),
            Activo("Bancolombia", "PFBCOLOM", Activo.RENTA_VARIABLE, "Acción", "Financiero", "#C73E1D"),
            Activo("Nike", "NKE", Activo.RENTA_VARIABLE, "Acción", "Consumo", "#6A4C93"),
            Activo("CDT Davivienda", "CDT-DAV", Activo.RENTA_FIJA, "CDT", "Financiero", "#2E86AB"),
            Activo("CDT Bancolombia", "CDT-BCO", Activo.RENTA_FIJA, "CDT", "Financiero", "#3BB273"),
            Activo("Bono Ecopetrol", "BONO-ECO", Activo.RENTA_FIJA, "Bono", "Energía", "#1F3A5F"),
            Activo("TES 2031", "TES-2031", Activo.RENTA_FIJA, "TES", "Gobierno", "#7FB7BE"),
        ]

    @staticmethod
    def buscar(nombre):
        for activo in Activo.catalogo():
            if activo.nombre == nombre:
                return activo
        raise ValueError(f"El activo '{nombre}' no está en el catálogo.")
