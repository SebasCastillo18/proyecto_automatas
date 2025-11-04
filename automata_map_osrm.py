# automata_map_moderno.py
import folium
import random
import networkx as nx
import tkinter as tk
from tkinter import ttk
from io import BytesIO
from PIL import Image, ImageTk
import threading
import webbrowser
import os
import matplotlib.pyplot as plt

# ===============================
# GRAFO SIMULADO (Medellín, offline)
# ===============================
G = nx.Graph()

# Nodos simulados distribuidos norte-sur y este-oeste (coordenadas plausibles en Medellín)
nodos = {
    'A':  (6.3140, -75.5750),  # Norte
    'B':  (6.3050, -75.5790),
    'C':  (6.2960, -75.5730),
    'D':  (6.2870, -75.5680),
    'E':  (6.2780, -75.5620),
    'F':  (6.2690, -75.5560),  # Media-norte
    'G':  (6.2600, -75.5500),
    'H':  (6.2510, -75.5450),
    'I':  (6.2420, -75.5400),
    'J':  (6.2330, -75.5350),  # Centro-sur
    'K':  (6.2240, -75.5300),
    'L':  (6.2150, -75.5250),
    'M':  (6.2060, -75.5200),
    'N':  (6.1970, -75.5150),
    'O':  (6.1880, -75.5100),  # Sur
    'P':  (6.3000, -75.5600),  # Este-nodos de conexión
    'Q':  (6.2800, -75.5900),
    'R':  (6.2450, -75.5850),
    'S':  (6.2300, -75.5650),
    'T':  (6.2100, -75.5450),
    'U':  (6.1900, -75.5400),
    'V':  (6.1750, -75.5300),
    'W':  (6.1600, -75.5200)
}

for nodo, coords in nodos.items():
    G.add_node(nodo, pos=coords)

# Conexiones lógicas tipo vías por donde pasan autos (malla + diagonales + ramales)
edges = [
    # Columnas norte-sud
    ('A','B'),('B','C'),('C','D'),('D','E'),('E','F'),('F','G'),('G','H'),('H','I'),
    ('I','J'),('J','K'),('K','L'),('L','M'),('M','N'),('N','O'),

    # Ramas est-eo para dar más rutas
    ('A','P'),('P','C'),('P','F'),('Q','B'),('Q','E'),('Q','G'),
    ('R','H'),('R','I'),('R','J'),('S','J'),('S','L'),('T','M'),
    ('U','N'),('V','O'),('W','O'),

    # Diagonales y alternativas (permite múltiples caminos)
    ('B','D'),('C','E'),('D','F'),('E','G'),('F','H'),('G','I'),('H','J'),
    ('I','K'),('J','L'),('K','M'),('L','N'),('M','O'),('N','P'),
    ('O','S'),('P','Q'),('Q','R'),('R','S'),('S','T'),('T','U'),('U','V'),('V','W'),

    # Conexiones largas (simulan avenidas)
    ('A','C'),('C','F'),('F','I'),('I','M'),('M','O'),
    ('B','G'),('G','K'),('K','O'),('P','S'),('Q','T'),('R','U')
]

G.add_edges_from(edges)

# Asignar pesos aleatorios (1-3) a todas las aristas cada vez que se (re)calcula
def randomize_weights():
    for u, v in G.edges():
        G[u][v]['weight'] = random.randint(1, 3)

randomize_weights()

# ===============================
# MAPA INTERACTIVO (satélite claro / positron)
# ===============================
def generar_mapa(estado_inicial, estado_final, nombre_archivo="simulacion_medellin.html"):
    inicio = nodos[estado_inicial]
    fin = nodos[estado_final]

    # Mapa claro y profesional
    m = folium.Map(location=inicio, zoom_start=12, tiles="CartoDB positron")

    # Dibujar TODAS las rutas posibles (líneas grises)
    for (a, b, data) in G.edges(data=True):
        loc1, loc2 = nodos[a], nodos[b]
        folium.PolyLine([loc1, loc2], color="#B0BEC5", weight=3, opacity=0.7).add_to(m)
        # mostrar peso como etiqueta pequeña en la mitad del segmento
        mid = [(loc1[0]+loc2[0])/2, (loc1[1]+loc2[1])/2]
        folium.map.Marker(
            mid,
            icon=folium.DivIcon(
                html=f"""<div style="font-size:10px;color:#455A64;background:rgba(255,255,255,0.0);padding:0px">"""
                     f"{data['weight']}</div>"""
            )
        ).add_to(m)

    # calcular ruta óptima (menor peso)
    try:
        ruta_optima = nx.shortest_path(G, source=estado_inicial, target=estado_final, weight='weight')
        peso_total = nx.shortest_path_length(G, source=estado_inicial, target=estado_final, weight='weight')
    except nx.NetworkXNoPath:
        ruta_optima = []
        peso_total = None

    # Resaltar SOLO la ruta óptima en neón cyan (doble capa para efecto glow)
    if ruta_optima:
        coords = [nodos[n] for n in ruta_optima]
        folium.PolyLine(coords, color="#00e5ff", weight=10, opacity=0.25).add_to(m)  # glow base
        folium.PolyLine(coords, color="#00B8D4", weight=6, opacity=0.95,
                        tooltip=f"Ruta óptima (peso: {peso_total})").add_to(m)

        # marcadores inicio/fin y nodos de la ruta
        folium.Marker(inicio, popup=f"Inicio: {estado_inicial}", icon=folium.Icon(color='green')).add_to(m)
        folium.Marker(fin, popup=f"Fin: {estado_final}", icon=folium.Icon(color='red')).add_to(m)
        for n in ruta_optima:
            folium.CircleMarker(location=nodos[n], radius=6, color="#00B8D4", fill=True, fill_color="#00B8D4").add_to(m)

    m.save(nombre_archivo)
    return ruta_optima, peso_total

# ===============================
# INTERFAZ MODERNA (mejorada pero misma lógica)
# ===============================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulación de Rutas - Medellín (simulado)")
        self.root.geometry("1320x860")
        self.root.configure(bg="#F3F6FB")

        # Estilo
        style = ttk.Style()
        style.configure("TLabel", background="#F3F6FB", foreground="#2E3B4E", font=("Segoe UI", 11))
        style.configure("TEntry", font=("Segoe UI", 11))
        style.configure("TFrame", background="#F3F6FB")
        style.configure("TButton", foreground="white", background="#007AFF", font=("Segoe UI", 11, "bold"))

        # Layout con scroll
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=18, pady=18)

        self.canvas = tk.Canvas(main_frame, bg="#F3F6FB", highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll_y.set)
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)
        self.frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Header
        ttk.Label(self.frame, text="🚗 Simulador de Rutas (Medellín - Simulado)", font=("Segoe UI Semibold", 18),
                  foreground="#007AFF", background="#F3F6FB").grid(row=0, column=0, columnspan=4, pady=(8,18))

        # Inputs
        ttk.Label(self.frame, text="Estado inicial:").grid(row=1, column=0, padx=10, sticky="e")
        self.entry_inicio = ttk.Entry(self.frame, width=6)
        self.entry_inicio.grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(self.frame, text="Estado final:").grid(row=1, column=2, padx=10, sticky="e")
        self.entry_final = ttk.Entry(self.frame, width=6)
        self.entry_final.grid(row=1, column=3, sticky="w", pady=6)

        # Bind Enter
        self.entry_inicio.bind("<Return>", lambda e: self._recalculate())
        self.entry_final.bind("<Return>", lambda e: self._recalculate())

        # Result / info area
        self.info_label = ttk.Label(self.frame, text="", font=("Segoe UI", 12, "italic"))
        self.info_label.grid(row=2, column=0, columnspan=4, pady=(8,12))

        # Large graph image
        self.grafo_label = tk.Label(self.frame, bg="#F3F6FB")
        self.grafo_label.grid(row=3, column=0, columnspan=4, pady=10)

        # Additional automata info (initial, final, set, transitions)
        self.details_label = ttk.Label(self.frame, text="", justify="left", font=("Segoe UI", 10))
        self.details_label.grid(row=4, column=0, columnspan=4, pady=(10,8), padx=10, sticky="w")

        # init view
        self._recalculate()

    def _recalculate(self):
        # new random weights each recalculation
        randomize_weights()

        start = (self.entry_inicio.get().strip().upper() or "A")
        end   = (self.entry_final.get().strip().upper() or "O")

        # validate
        if start not in nodos or end not in nodos:
            self.info_label.config(text="Introduce estados válidos (p. ej.: A, B, C... O).", foreground="#C62828")
            return

        ruta_optima, peso_total = generar_mapa(start, end)
        self._render_graph(ruta_optima)

        # info textual
        conjunto = ", ".join(sorted(list(G.nodes())))
        transiciones = "\n".join([f"δ({u},{v}) = {d['weight']}" for u, v, d in G.edges(data=True)])
        details = (f"Estado inicial: {start}\nEstado final: {end}\nConjunto de estados: {{ {conjunto} }}\n\n"
                   f"Función de transición (pesos):\n{transiciones}")
        self.details_label.config(text=details)

        if ruta_optima:
            self.info_label.config(text=f"Ruta óptima: {' → '.join(ruta_optima)}   |   Peso total: {peso_total}", foreground="#007AFF")
        else:
            self.info_label.config(text="No existe ruta entre esos estados.", foreground="#C62828")

        # open map in browser asynchronously
        threading.Thread(target=lambda: webbrowser.open("file://" + os.path.abspath("simulacion_medellin.html")), daemon=True).start()

    def _render_graph(self, ruta_optima):
        plt.figure(figsize=(9, 7))
        pos = nx.spring_layout(G, seed=42, k=0.35)
        weights = nx.get_edge_attributes(G, 'weight')

        nx.draw_networkx_nodes(G, pos, node_color="#007AFF", node_size=820, alpha=0.95)
        nx.draw_networkx_labels(G, pos, font_color="white", font_size=12, font_weight="bold")
        nx.draw_networkx_edges(G, pos, width=2.0, edge_color="#B0BEC5", alpha=0.6)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=weights, font_color="#37474F", font_size=10)

        if ruta_optima:
            edges_optimos = list(zip(ruta_optima[:-1], ruta_optima[1:]))
            nx.draw_networkx_edges(G, pos, edgelist=edges_optimos, width=4.2, edge_color="#00B8D4")

        plt.axis('off')
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#F3F6FB')
        buf.seek(0)
        plt.close()
        img = Image.open(buf)
        img = img.resize((820, 620))
        self.tk_img = ImageTk.PhotoImage(img)
        self.grafo_label.config(image=self.tk_img)

# ===============================
# EJECUCIÓN
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
