from datetime import date


class Operacion:
    """Una compra o venta de un activo, con su comisión.

    Para renta fija, la compra trae la tasa efectiva anual (decimal, 0.105 = 10,5 %)
    y la fecha de vencimiento del título.
    """

    COMPRA = "Compra"
    VENTA = "Venta"
    TIPOS_OPERACION = [COMPRA, VENTA]

    def __init__(self, fecha, tipo_activo, activo, tipo_operacion, cantidad, precio,
                 comision=0.0, tasa=0.0, vencimiento=None):
        if not isinstance(fecha, date):
            raise ValueError("La fecha no es válida.")
        if tipo_operacion not in Operacion.TIPOS_OPERACION:
            raise ValueError(f"Operación desconocida: {tipo_operacion}")
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que cero.")
        if precio <= 0:
            raise ValueError("El precio debe ser mayor que cero.")
        if comision < 0:
            raise ValueError("La comisión no puede ser negativa.")
        if tasa < 0:
            raise ValueError("La tasa no puede ser negativa.")
        if tipo_activo == "Renta fija" and tipo_operacion == Operacion.COMPRA:
            if tasa <= 0:
                raise ValueError("La compra de renta fija necesita la tasa E.A. del título.")
            if vencimiento is None or vencimiento <= fecha:
                raise ValueError("La compra de renta fija necesita un vencimiento posterior a la fecha.")

        self.fecha = fecha
        self.tipo_activo = tipo_activo
        self.activo = activo
        self.tipo_operacion = tipo_operacion
        self.cantidad = float(cantidad)
        self.precio = float(precio)
        self.comision = float(comision)
        self.tasa = float(tasa)
        self.vencimiento = vencimiento

    @property
    def es_compra(self):
        return self.tipo_operacion == Operacion.COMPRA

    @property
    def monto(self):
        """Cantidad x precio, sin comisión."""
        return self.cantidad * self.precio

    @property
    def flujo_caja(self):
        """Dinero que sale (-) o entra (+) a la cuenta. La comisión siempre resta."""
        if self.es_compra:
            return -(self.monto + self.comision)
        return self.monto - self.comision

    def a_dict(self):
        return {"fecha": self.fecha.isoformat(), "tipo_activo": self.tipo_activo,
                "activo": self.activo, "tipo_operacion": self.tipo_operacion,
                "cantidad": self.cantidad, "precio": self.precio, "comision": self.comision,
                "tasa": self.tasa,
                "vencimiento": self.vencimiento.isoformat() if self.vencimiento else None}

    @staticmethod
    def desde_dict(d):
        return Operacion(date.fromisoformat(d["fecha"]), d["tipo_activo"], d["activo"],
                         d["tipo_operacion"], d["cantidad"], d["precio"], d.get("comision", 0),
                         d.get("tasa", 0),
                         date.fromisoformat(d["vencimiento"]) if d.get("vencimiento") else None)
