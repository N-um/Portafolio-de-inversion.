import json
import os
from datetime import date, timedelta

from activo import Activo
from mercado import Mercado
from operacion import Operacion
from pago import Pago
from posicion import Posicion
from rentabilidad import Rentabilidad


class Portafolio:
    """Guarda las operaciones y los pagos, tiene el Mercado (precios y TRM) y calcula los resultados.

    Todo se calcula a la "fecha de corte" (por defecto, hoy). Lo registrado con fecha
    posterior a la fecha de corte no se tiene en cuenta, igual que en el Excel de control.
    """

    def __init__(self, ruta=None, fecha_corte=None, mercado=None):
        self.ruta = ruta                  # archivo JSON donde se guardan los datos (opcional)
        self._fecha_corte = fecha_corte   # None = hoy
        self.operaciones = []
        self.pagos = []
        self.mercado = mercado or Mercado()

    @property
    def fecha_corte(self):
        return self._fecha_corte or date.today()

    # ---------- Registro de datos ----------
    def agregar_operacion(self, op):
        activo = Activo.buscar(op.activo)
        if op.tipo_activo != activo.tipo:
            raise ValueError(f"{activo.nombre} es de {activo.tipo}, no de {op.tipo_activo}.")
        if activo.moneda == "USD":
            self.mercado.trm(op.fecha)  # sin TRM de esa fecha no se puede pasar a pesos
        self._validar_cantidades(self.operaciones + [op], activo.nombre)
        self.operaciones.append(op)
        self.guardar()

    def eliminar_operacion(self, op):
        restantes = [o for o in self.operaciones if o is not op]
        self._validar_cantidades(restantes, op.activo)
        self.operaciones = restantes
        self.guardar()

    def agregar_pago(self, pago):
        activo = Activo.buscar(pago.activo)
        if activo.es_renta_fija and pago.tipo == Pago.DIVIDENDO:
            raise ValueError("La renta fija paga intereses o capital, no dividendos.")
        if not activo.es_renta_fija and pago.tipo != Pago.DIVIDENDO:
            raise ValueError("Las acciones solo pagan dividendos.")
        compras = [o.fecha for o in self.operaciones if o.activo == pago.activo and o.es_compra]
        if not compras or pago.fecha < min(compras):
            raise ValueError("No hay una compra de ese activo antes de la fecha del pago.")
        if activo.moneda == "USD":
            self.mercado.trm(pago.fecha)
        self.pagos.append(pago)
        self.guardar()

    def eliminar_pago(self, pago):
        self.pagos = [p for p in self.pagos if p is not pago]
        self.guardar()

    def actualizar_precio(self, nombre, precio):
        """Precio de mercado escrito a mano (moneda del activo), válido desde la fecha de corte."""
        activo = Activo.buscar(nombre)
        if activo.es_renta_fija:
            raise ValueError("La renta fija se valora con su tasa E.A.; el precio manual es solo para acciones.")
        self.mercado.agregar(activo.ticker, self.fecha_corte, precio, Mercado.MANUAL)
        self.guardar()

    def quitar_precio_manual(self, nombre):
        self.mercado.quitar_manuales(Activo.buscar(nombre).ticker)
        self.guardar()

    def precio_sugerido(self, nombre, fecha):
        """Cierre de mercado de una acción en esa fecha (o el último antes): (fecha_del_dato, precio, fuente).
        None si no hay datos o si es renta fija (CDT, bonos y TES no cotizan en Yahoo Finance)."""
        activo = Activo.buscar(nombre)
        if activo.es_renta_fija:
            return None
        return self.mercado.dato(activo.ticker, fecha)

    def cantidad_antes_de(self, nombre, fecha):
        """Acciones que se tenían al cierre del día anterior a la fecha (las que cobran un dividendo con esa fecha ex)."""
        return sum((o.cantidad if o.es_compra else -o.cantidad)
                   for o in self.operaciones if o.activo == nombre and o.fecha < fecha)

    def dividendos_automaticos(self, nombre, por_accion):
        """Pagos de dividendo a partir de {fecha ex: monto por acción}: cantidad antes de la fecha ex x monto."""
        pagos = []
        for fecha_ex, monto in sorted(por_accion.items()):
            cantidad = self.cantidad_antes_de(nombre, fecha_ex)
            if fecha_ex <= self.fecha_corte and cantidad > 0:
                pagos.append(Pago(fecha_ex, nombre, Pago.DIVIDENDO, round(cantidad * monto, 6)))
        return pagos

    def traer_dividendos(self):
        """Reemplaza los dividendos registrados de cada acción por los de yfinance.
        Si Yahoo no tiene dividendos de una acción, se dejan los que ya estaban."""
        resumen = []
        for activo in Activo.catalogo():
            if activo.es_renta_fija or not any(o.activo == activo.nombre for o in self.operaciones):
                continue
            por_accion = self.mercado.descargar_dividendos(activo.ticker)
            if activo.ticker_anterior:  # dividendos de antes del cambio de símbolo
                try:
                    viejos = self.mercado.descargar_dividendos(activo.ticker_anterior)
                except Exception:
                    viejos = {}
                corte = min(por_accion) if por_accion else date.max
                por_accion.update({f: v for f, v in viejos.items() if f < corte})
            if not por_accion:
                resumen.append(f"{activo.nombre}: Yahoo no tiene dividendos; se dejan los registrados.")
                continue
            nuevos = self.dividendos_automaticos(activo.nombre, por_accion)
            if activo.moneda == "USD":
                for pago in nuevos:
                    self.mercado.trm(pago.fecha)  # valida que haya TRM antes de cambiar nada
            self.pagos = [x for x in self.pagos if not (x.activo == activo.nombre and x.tipo == Pago.DIVIDENDO)]
            self.pagos += nuevos
            resumen.append(f"{activo.nombre}: {len(nuevos)} dividendos.")
        self.guardar()
        return "\n".join(resumen) if resumen else "No hay acciones registradas."

    def actualizar_mercado(self, desde=None):
        """Descarga la TRM y los cierres de las acciones hasta la fecha de corte, desde la primera
        operación o desde la fecha 'desde' si es anterior (p. ej. una compra vieja que se va a registrar)."""
        fechas = [o.fecha for o in self.operaciones] + ([desde] if desde else [])
        if not fechas:
            raise ValueError("Primero registre alguna operación.")
        inicio = min(fechas) - timedelta(days=10)
        fin = self.fecha_corte
        fuente_trm = self.mercado.descargar_trm(inicio, fin)
        acciones = [a for a in Activo.catalogo() if not a.es_renta_fija]
        anteriores = [a.ticker_anterior for a in acciones if a.ticker_anterior]
        faltan = self.mercado.descargar_precios([a.ticker for a in acciones] + anteriores, inicio, fin)
        for a in acciones:
            if a.ticker_anterior:
                self.mercado.unir_anterior(a.ticker, a.ticker_anterior)
        faltan = [t for t in faltan if t not in anteriores]
        self.guardar()
        mensaje = f"{fuente_trm} y precios de yfinance del {inicio} al {fin}."
        if faltan:
            mensaje += f"\nSin datos para: {', '.join(faltan)} (se mantienen sus datos anteriores; intente de nuevo)."
        return mensaje

    @staticmethod
    def _validar_cantidades(operaciones, nombre):
        """No se puede vender más de lo que se tiene en ningún momento."""
        saldo = 0.0
        for o in Portafolio._en_orden([o for o in operaciones if o.activo == nombre]):
            saldo += o.cantidad if o.es_compra else -o.cantidad
            if saldo < -1e-9:
                raise ValueError(f"El {o.fecha} se venderían más unidades de {nombre} de las que se tienen.")

    @staticmethod
    def _en_orden(lista):
        # sorted es estable: si dos registros tienen la misma fecha, conserva el orden de ingreso.
        return sorted(lista, key=lambda x: x.fecha)

    # ---------- Consultas ----------
    def operaciones_ordenadas(self):
        return self._en_orden(self.operaciones)

    def pagos_ordenados(self):
        return self._en_orden(self.pagos)

    def posiciones(self, fecha=None):
        """Una Posicion por cada activo del catálogo que tenga operaciones hasta la fecha dada
        (por defecto, la fecha de corte)."""
        corte = fecha or self.fecha_corte
        resultado = []
        for activo in Activo.catalogo():
            ops = [o for o in self.operaciones_ordenadas() if o.activo == activo.nombre and o.fecha <= corte]
            if not ops:
                continue
            pagos = [p for p in self.pagos_ordenados() if p.activo == activo.nombre and p.fecha <= corte]
            resultado.append(Posicion(activo, ops, pagos, corte, self.mercado))
        return resultado

    def valor_diario(self, inicio, fin):
        """Valor del portafolio en pesos para cada día del rango (sin pasar de la fecha de corte).

        Cada día se valora como si ese día fuera la fecha de corte: cantidades a esa fecha,
        último cierre conocido de cada acción, TRM de ese día y renta fija causada a su tasa.
        """
        fin = min(fin, self.fecha_corte)
        if inicio > fin:
            raise ValueError("La fecha inicial debe ser anterior a la final (y a la fecha de corte).")
        dias = []
        dia = inicio
        while dia <= fin:
            posiciones = self.posiciones(dia)
            dato_trm = self.mercado.dato(Mercado.TRM, dia)
            dias.append({
                "fecha": dia,
                "trm": dato_trm[1] if dato_trm else None,
                "por_activo": {p.activo.nombre: p.valor for p in posiciones},
                "renta_variable": sum(p.valor for p in posiciones if not p.activo.es_renta_fija),
                "renta_fija": sum(p.valor for p in posiciones if p.activo.es_renta_fija),
                "total": sum(p.valor for p in posiciones)})
            dia += timedelta(days=1)
        return dias

    def resumen(self):
        posiciones = self.posiciones()
        valor_total = sum(p.valor for p in posiciones)
        invertido = sum(p.compras for p in posiciones)
        ganancia = sum(p.ganancia for p in posiciones)
        flujos = [f for p in posiciones for f in p.flujos()]

        por_activo = {}
        for p in posiciones:
            por_activo[p.activo.nombre] = {
                "tipo": p.activo.tipo, "cantidad": p.cantidad, "valor": p.valor,
                "peso": p.valor / valor_total if valor_total > 0 else 0.0,
                "compras": p.compras, "pagos": p.ingresos, "ganancia": p.ganancia,
                "rent": p.rent_acumulada, "rent_ea": p.rent_ea}

        dato_trm = self.mercado.dato(Mercado.TRM, self.fecha_corte)
        return {
            "fecha_corte": self.fecha_corte,
            "trm": dato_trm[1] if dato_trm else None,
            "invertido": invertido,
            "ventas": sum(p.ventas for p in posiciones),
            "ingresos": sum(p.ingresos for p in posiciones),
            "capital": sum(p.capital for p in posiciones),
            "comisiones": sum(p.comisiones for p in posiciones),
            "valor_actual": valor_total,
            "ganancia": ganancia,
            "no_realizada": sum(p.no_realizada for p in posiciones),
            "realizada": sum(p.realizada for p in posiciones),
            "rent_acumulada": Rentabilidad.acumulada(ganancia, invertido),
            "rent_ea": Rentabilidad.efectiva_anual(flujos),
            "renta_fija": sum(p.valor for p in posiciones if p.activo.es_renta_fija),
            "renta_variable": sum(p.valor for p in posiciones if not p.activo.es_renta_fija),
            "por_activo": por_activo,
        }

    def valoracion(self):
        """Filas de la pestaña Valoración de la interfaz."""
        filas = []
        for p in self.posiciones():
            filas.append({
                "activo": p.activo.nombre, "cantidad": p.cantidad, "costo": p.costo_remanente,
                "precio": p.precio_actual, "origen": p.origen, "valor": p.valor,
                "no_realizada": p.no_realizada,
                "rent": p.no_realizada / p.costo_remanente if p.costo_remanente > 0 else None,
                "tasa": p.tasa, "vencimiento": p.vencimiento, "dias": p.dias_al_vencimiento})
        return filas

    # ---------- Archivo ----------
    def guardar(self):
        if not self.ruta:
            return
        datos = {"operaciones": [o.a_dict() for o in self.operaciones],
                 "pagos": [p.a_dict() for p in self.pagos]}
        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        self.mercado.guardar()

    @staticmethod
    def cargar(ruta, fecha_corte=None):
        """Lee las operaciones y pagos del JSON y el mercado del CSV 'mercado.csv' de la misma carpeta."""
        mercado = Mercado.cargar(os.path.join(os.path.dirname(ruta), "mercado.csv"))
        portafolio = Portafolio(ruta, fecha_corte, mercado)
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as archivo:
                datos = json.load(archivo)
            portafolio.operaciones = [Operacion.desde_dict(d) for d in datos.get("operaciones", [])]
            portafolio.pagos = [Pago.desde_dict(d) for d in datos.get("pagos", [])]
        return portafolio
