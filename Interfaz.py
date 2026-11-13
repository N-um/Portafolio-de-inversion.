import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta

from activo import Activo
from mercado import Mercado
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


def numero(x):
    """Monto en la moneda del activo (con centavos, para que se vean los dólares)."""
    return f"{x:,.2f}" if x >= 0 else f"-{-x:,.2f}"


def porcentaje(x):
    return "N/A" if x is None else f"{x * 100:,.2f}%"


def color_signo(x):
    return VERDE if x is not None and x >= 0 else ROJO


class Interfaz:
    """Ventana principal con 5 pestañas: Resumen, Operaciones, Dividendos e intereses, Valoración y Valor diario."""

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
        self.tab_diario = tk.Frame(pestanas, bg=FONDO)
        pestanas.add(self.tab_resumen, text="  Resumen  ")
        pestanas.add(self.tab_ops, text="  Operaciones  ")
        pestanas.add(self.tab_pagos, text="  Dividendos e intereses  ")
        pestanas.add(self.tab_valor, text="  Valoración  ")
        pestanas.add(self.tab_diario, text="  Valor diario  ")

        self._armar_resumen()
        self._armar_operaciones()
        self._armar_pagos()
        self._armar_valoracion()
        self._armar_diario()
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

        der = self._tarjeta(medio, "Detalle financiero")
        der.pack(side="left", fill="y", padx=4)
        self.lbl_detalle = tk.Label(der, text="", bg="white", font=("Segoe UI", 10), justify="left")
        self.lbl_detalle.pack(padx=14, pady=(4, 8), anchor="w")

        tk.Label(self.tab_resumen, text="Rendimiento por activo", bg=FONDO, fg=AZUL,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(6, 0))
        marco, self.tabla_resumen = self._tabla(
            self.tab_resumen,
            ("Activo", "Tipo", "Cantidad", "Valor actual", "Peso", "Total invertido",
             "Dividendos / intereses", "Ganancia", "Rent. acum.", "Rent. E.A."),
            (100, 70, 70, 110, 60, 110, 130, 110, 85, 85), alto=6)
        marco.pack(fill="both", expand=True, padx=10, pady=(2, 8))

    def _actualizar_resumen(self):
        r = self.portafolio.resumen()
        trm = f"   ·   TRM {dinero(r['trm'])}" if r["trm"] else "   ·   sin TRM"
        prueba = any(f.startswith("PRUEBA") for f in self.portafolio.mercado.fuentes())
        self.lbl_fecha.config(text=f"Valoración al {r['fecha_corte']:%d/%m/%Y}{trm}"
                                   + ("   ·   ⚠ precios de PRUEBA" if prueba else ""))
        self.kpis["invertido"].config(text=dinero(r["invertido"]))
        self.kpis["valor_actual"].config(text=dinero(r["valor_actual"]))
        self.kpis["ganancia"].config(text=dinero(r["ganancia"]), fg=color_signo(r["ganancia"]))
        self.kpis["rent_acumulada"].config(text=porcentaje(r["rent_acumulada"]),
                                           fg=color_signo(r["rent_acumulada"]))
        self.kpis["rent_ea"].config(text=porcentaje(r["rent_ea"]), fg=color_signo(r["rent_ea"]))
        self.kpis["comisiones"].config(text=dinero(r["comisiones"]))

        self.lbl_detalle.config(text=(
            f"Ganancia no realizada:   {dinero(r['no_realizada'])}\n"
            f"   (valor actual − costo de lo que aún tengo)\n"
            f"Ganancia realizada:   {dinero(r['realizada'])}\n"
            f"   (ventas hechas + dividendos e intereses)\n\n"
            f"Dividendos e intereses:   {dinero(r['ingresos'])}\n"
            f"Ventas netas recibidas:   {dinero(r['ventas'])}\n"
            f"Comisiones pagadas:   {dinero(r['comisiones'])}"))

        self._dibujar_torta(r)
        self._dibujar_barras(r)

        self.tabla_resumen.delete(*self.tabla_resumen.get_children())
        for nombre, a in r["por_activo"].items():
            tag = "pos" if a["ganancia"] >= 0 else "neg"
            self.tabla_resumen.insert("", "end", tags=(tag,), values=(
                nombre, a["tipo"], f"{a['cantidad']:g}", dinero(a["valor"]),
                f"{a['peso'] * 100:.1f}%", dinero(a["compras"]), dinero(a["pagos"]),
                dinero(a["ganancia"]), porcentaje(a["rent"]), porcentaje(a["rent_ea"])))

    def _dibujar_torta(self, r):
        c = self.canvas_torta
        c.delete("all")
        total = r["renta_fija"] + r["renta_variable"]
        if total <= 0:
            c.create_text(125, 85, text="Sin inversiones", fill="#999")
            self.lbl_leyenda.config(text="")
            return
        caja = (65, 10, 185, 130)
        pct_fija = r["renta_fija"] / total
        if pct_fija >= 0.9999 or pct_fija <= 0.0001:
            c.create_oval(*caja, fill=COLOR_FIJA if pct_fija > 0.5 else COLOR_VARIABLE, outline="white")
        else:
            c.create_arc(*caja, start=90, extent=-360 * pct_fija, fill=COLOR_FIJA, outline="white")
            c.create_arc(*caja, start=90 - 360 * pct_fija, extent=-360 * (1 - pct_fija),
                         fill=COLOR_VARIABLE, outline="white")
        c.create_rectangle(10, 142, 22, 154, fill=COLOR_FIJA, outline="")
        c.create_text(28, 148, anchor="w", font=("Segoe UI", 9),
                      text=f"Renta fija  {pct_fija * 100:.1f}%  ({dinero(r['renta_fija'])})")
        c.create_rectangle(10, 158, 22, 170, fill=COLOR_VARIABLE, outline="")
        c.create_text(28, 164, anchor="w", font=("Segoe UI", 9),
                      text=f"Renta variable  {(1 - pct_fija) * 100:.1f}%  ({dinero(r['renta_variable'])})")
        self.lbl_leyenda.config(text="")

    def _dibujar_barras(self, r):
        c = self.canvas_barras
        c.delete("all")
        activos = [(n, a) for n, a in r["por_activo"].items() if a["valor"] > 0]
        if not activos:
            c.create_text(165, 100, text="Sin inversiones", fill="#999")
            return
        activos.sort(key=lambda x: -x[1]["valor"])
        mayor = activos[0][1]["peso"]
        for i, (nombre, a) in enumerate(activos):
            y = 10 + i * 32
            color = Activo.buscar(nombre).color
            c.create_text(4, y + 10, anchor="w", text=nombre, font=("Segoe UI", 9))
            largo = 150 * a["peso"] / mayor if mayor > 0 else 0
            c.create_rectangle(95, y, 95 + largo, y + 20, fill=color, outline="")
            c.create_text(100 + largo, y + 10, anchor="w", font=("Segoe UI", 9, "bold"),
                          text=f"{a['peso'] * 100:.1f}%")

    # ---------- Pestaña Operaciones ----------
    def _armar_operaciones(self):
        form = tk.Frame(self.tab_ops, bg=FONDO)
        form.pack(fill="x", padx=10, pady=(10, 0))
        self.op_fecha = self._campo(form, "Fecha (AAAA-MM-DD)", 0, valor=date.today().isoformat(), ancho=16)
        self.op_activo = self._campo(form, "Activo", 1, self.nombres, ancho=16)
        self.op_activo.bind("<<ComboboxSelected>>", self._al_elegir_activo)
        self.op_fecha.bind("<FocusOut>", self._sugerir_precio)
        self.op_fecha.bind("<Return>", self._sugerir_precio)
        self.op_tipo = self._campo(form, "Operación", 2, Operacion.TIPOS_OPERACION, ancho=10)
        self.op_cantidad = self._campo(form, "Cantidad", 3, valor="1", ancho=8)
        self.op_precio = self._campo(form, "Precio unitario (moneda del activo)", 4, ancho=26)
        tk.Label(form, text=f"Comisión del bróker: {Operacion.TASA_COMISION:.1%} automática",
                 bg=FONDO, fg="#555", font=("Segoe UI", 9)).grid(row=1, column=5, padx=8, sticky="w")

        form2 = tk.Frame(self.tab_ops, bg=FONDO)
        form2.pack(fill="x", padx=10)
        self.op_tasa = self._campo(form2, "Tasa E.A. % (CDT)", 0, valor="0", ancho=16)
        self.op_venc = self._campo(form2, "Vencimiento (CDT)", 1, ancho=16)
        self.lbl_info = tk.Label(form2, text="", bg=FONDO, fg="#555", font=("Segoe UI", 9), justify="left")
        self.lbl_info.grid(row=1, column=2, padx=10, sticky="w")
        ttk.Button(form2, text="Registrar operación", command=self._registrar_operacion
                   ).grid(row=1, column=3, padx=10, pady=(0, 6))
        self.lbl_precio = tk.Label(form2, text="", bg=FONDO, fg=AZUL, font=("Segoe UI", 9), justify="left")
        self.lbl_precio.grid(row=1, column=4, padx=10, sticky="w")
        self._precio_auto = ""

        marco, self.tabla_ops = self._tabla(
            self.tab_ops,
            ("Fecha", "Activo", "Tipo", "Operación", "Cantidad", "Moneda", "Precio", "Comisión", "Flujo de caja"),
            (90, 120, 100, 80, 70, 60, 110, 90, 130), alto=14)
        marco.pack(fill="both", expand=True, padx=10, pady=8)
        ttk.Button(self.tab_ops, text="Eliminar operación seleccionada",
                   command=self._eliminar_operacion).pack(anchor="e", padx=10, pady=(0, 10))
        self._al_elegir_activo()

    def _al_elegir_activo(self, _evento=None):
        activo = Activo.buscar(self.op_activo.get())
        self.lbl_info.config(text=f"{activo.ticker} · {activo.tipo} · {activo.sector} · Moneda: {activo.moneda}\n"
                                  + ("Precio = valor del título; cantidad = 1 si es un solo CDT."
                                     if activo.es_renta_fija else f"Precio de la acción en {activo.moneda}."))
        for campo, vacio in ((self.op_tasa, "0"), (self.op_venc, "")):
            campo.state(["!disabled"])
            if not activo.es_renta_fija:  # las acciones no tienen tasa ni vencimiento
                campo.delete(0, "end")
                campo.insert(0, vacio)
                campo.state(["disabled"])
        self._sugerir_precio()

    def _sugerir_precio(self, _evento=None):
        """Llena el precio con el cierre de mercado de ese día. Se puede cambiar a mano."""
        try:
            fecha = date.fromisoformat(self.op_fecha.get().strip())
            activo = Activo.buscar(self.op_activo.get())
        except ValueError:
            return
        escrito = self.op_precio.get().strip()
        puede_cambiar = escrito in ("", self._precio_auto)  # no borra un precio escrito a mano
        if activo.es_renta_fija:
            self.lbl_precio.config(text="Renta fija: escriba el valor\npor título (no cotiza en Yahoo).")
            if puede_cambiar:
                self.op_precio.delete(0, "end")
                self._precio_auto = ""
            return
        dato = self.portafolio.precio_sugerido(activo.nombre, fecha)
        if dato is None:
            self.lbl_precio.config(text="Sin cierre para esa fecha:\nescríbalo o actualice precios.")
            if puede_cambiar:
                self.op_precio.delete(0, "end")
                self._precio_auto = ""
            return
        fecha_dato, precio, fuente = dato
        cuando = "de ese día" if fecha_dato == fecha else f"del {fecha_dato}"
        self.lbl_precio.config(text=f"Sugerido: cierre {cuando}\n({fuente}). Puede cambiarlo.")
        if puede_cambiar:
            self._precio_auto = f"{precio:.2f}"
            self.op_precio.delete(0, "end")
            self.op_precio.insert(0, self._precio_auto)

    def _registrar_operacion(self):
        try:
            activo = Activo.buscar(self.op_activo.get())
            venc = self.op_venc.get().strip()
            op = Operacion(
                date.fromisoformat(self.op_fecha.get().strip()), activo.tipo, activo.nombre,
                self.op_tipo.get(), float(self.op_cantidad.get()), float(self.op_precio.get()),
                float(self.op_tasa.get() or 0) / 100,
                date.fromisoformat(venc) if venc else None)
            self.portafolio.agregar_operacion(op)
        except ValueError as e:
            messagebox.showerror("Dato inválido", f"Revisa los datos.\n\n{e}")
            return
        self.op_precio.delete(0, "end")
        self._precio_auto = ""
        self.actualizar()
        self._sugerir_precio()

    def _eliminar_operacion(self):
        seleccion = self.tabla_ops.selection()
        if not seleccion:
            messagebox.showinfo("Operaciones", "Primero selecciona una operación de la tabla.")
            return
        if messagebox.askyesno("Eliminar", "¿Eliminar la operación seleccionada?"):
            try:
                self.portafolio.eliminar_operacion(self.ops_en_tabla[seleccion[0]])
            except ValueError as e:  # p. ej. quitar una compra que respalda una venta posterior
                messagebox.showerror("No se puede eliminar", str(e))
                return
            self.actualizar()

    # ---------- Pestaña Pagos ----------
    def _armar_pagos(self):
        form = tk.Frame(self.tab_pagos, bg=FONDO)
        form.pack(fill="x", padx=10, pady=10)
        self.pg_fecha = self._campo(form, "Fecha (AAAA-MM-DD)", 0, valor=date.today().isoformat(), ancho=16)
        self.pg_activo = self._campo(form, "Activo", 1, self.nombres, ancho=16)
        self.pg_tipo = self._campo(form, "Tipo de pago", 2, Pago.TIPOS)
        self.pg_monto = self._campo(form, "Monto recibido (moneda del activo)", 3, ancho=26)
        ttk.Button(form, text="Registrar pago", command=self._registrar_pago
                   ).grid(row=1, column=4, padx=10, pady=(0, 6))

        tk.Label(self.tab_pagos, bg=FONDO, fg="#555", font=("Segoe UI", 9), justify="left",
                 text=("Dividendo: acciones. Interés: CDT (se descuenta del valor causado). Capital: devolución de "
                       "parte del dinero invertido (reduce el valor del título).")).pack(anchor="w", padx=14)
        marco, self.tabla_pagos = self._tabla(
            self.tab_pagos, ("Fecha", "Activo", "Tipo", "Moneda", "Monto"), (110, 200, 110, 80, 140), alto=14)
        marco.pack(fill="both", expand=True, padx=10, pady=8)
        ttk.Button(self.tab_pagos, text="Eliminar pago seleccionado",
                   command=self._eliminar_pago).pack(anchor="e", padx=10, pady=(0, 10))

    def _registrar_pago(self):
        try:
            pago = Pago(date.fromisoformat(self.pg_fecha.get().strip()), self.pg_activo.get(),
                        self.pg_tipo.get(), float(self.pg_monto.get()))
            self.portafolio.agregar_pago(pago)
        except ValueError as e:
            messagebox.showerror("Dato inválido", f"Revisa los datos.\n\n{e}")
            return
        self.pg_monto.delete(0, "end")
        self.actualizar()

    def _eliminar_pago(self):
        seleccion = self.tabla_pagos.selection()
        if not seleccion:
            messagebox.showinfo("Pagos", "Primero selecciona un pago de la tabla.")
            return
        if messagebox.askyesno("Eliminar", "¿Eliminar el pago seleccionado?"):
            self.portafolio.eliminar_pago(self.pagos_en_tabla[seleccion[0]])
            self.actualizar()

    # ---------- Pestaña Valoración ----------
    def _armar_valoracion(self):
        tk.Label(self.tab_valor, bg=FONDO, justify="left", font=("Segoe UI", 9), fg="#555",
                 text=("Acciones: último cierre de yfinance × TRM del día (o un precio manual en su moneda). "
                       "CDT, bonos y TES: valor causado a su tasa E.A. (no cotizan en Yahoo Finance).")
                 ).pack(anchor="w", padx=10, pady=(10, 4))
        marco, self.tabla_val = self._tabla(
            self.tab_valor,
            ("Activo", "Cantidad", "Costo", "Precio actual", "Origen", "Valor actual",
             "Ganancia no realizada", "Rent. %", "Tasa E.A.", "Vence", "Días"),
            (95, 65, 105, 100, 80, 110, 130, 70, 70, 90, 55), alto=10)
        marco.pack(fill="both", expand=True, padx=10, pady=4)

        form = tk.Frame(self.tab_valor, bg=FONDO)
        form.pack(fill="x", padx=10, pady=10)
        self.val_precio = self._campo(form, "Nuevo precio de mercado", 0, ancho=22)
        ttk.Button(form, text="Actualizar precio", command=self._actualizar_precio
                   ).grid(row=1, column=1, padx=10, pady=(0, 6))
        ttk.Button(form, text="Volver a valoración automática", command=self._quitar_precio
                   ).grid(row=1, column=2, padx=4, pady=(0, 6))
        ttk.Button(form, text="Actualizar precios de mercado (yfinance + TRM)", command=self._actualizar_mercado
                   ).grid(row=1, column=3, padx=(30, 4), pady=(0, 6))

    def _activo_seleccionado(self):
        seleccion = self.tabla_val.selection()
        if not seleccion:
            messagebox.showinfo("Valoración", "Primero selecciona un activo de la tabla.")
            return None
        return str(self.tabla_val.item(seleccion[0])["values"][0])

    def _actualizar_precio(self):
        nombre = self._activo_seleccionado()
        if nombre is None:
            return
        try:
            self.portafolio.actualizar_precio(nombre, float(self.val_precio.get()))
        except ValueError as e:
            messagebox.showerror("Dato inválido", f"Revisa el precio.\n\n{e}")
            return
        self.val_precio.delete(0, "end")
        self.actualizar()

    def _quitar_precio(self):
        nombre = self._activo_seleccionado()
        if nombre is not None:
            self.portafolio.quitar_precio_manual(nombre)
            self.actualizar()

    def _actualizar_mercado(self):
        self.root.config(cursor="watch")
        self.root.update()
        try:
            mensaje = self.portafolio.actualizar_mercado()
        except Exception as e:  # sin internet, yfinance no instalado, etc.
            messagebox.showerror("Mercado", f"No se pudieron descargar los datos.\n\n{e}\n\n"
                                            "Revise la conexión e instale yfinance: pip install yfinance")
            return
        finally:
            self.root.config(cursor="")
        messagebox.showinfo("Mercado", mensaje)
        self.actualizar()
        self._sugerir_precio()

    # ---------- Pestaña Valor diario ----------
    def _armar_diario(self):
        form = tk.Frame(self.tab_diario, bg=FONDO)
        form.pack(fill="x", padx=10, pady=(10, 0))
        hoy = self.portafolio.fecha_corte
        self.dia_desde = self._campo(form, "Desde (AAAA-MM-DD)", 0, valor=(hoy - timedelta(days=365)).isoformat(), ancho=16)
        self.dia_hasta = self._campo(form, "Hasta (AAAA-MM-DD)", 1, valor=hoy.isoformat(), ancho=16)
        ttk.Button(form, text="Calcular", command=self._calcular_diario).grid(row=1, column=2, padx=10, pady=(0, 6))
        ttk.Button(form, text="Exportar CSV", command=self._exportar_diario).grid(row=1, column=3, padx=4, pady=(0, 6))
        tk.Label(form, bg=FONDO, fg="#555", font=("Segoe UI", 9), justify="left",
                 text="Cada día: acciones = último cierre × cantidad × TRM del día;\nrenta fija = valor causado a su tasa E.A."
                 ).grid(row=1, column=4, padx=10, sticky="w")
        tarjeta = self._tarjeta(self.tab_diario, "Valor del portafolio (COP)")
        tarjeta.pack(fill="x", padx=10, pady=6)
        self.canvas_diario = tk.Canvas(tarjeta, width=1020, height=230, bg="white", highlightthickness=0)
        self.canvas_diario.pack(padx=8, pady=(0, 8))
        marco, self.tabla_diario = self._tabla(
            self.tab_diario, ("Fecha", "TRM", "Renta variable", "Renta fija", "Total"), (110, 100, 160, 160, 170), alto=8)
        marco.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.dias = []

    def _calcular_diario(self):
        try:
            desde = date.fromisoformat(self.dia_desde.get().strip())
            hasta = date.fromisoformat(self.dia_hasta.get().strip())
            self.dias = self.portafolio.valor_diario(desde, hasta)
        except ValueError as e:
            messagebox.showerror("Valor diario", f"Revisa las fechas.\n\n{e}")
            return
        self.tabla_diario.delete(*self.tabla_diario.get_children())
        for d in self.dias:
            self.tabla_diario.insert("", "end", values=(
                d["fecha"].isoformat(), dinero(d["trm"]) if d["trm"] else "-", dinero(d["renta_variable"]),
                dinero(d["renta_fija"]), dinero(d["total"])))
        self._dibujar_diario()

    def _dibujar_diario(self):
        c = self.canvas_diario
        c.delete("all")
        if not self.dias:
            return
        ancho, alto, izq, abajo = 1020, 230, 90, 30
        mayor = max(d["total"] for d in self.dias) or 1
        n = max(len(self.dias) - 1, 1)
        def punto(i, v):
            return izq + (ancho - izq - 20) * i / n, 15 + (alto - abajo - 15) * (1 - v / mayor)
        for k in range(5):  # líneas guía
            v = mayor * k / 4
            y = punto(0, v)[1]
            c.create_line(izq, y, ancho - 20, y, fill="#EEF1F6")
            c.create_text(izq - 6, y, anchor="e", text=dinero(v), font=("Segoe UI", 8), fill="#777")
        for clave, color, grosor in (("renta_fija", COLOR_FIJA, 1), ("renta_variable", COLOR_VARIABLE, 1), ("total", AZUL, 2)):
            puntos = [coord for i, d in enumerate(self.dias) for coord in punto(i, d[clave])]
            if len(puntos) >= 4:
                c.create_line(*puntos, fill=color, width=grosor)
        for i in (0, len(self.dias) // 2, len(self.dias) - 1):
            x = punto(i, 0)[0]
            c.create_text(x, alto - 12, text=self.dias[i]["fecha"].isoformat(), font=("Segoe UI", 8), fill="#777")
        for j, (texto, color) in enumerate((("Total", AZUL), ("Renta fija", COLOR_FIJA), ("Renta variable", COLOR_VARIABLE))):
            c.create_rectangle(izq + 10 + j * 120, 4, izq + 22 + j * 120, 12, fill=color, outline="")
            c.create_text(izq + 26 + j * 120, 8, anchor="w", text=texto, font=("Segoe UI", 8))

    def _exportar_diario(self):
        if not self.dias:
            messagebox.showinfo("Valor diario", "Primero presiona Calcular.")
            return
        ruta = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="valor_diario.csv")
        if not ruta:
            return
        nombres = [a.nombre for a in self.activos]
        with open(ruta, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["fecha", "trm"] + nombres + ["renta_variable", "renta_fija", "total"])
            for d in self.dias:
                escritor.writerow([d["fecha"].isoformat(), d["trm"]] + [d["por_activo"].get(n, 0) for n in nombres]
                                  + [d["renta_variable"], d["renta_fija"], d["total"]])
        messagebox.showinfo("Valor diario", f"Guardado en {ruta}")

    # ---------- Refrescar todo ----------
    def actualizar(self):
        for tabla in (self.tabla_ops, self.tabla_pagos, self.tabla_val):
            tabla.delete(*tabla.get_children())
        self.ops_en_tabla, self.pagos_en_tabla = {}, {}

        for op in self.portafolio.operaciones_ordenadas():
            fila = self.tabla_ops.insert("", "end", tags=("pos" if op.flujo_caja >= 0 else "neg",), values=(
                op.fecha.isoformat(), op.activo, op.tipo_activo, op.tipo_operacion, f"{op.cantidad:g}",
                Activo.buscar(op.activo).moneda, numero(op.precio), numero(op.comision), numero(op.flujo_caja)))
            self.ops_en_tabla[fila] = op

        for pago in self.portafolio.pagos_ordenados():
            fila = self.tabla_pagos.insert("", "end", values=(
                pago.fecha.isoformat(), pago.activo, pago.tipo, Activo.buscar(pago.activo).moneda, numero(pago.monto)))
            self.pagos_en_tabla[fila] = pago

        for v in self.portafolio.valoracion():
            self.tabla_val.insert("", "end", tags=("pos" if v["no_realizada"] >= 0 else "neg",), values=(
                v["activo"], f"{v['cantidad']:g}", dinero(v["costo"]), dinero(v["precio"]), v["origen"],
                dinero(v["valor"]), dinero(v["no_realizada"]), porcentaje(v["rent"]),
                porcentaje(v["tasa"]), v["vencimiento"].isoformat() if v["vencimiento"] else "-",
                "-" if v["dias"] is None else v["dias"]))

        self._actualizar_resumen()
