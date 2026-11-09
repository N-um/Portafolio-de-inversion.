import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from activo import Activo
from operacion import Operacion
from pago import Pago
from portafolio import Portafolio

AZUL = "#1F3A5F"
FONDO = "#F3F5F9"
BORDE = "#D0D6E0"
VERDE = "#1B7F3B"
ROJO = "#C0392B"
COLOR_FIJA = "#2E86AB"
COLOR_VARIABLE = "#F18F01"

def dinero(x):
    return f"${x:,.0f}" if x >= 0 else f"-${-x:,.0f}"


def porcentaje(x):
    return "N/A" if x is None else f"{x * 100:,.2f}%"


def color_signo(x):
    return VERDE if x is not None and x >= 0 else ROJO


class Interfaz:
    """Ventana principal con 4 pestañas: Resumen, Operaciones, Dividendos e intereses y Valoración."""

    def __init__(self, portafolio: Portafolio):
        self.portafolio = portafolio
        self.activos = Activo.catalogo()
        self.nombres = [a.nombre for a in self.activos]
        self.ops_en_tabla = {}    # id de fila -> Operacion
        self.pagos_en_tabla = {}  # id de fila -> Pago

        self.root = tk.Tk()
        self.root.title("Seguimiento de Portafolio de Inversión")
        self.root.geometry("1080x790")
        self.root.configure(bg=FONDO)
        self._estilos()

        encabezado = tk.Frame(self.root, bg=AZUL)
        encabezado.pack(fill="x")
        tk.Label(encabezado, text="Seguimiento de Portafolio de Inversión", bg=AZUL, fg="white",
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=16, pady=12)
        self.lbl_fecha = tk.Label(encabezado, text="", bg=AZUL, fg="#BFD0E8", font=("Segoe UI", 10))
        self.lbl_fecha.pack(side="right", padx=16)

        pestanas = ttk.Notebook(self.root)
        pestanas.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_resumen = tk.Frame(pestanas, bg=FONDO)
        self.tab_ops = tk.Frame(pestanas, bg=FONDO)
        self.tab_pagos = tk.Frame(pestanas, bg=FONDO)
        self.tab_valor = tk.Frame(pestanas, bg=FONDO)
        pestanas.add(self.tab_resumen, text="  Resumen  ")
        pestanas.add(self.tab_ops, text="  Operaciones  ")
        pestanas.add(self.tab_pagos, text="  Dividendos e intereses  ")
        pestanas.add(self.tab_valor, text="  Valoración  ")

        self._armar_resumen()
        self._armar_operaciones()
        self._armar_pagos()
        self._armar_valoracion()
        self.actualizar()
        self.root.update_idletasks()
        self.root.lift()

    def ejecutar(self):
        self.root.after(200, self.root.update)  # fuerza el redibujado en macOS
        self.root.mainloop()

    # ---------- Utilidades de diseño ----------
    def _estilos(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Treeview", rowheight=24, font=("Segoe UI", 10))
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                         background=AZUL, foreground="white")
        estilo.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(10, 5))

    def _tabla(self, padre, columnas, anchos, alto=8):
        marco = tk.Frame(padre, bg=FONDO)
        tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=alto)
        for col, ancho in zip(columnas, anchos):
            tabla.heading(col, text=col)
            tabla.column(col, width=ancho, anchor="center")
        tabla.tag_configure("pos", foreground=VERDE)
        tabla.tag_configure("neg", foreground=ROJO)
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return marco, tabla

    def _campo(self, padre, texto, columna, valores=None, valor="", ancho=14):
        tk.Label(padre, text=texto, bg=FONDO, font=("Segoe UI", 9)).grid(
            row=0, column=columna, sticky="w", padx=4)
        if valores:
            widget = ttk.Combobox(padre, values=valores, state="readonly", width=ancho - 2)
            widget.set(valores[0])
        else:
            widget = ttk.Entry(padre, width=ancho)
            widget.insert(0, valor)
        widget.grid(row=1, column=columna, padx=4, pady=(0, 6))
        return widget

    def _tarjeta(self, padre, titulo):
        marco = tk.Frame(padre, bg="white", highlightbackground=BORDE, highlightthickness=1)
        tk.Label(marco, text=titulo, bg="white", fg=AZUL, font=("Segoe UI", 11, "bold")).pack(pady=(8, 2))
        return marco

    # ---------- Pestaña Resumen ----------
    def _armar_resumen(self):
        self.kpis = {}
        fila = tk.Frame(self.tab_resumen, bg=FONDO)
        fila.pack(fill="x", padx=6, pady=(10, 4))
        for i, (clave, titulo) in enumerate([("invertido", "Total invertido"),
                                             ("valor_actual", "Valor actual"),
                                             ("ganancia", "Ganancia / pérdida"),
                                             ("rent_acumulada", "Rentab. acumulada"),
                                             ("rent_ea", "Rentab. efectiva anual"),
                                             ("comisiones", "Comisiones pagadas")]):
            tarjeta = tk.Frame(fila, bg="white", highlightbackground=BORDE, highlightthickness=1)
            tarjeta.grid(row=0, column=i, padx=4, sticky="nsew")
            fila.columnconfigure(i, weight=1)
            tk.Label(tarjeta, text=titulo, bg="white", fg="#666", font=("Segoe UI", 9)).pack(pady=(8, 0))
            valor = tk.Label(tarjeta, text="-", bg="white", fg=AZUL, font=("Segoe UI", 14, "bold"))
            valor.pack(pady=(0, 8), padx=6)
            self.kpis[clave] = valor

        medio = tk.Frame(self.tab_resumen, bg=FONDO)
        medio.pack(fill="x", padx=6, pady=4)

        izq = self._tarjeta(medio, "Renta fija vs. renta variable")
        izq.pack(side="left", fill="y", padx=4)
        self.canvas_torta = tk.Canvas(izq, width=250, height=170, bg="white", highlightthickness=0)
        self.canvas_torta.pack(padx=8)
        self.lbl_leyenda = tk.Label(izq, text="", bg="white", font=("Segoe UI", 9), justify="left")
        self.lbl_leyenda.pack(pady=(0, 8))

        centro = self._tarjeta(medio, "Distribución por activo")
        centro.pack(side="left", fill="both", expand=True, padx=4)
        self.canvas_barras = tk.Canvas(centro, width=330, height=200, bg="white", highlightthickness=0)
        self.canvas_barras.pack(padx=8, pady=(0, 8))
