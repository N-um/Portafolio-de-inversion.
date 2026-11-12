from rentabilidad import Rentabilidad


class Posicion:
    """Resultado de un activo a la fecha de corte, calculado con sus operaciones y pagos.

    Cada propiedad corresponde a una columna de la hoja "Por activo" del Excel de control.
    Las operaciones deben llegar en orden cronológico y solo con fecha <= fecha de corte.
    """

    def __init__(self, activo, operaciones, pagos, fecha_corte, precio_manual=None):
        self.activo = activo
        self.operaciones = operaciones
        self.pagos = pagos
        self.fecha_corte = fecha_corte
        self.precio_manual = precio_manual

    # ---------- Cantidades y dinero ----------
    @property
    def cantidad_comprada(self):
        return sum(o.cantidad for o in self.operaciones if o.es_compra)

    @property
    def cantidad(self):
        return self.cantidad_comprada - sum(o.cantidad for o in self.operaciones if not o.es_compra)

    @property
    def compras(self):
        """Total invertido: lo pagado en compras, comisiones incluidas."""
        return sum(-o.flujo_caja for o in self.operaciones if o.es_compra)

    @property
    def ventas(self):
        """Ventas netas: lo recibido en ventas, ya descontada la comisión."""
        return sum(o.flujo_caja for o in self.operaciones if not o.es_compra)

    @property
    def comisiones(self):
        return sum(o.comision for o in self.operaciones)

    @property
    def ingresos(self):
        """Dividendos + intereses."""
        return sum(p.monto for p in self.pagos if p.es_ingreso)

    @property
    def capital(self):
        """Pagos de capital (devolución del dinero invertido en renta fija)."""
        return sum(p.monto for p in self.pagos if not p.es_ingreso)

    # ---------- Condiciones del título (renta fija) ----------
    def _primera_compra(self):
        return next((o for o in self.operaciones if o.es_compra), None)

    @property
    def tasa(self):
        compra = self._primera_compra()
        return compra.tasa if compra and self.activo.es_renta_fija else None

    @property
    def vencimiento(self):
        compra = self._primera_compra()
        return compra.vencimiento if compra and self.activo.es_renta_fija else None

    @property
    def dias_al_vencimiento(self):
        if self.vencimiento is None:
            return None
        return max(0, (self.vencimiento - self.fecha_corte).days)

    # ---------- Valoración ----------
    @property
    def origen(self):
        if self.cantidad <= 0:
            return "Sin posición"
        if self.precio_manual is not None:
            return "Manual"
        if not self.activo.es_renta_fija:
            return "Último precio"
        if self.fecha_corte >= self.vencimiento:
            return "Vencido"
        return "Tasa E.A."

    @property
    def valor(self):
        origen = self.origen
        if origen in ("Sin posición", "Vencido"):
            return 0.0
        if origen == "Manual":
            return self.precio_manual * self.cantidad
        if origen == "Último precio":
            return self.operaciones[-1].precio * self.cantidad
        return max(0.0, self._valor_causado())

    def _valor_causado(self):
        """Renta fija: cada peso invertido crece a la tasa E.A. hasta la fecha de corte;
        cada peso recibido (venta, interés o capital) deja de crecer desde el día en que se recibió.

        valor = sum(compras * (1+t)^(d/365)) - sum(ventas, intereses, capital * (1+t)^(d/365))
        con d = días entre el movimiento y la fecha de corte (sin pasar del vencimiento).
        """
        fin = min(self.fecha_corte, self.vencimiento)

        def crecer(monto, fecha):
            return monto * (1 + self.tasa) ** ((fin - fecha).days / 365)

        total = 0.0
        for o in self.operaciones:
            total += crecer(o.monto, o.fecha) if o.es_compra else -crecer(o.monto, o.fecha)
        for p in self.pagos:
            total -= crecer(p.monto, p.fecha)
        return total

    @property
    def precio_actual(self):
        return self.valor / self.cantidad if self.cantidad > 0 else 0.0

    # ---------- Resultados ----------
    @property
    def costo_remanente(self):
        """Costo de lo que aún se tiene: cantidad x costo promedio de compra, menos capital devuelto."""
        if self.cantidad_comprada == 0:
            return 0.0
        return self.cantidad * self.compras / self.cantidad_comprada - self.capital

    @property
    def ganancia(self):
        """Valor actual + todo lo recibido - todo lo invertido (las comisiones ya están restadas)."""
        return self.valor + self.ventas + self.ingresos + self.capital - self.compras

    @property
    def no_realizada(self):
        return self.valor - self.costo_remanente

    @property
    def realizada(self):
        return self.ganancia - self.no_realizada

    @property
    def rent_acumulada(self):
        return Rentabilidad.acumulada(self.ganancia, self.compras)

    def flujos(self):
        """Flujos de caja para la TIR: compras (-), ventas y pagos (+) y el valor actual al corte (+)."""
        flujos = [(o.fecha, o.flujo_caja) for o in self.operaciones]
        flujos += [(p.fecha, p.monto) for p in self.pagos]
        flujos.append((self.fecha_corte, self.valor))
        return flujos

    @property
    def rent_ea(self):
        return Rentabilidad.efectiva_anual(self.flujos())
