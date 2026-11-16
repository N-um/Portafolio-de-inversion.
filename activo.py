class Activo:
    """Un instrumento del catálogo: una acción (renta variable) o un título de renta fija.

    El catálogo es fijo y es el mismo que aparece en la hoja "Activos" del Excel de control.
    Las acciones se cotizan con yfinance; la renta fija (CDT, bonos, TES) no está en Yahoo
    Finance y se valora con su tasa E.A.
    """

    RENTA_FIJA = "Renta fija"
    RENTA_VARIABLE = "Renta variable"

    def __init__(self, nombre, ticker, tipo, clase, sector, moneda, color, ticker_anterior=None):
        if tipo not in (Activo.RENTA_FIJA, Activo.RENTA_VARIABLE):
            raise ValueError(f"Tipo de activo desconocido: {tipo}")
        self.nombre = nombre
        self.ticker = ticker  # acciones: símbolo de Yahoo Finance (yfinance); renta fija: código interno
        self.tipo = tipo      # Renta fija / Renta variable
        self.clase = clase    # Acción, CDT, Bono o TES
        self.sector = sector
        self.moneda = moneda  # COP o USD: moneda en que se registran precios y pagos del activo
        self.color = color    # color usado en los gráficos de la interfaz
        # símbolo con el que cotizaba antes (p. ej. Bancolombia antes de volverse Grupo Cibest):
        # su historia de precios y dividendos se une a la del ticker actual
        self.ticker_anterior = ticker_anterior

    @property
    def es_renta_fija(self):
        return self.tipo == Activo.RENTA_FIJA

    def __repr__(self):
        return f"Activo({self.nombre!r}, {self.clase})"

    @staticmethod
    def catalogo():
        return [
            Activo("Ecopetrol", "ECOPETROL.CL", Activo.RENTA_VARIABLE, "Acción", "Energía", "COP", "#F18F01"),
            Activo("Grupo Cibest", "CIB", Activo.RENTA_VARIABLE, "Acción (ADR)", "Financiero", "USD", "#C73E1D"),
            Activo("Cibest preferencial", "PFCIBEST.CL", Activo.RENTA_VARIABLE, "Acción", "Financiero", "COP", "#E4572E",
                   ticker_anterior="PFBCOLOM.CL"),
            Activo("Nike", "NKE", Activo.RENTA_VARIABLE, "Acción", "Consumo", "USD", "#6A4C93"),
            Activo("Grupo Energía Bogotá", "GEB.CL", Activo.RENTA_VARIABLE, "Acción", "Energía", "COP", "#E0A458"),
            Activo("Nu Holdings", "NU", Activo.RENTA_VARIABLE, "Acción", "Financiero", "USD", "#8E44AD"),
            Activo("CDT Davivienda", "CDT-DAV", Activo.RENTA_FIJA, "CDT", "Financiero", "COP", "#2E86AB"),
            Activo("CDT Bancolombia", "CDT-BCO", Activo.RENTA_FIJA, "CDT", "Financiero", "COP", "#3BB273"),
            Activo("Bono Ecopetrol", "BONO-ECO", Activo.RENTA_FIJA, "Bono", "Energía", "COP", "#1F3A5F"),
            Activo("TES 2031", "TES-2031", Activo.RENTA_FIJA, "TES", "Gobierno", "COP", "#7FB7BE"),
        ]

    @staticmethod
    def buscar(nombre):
        for activo in Activo.catalogo():
            if activo.nombre == nombre:
                return activo
        raise ValueError(f"El activo '{nombre}' no está en el catálogo.")
