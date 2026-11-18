class Activo:
    """Un activo del catálogo: lo que el usuario puede elegir al registrar operaciones."""

    def __init__(self, nombre, ticker, tipo, sector, color):
        self.nombre = nombre
        self.ticker = ticker
        self.tipo = tipo        # Acción / CDT / Bono / TES
        self.sector = sector
        self.color = color      # color en los gráficos

    @property
    def es_renta_fija(self):
        return self.tipo != "Acción"

    @staticmethod
    def catalogo():
        # Para agregar más activos (un bono, un TES...) basta con añadir una línea aquí.
        return [
            Activo("Ecopetrol", "EC", "Acción", "Energía", "#2E86AB"),
            Activo("Bancolombia", "CIB", "Acción", "Financiero", "#F18F01"),
            Activo("Nike", "NKE", "Acción", "Consumo", "#C73E1D"),
            Activo("Coca-Cola", "KO", "Acción", "Consumo", "#6A994E"),
            Activo("CDT", "CDT", "CDT", "Financiero", "#7B5EA7"),
        ]

    @staticmethod
    def buscar(nombre):
        catalogo = Activo.catalogo()
        return next((a for a in catalogo if a.nombre == nombre), catalogo[0])
