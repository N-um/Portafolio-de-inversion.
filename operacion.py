from datetime import date


class Operacion:
    """Una compra o venta de un activo (acción, CDT, bono o TES)."""

    TIPOS_ACTIVO = ["Acción", "CDT", "Bono", "TES"]
    TIPOS_OPERACION = ["Compra", "Venta"]

    def __init__(self, fecha, tipo_activo, nombre, tipo_operacion,
                 cantidad, precio, comision=0.0, tasa_ea=0.0, vencimiento=None):
        self.fecha = fecha                    # date
        self.tipo_activo = tipo_activo        # Acción / CDT / Bono / TES
        self.nombre = nombre                  # ej: "Ecopetrol", "CDT Bancolombia"
        self.tipo_operacion = tipo_operacion  # Compra / Venta
        self.cantidad = cantidad
        self.precio = precio                  # precio o valor por unidad
        self.comision = comision              # comisión del bróker
        self.tasa_ea = tasa_ea                # tasa E.A. del título (renta fija), ej. 0.12
        self.vencimiento = vencimiento        # date o None

    @property
    def es_renta_fija(self):
        return self.tipo_activo != "Acción"

    @property
    def valor_bruto(self):
        return self.cantidad * self.precio

    def flujo_de_caja(self):
        """Dinero que sale (negativo) o entra (positivo) por esta operación."""
        if self.tipo_operacion == "Compra":
            return -(self.valor_bruto + self.comision)
        return self.valor_bruto - self.comision

    def a_dict(self):
        return {
            "fecha": self.fecha.isoformat(), "tipo_activo": self.tipo_activo,
            "nombre": self.nombre, "tipo_operacion": self.tipo_operacion,
            "cantidad": self.cantidad, "precio": self.precio,
            "comision": self.comision, "tasa_ea": self.tasa_ea,
            "vencimiento": self.vencimiento.isoformat() if self.vencimiento else None,
        }

    @staticmethod
    def desde_dict(d):
        venc = date.fromisoformat(d["vencimiento"]) if d.get("vencimiento") else None
        return Operacion(date.fromisoformat(d["fecha"]), d["tipo_activo"], d["nombre"],
                         d["tipo_operacion"], d["cantidad"], d["precio"],
                         d["comision"], d["tasa_ea"], venc)
