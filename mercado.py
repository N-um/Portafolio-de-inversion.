import bisect
import csv
import json
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta


class Mercado:
    """Historial de precios de mercado y de la TRM, guardado en un CSV: fecha, serie, valor, fuente.

    - serie "TRM": pesos por dólar (oficial, datos.gov.co / Superintendencia Financiera).
    - serie = ticker de Yahoo (p. ej. "NKE"): precio de cierre en la moneda del activo.
    El valor de una serie en una fecha es el último dato registrado en esa fecha o antes
    (los fines de semana y festivos se usa el último cierre). Es la misma regla de la hoja
    "Mercado" del Excel de control.
    """

    TRM = "TRM"
    MANUAL = "Manual"
    URL_TRM = "https://www.datos.gov.co/resource/32sa-8pi3.json"

    def __init__(self, ruta=None):
        self.ruta = ruta
        self._series = {}  # serie -> {fecha: (valor, fuente)}
        self._indice = {}  # serie -> fechas ordenadas (para buscar rápido)

    # ---------- Consultas ----------
    def dato(self, serie, fecha):
        """(fecha_del_dato, valor, fuente) del último dato con fecha <= fecha, o None si no hay."""
        puntos = self._series.get(serie, {})
        if serie not in self._indice:
            self._indice[serie] = sorted(puntos)
        fechas = self._indice[serie]
        posicion = bisect.bisect_right(fechas, fecha)
        if posicion == 0:
            return None
        ultima = fechas[posicion - 1]
        valor, fuente = puntos[ultima]
        return ultima, valor, fuente

    def trm(self, fecha):
        d = self.dato(Mercado.TRM, fecha)
        if d is None:
            raise ValueError(f"No hay TRM para el {fecha}. Use 'Actualizar precios de mercado'.")
        return d[1]

    def fuentes(self):
        return sorted({fuente for puntos in self._series.values() for _, fuente in puntos.values()})

    def filas(self):
        """Todas las filas ordenadas por serie y fecha (para el CSV y el Excel)."""
        return [(f, s, v, fu) for s in sorted(self._series)
                for f, (v, fu) in sorted(self._series[s].items())]

    # ---------- Cambios ----------
    def agregar(self, serie, fecha, valor, fuente):
        if valor <= 0:
            raise ValueError("El precio debe ser mayor que cero.")
        self._series.setdefault(serie, {})[fecha] = (float(valor), fuente)
        self._indice.pop(serie, None)

    def quitar_manuales(self, serie):
        puntos = self._series.get(serie, {})
        for f in [f for f, (_, fu) in puntos.items() if fu == Mercado.MANUAL]:
            del puntos[f]
        self._indice.pop(serie, None)

    def _reemplazar_serie(self, serie, nuevos, fuente):
        """Cambia los datos descargados de una serie y conserva los precios manuales."""
        manuales = {f: p for f, p in self._series.get(serie, {}).items() if p[1] == Mercado.MANUAL}
        self._series[serie] = {f: (v, fuente) for f, v in nuevos.items()}
        self._series[serie].update(manuales)
        self._indice.pop(serie, None)

    # ---------- Descargas ----------
    def descargar_trm(self, inicio, fin):
        """TRM oficial (datos.gov.co). Si falla, usa el dólar de Yahoo (COP=X) como respaldo."""
        try:
            consulta = urllib.parse.urlencode({
                "$select": "valor,vigenciadesde",
                "$where": f"vigenciahasta >= '{inicio}T00:00:00' AND vigenciadesde <= '{fin}T00:00:00'",
                "$order": "vigenciadesde", "$limit": 50000})
            with urllib.request.urlopen(f"{Mercado.URL_TRM}?{consulta}", timeout=30) as respuesta:
                registros = json.loads(respuesta.read().decode("utf-8"))
            nuevos = {datetime.fromisoformat(r["vigenciadesde"][:10]).date(): float(r["valor"])
                      for r in registros}
            if not nuevos:
                raise ValueError("datos.gov.co no devolvió datos")
            self._reemplazar_serie(Mercado.TRM, nuevos, "datos.gov.co")
            return "TRM oficial (datos.gov.co)"
        except Exception:  # sin internet o servicio caído: respaldo con Yahoo
            nuevos = self._cierres_yahoo(["COP=X"], inicio, fin).get("COP=X", {})
            if not nuevos:
                raise ValueError("No se pudo descargar la TRM (datos.gov.co ni Yahoo).")
            self._reemplazar_serie(Mercado.TRM, nuevos, "yfinance COP=X")
            return "TRM de respaldo (Yahoo COP=X)"

    def descargar_precios(self, tickers, inicio, fin):
        cierres = self._cierres_yahoo(tickers, inicio, fin)
        for ticker in [t for t in tickers if not cierres.get(t)]:  # un reintento, de a uno
            cierres.update(self._cierres_yahoo([ticker], inicio, fin))
        faltan = [t for t in tickers if not cierres.get(t)]
        for ticker, nuevos in cierres.items():
            if nuevos:
                self._reemplazar_serie(ticker, nuevos, "yfinance")
        return faltan

    @staticmethod
    def _cierres_yahoo(tickers, inicio, fin):
        """Precio de cierre SIN ajustar (los dividendos se registran aparte como pagos)."""
        import yfinance as yf  # se importa aquí: solo hace falta para descargar
        datos = yf.download(tickers, start=inicio.isoformat(), end=(fin + timedelta(days=1)).isoformat(),
                            auto_adjust=False, progress=False,
                            threads=False)  # en paralelo, Windows puede dar "database is locked"
        if datos is None or datos.empty:
            return {}
        cierres = datos["Close"]
        if not hasattr(cierres, "columns"):  # un solo ticker en versiones viejas de yfinance
            cierres = cierres.to_frame(tickers[0])
        resultado = {}
        for ticker in cierres.columns:
            serie = cierres[ticker].dropna()
            resultado[str(ticker)] = {i.date(): float(v) for i, v in serie.items() if float(v) > 0}
        return resultado

    # ---------- Archivo ----------
    def guardar(self):
        if not self.ruta:
            return
        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(self.ruta, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["fecha", "serie", "valor", "fuente"])
            for f, s, v, fu in self.filas():
                escritor.writerow([f.isoformat(), s, repr(v), fu])

    @staticmethod
    def cargar(ruta):
        mercado = Mercado(ruta)
        if ruta and os.path.exists(ruta):
            with open(ruta, newline="", encoding="utf-8") as archivo:
                for fila in csv.DictReader(archivo):
                    mercado.agregar(fila["serie"], date.fromisoformat(fila["fecha"]),
                                    float(fila["valor"]), fila["fuente"])
        return mercado
