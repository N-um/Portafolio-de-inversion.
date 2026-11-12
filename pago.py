from datetime import date


class Pago:
    """Dinero que el activo le paga al inversionista.

    - Dividendo: lo pagan las acciones.
    - Interés: lo paga la renta fija (cupón o intereses al vencimiento).
    - Capital: la renta fija devuelve parte o todo el dinero invertido.
    """

    DIVIDENDO = "Dividendo"
    INTERES = "Interés"
    CAPITAL = "Capital"
    TIPOS = [DIVIDENDO, INTERES, CAPITAL]

    def __init__(self, fecha, activo, tipo, monto):
        if not isinstance(fecha, date):
            raise ValueError("La fecha no es válida.")
        if tipo not in Pago.TIPOS:
            raise ValueError(f"Tipo de pago desconocido: {tipo}")
        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero.")
        self.fecha = fecha
        self.activo = activo
        self.tipo = tipo
        self.monto = float(monto)

    @property
    def es_ingreso(self):
        """Dividendos e intereses son rendimiento; el capital es devolución de lo invertido."""
        return self.tipo != Pago.CAPITAL

    def a_dict(self):
        return {"fecha": self.fecha.isoformat(), "activo": self.activo,
                "tipo": self.tipo, "monto": self.monto}

    @staticmethod
    def desde_dict(d):
        return Pago(date.fromisoformat(d["fecha"]), d["activo"], d["tipo"], d["monto"])
