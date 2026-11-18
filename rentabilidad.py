class Rentabilidad:
    """Fórmulas de rentabilidad. Son las mismas que usa el Excel de control."""

    @staticmethod
    def acumulada(ganancia, invertido):
        """Ganancia total / total invertido. Equivale a la celda 'Rentab. acumulada' del Excel."""
        if invertido <= 0:
            return None
        return ganancia / invertido

    @staticmethod
    def efectiva_anual(flujos):
        """Tasa efectiva anual de una lista de (fecha, valor). Equivale a TIR.NO.PER (XIRR) de Excel.

        Resuelve  sum( valor_i / (1 + tasa) ** (dias_i / 365) ) = 0,
        donde dias_i son los días desde la primera fecha.
        Devuelve None si no hay al menos un flujo negativo y uno positivo.
        """
        flujos = [(f, v) for f, v in flujos if v != 0]
        if not any(v < 0 for _, v in flujos) or not any(v > 0 for _, v in flujos):
            return None
        inicio = min(f for f, _ in flujos)
        puntos = [((f - inicio).days / 365.0, v) for f, v in flujos]

        def vpn(tasa):
            return sum(v / (1 + tasa) ** t for t, v in puntos)

        # Búsqueda por bisección: lenta pero siempre converge si la raíz está en el rango.
        bajo, alto = -0.9999, 10.0
        if vpn(bajo) * vpn(alto) > 0:
            return None
        for _ in range(300):
            medio = (bajo + alto) / 2
            if vpn(bajo) * vpn(medio) <= 0:
                alto = medio
            else:
                bajo = medio
            if alto - bajo < 1e-12:
                break
        return (bajo + alto) / 2
