import json
import os
from datetime import date

from activo import Activo
from operacion import Operacion
from pago import Pago
from posicion import Posicion
from rentabilidad import Rentabilidad


class Portafolio:
    """Guarda las operaciones, los pagos y los precios manuales, y calcula los resultados.

    Todo se calcula a la "fecha de corte" (por defecto, hoy). Lo registrado con fecha
    posterior a la fecha de corte no se tiene en cuenta, igual que en el Excel de control.
    """

    def __init__(self, ruta=None, fecha_corte=None):
        self.ruta = ruta                  # archivo JSON donde se guardan los datos (opcional)
        self._fecha_corte = fecha_corte   # None = hoy
        self.operaciones = []
        self.pagos = []
        self.precios_manuales = {}        # nombre del activo -> precio de mercado por unidad

    @property
    def fecha_corte(self):
        return self._fecha_corte or date.today()

    # ---------- Registro de datos ----------
    def agregar_operacion(self, op):
        activo = Activo.buscar(op.activo)
        if op.tipo_activo != activo.tipo:
            raise ValueError(f"{activo.nombre} es de {activo.tipo}, no de {op.tipo_activo}.")
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
        self.pagos.append(pago)
        self.guardar()

    def eliminar_pago(self, pago):
        self.pagos = [p for p in self.pagos if p is not pago]
        self.guardar()

    def actualizar_precio(self, nombre, precio):
        Activo.buscar(nombre)
        self.precios_manuales[nombre] = float(precio)
        self.guardar()

    def quitar_precio_manual(self, nombre):
        self.precios_manuales.pop(nombre, None)
        self.guardar()

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

    def posiciones(self):
        """Una Posicion por cada activo del catálogo que tenga operaciones hasta la fecha de corte."""
        corte = self.fecha_corte
        resultado = []
        for activo in Activo.catalogo():
            ops = [o for o in self.operaciones_ordenadas() if o.activo == activo.nombre and o.fecha <= corte]
            if not ops:
                continue
            pagos = [p for p in self.pagos_ordenados() if p.activo == activo.nombre and p.fecha <= corte]
            resultado.append(Posicion(activo, ops, pagos, corte, self.precios_manuales.get(activo.nombre)))
        return resultado

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

        return {
            "fecha_corte": self.fecha_corte,
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
                 "pagos": [p.a_dict() for p in self.pagos],
                 "precios_manuales": self.precios_manuales}
        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)

    @staticmethod
    def cargar(ruta, fecha_corte=None):
        portafolio = Portafolio(ruta, fecha_corte)
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as archivo:
                datos = json.load(archivo)
            portafolio.operaciones = [Operacion.desde_dict(d) for d in datos.get("operaciones", [])]
            portafolio.pagos = [Pago.desde_dict(d) for d in datos.get("pagos", [])]
            portafolio.precios_manuales = {k: float(v) for k, v in datos.get("precios_manuales", {}).items()}
        return portafolio
