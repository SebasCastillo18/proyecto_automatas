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
# CONFIGURACIÓN DEL GRAFO
# ===============================
G = nx.Graph()

nodos = {
    'A': (4.7110, -74.0721),
    'B': (4.6097, -74.0817),
    'C': (4.6421, -74.0867),
    'D': (4.6550, -74.0830),
    'E': (4.6775, -74.0490),
    'F': (4.7000, -74.0400),
    'G': (4.7400, -74.0300),
    'H': (4.7200, -74.1000),
    'I': (4.6800, -74.1200),
    'J': (4.7600, -74.0600)
}

for nodo, coords in nodos.items():
    G.add_node(nodo, pos=coords)

rutas = [
    ('A', 'B'), ('A', 'C'), ('B', 'D'), ('C', 'E'), ('D', 'E'),
    ('E', 'F'), ('F', 'G'), ('G', 'J'), ('E', 'H'), ('H', 'I'),
    ('I', 'J'), ('C', 'H'), ('B', 'I'), ('D', 'F'), ('A', 'H')
]

for (a, b) in rutas:
    peso = random.randint(1, 3)
    G.add_edge(a, b, weight=peso)

# ===============================
# MAPA INTERACTIVO
# ===============================
def generar_mapa(estado_inicial, estado_final, nombre_archivo="simulacion_ruta_auto.html"):
    inicio = nodos[estado_inicial]
    fin = nodos[estado_final]
    m = folium.Map(location=inicio, zoom_start=12, tiles="CartoDB positron")

    # Todas las rutas en gris claro
    for (a, b, data) in G.edges(data=True):
        loc1, loc2 = nodos[a], nodos[b]
        folium.PolyLine([loc1, loc2], color="#B0BEC5", weight=3, opacity=0.6).add_to(m)
        mid_lat = (loc1[0] + loc2[0]) / 2
        mid_lon = (loc1[1] + loc2[1]) / 2
        folium.Marker(
            location=[mid_lat, mid_lon],
            icon=folium.DivIcon(html=f"<div style='font-size:10pt; color:#37474F'>{data['weight']}</div>")
        ).add_to(m)

    # Ruta óptima en azul degradado
    try:
        ruta_optima = nx.shortest_path(G, source=estado_inicial, target=estado_final, weight="weight")
        peso_total = nx.shortest_path_length(G, source=estado_inicial, target=estado_final, weight="weight")
    except nx.NetworkXNoPath:
        ruta_optima = []
        peso_total = None

    if ruta_optima:
        coords_optima = [nodos[n] for n in ruta_optima]
        folium.PolyLine(coords_optima, color="#007AFF", weight=7, opacity=0.9).add_to(m)

        for n in ruta_optima:
            folium.CircleMarker(
                location=nodos[n],
                radius=7,
                color="#007AFF",
                fill=True,
                fill_color="#007AFF",
                fill_opacity=0.9
            ).add_to(m)

        folium.Marker(inicio, popup=f"Inicio: {estado_inicial}", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(fin, popup=f"Final: {estado_final}", icon=folium.Icon(color="red")).add_to(m)

    m.save(nombre_archivo)
    return ruta_optima, peso_total

# ===============================
# INTERFAZ ESTÉTICA Y MODERNA
# ===============================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 Simulación de Rutas Inteligentes")
        self.root.geometry("1300x850")
        self.root.configure(bg="#F3F6FB")

        # Estilo moderno
        style = ttk.Style()
        style.configure("TLabel", background="#F3F6FB", foreground="#2E3B4E", font=("Segoe UI", 11))
        style.configure("TEntry", font=("Segoe UI", 11))
        style.configure("TFrame", background="#F3F6FB")
        style.configure("TButton", background="#007AFF", foreground="white", font=("Segoe UI", 11, "bold"))

        # Frame principal con scroll
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.canvas = tk.Canvas(main_frame, bg="#F3F6FB", highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll_y.set)
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)
        self.frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Título elegante
        ttk.Label(
            self.frame,
            text="🚀 Simulación de Rutas Óptimas",
            font=("Segoe UI Semibold", 18),
            foreground="#007AFF",
            background="#F3F6FB"
        ).grid(row=0, column=0, columnspan=4, pady=15)

        # Entradas
        ttk.Label(self.frame, text="Estado inicial:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.entry_inicio = ttk.Entry(self.frame, width=5)
        self.entry_inicio.grid(row=1, column=1, pady=5, sticky="w")

        ttk.Label(self.frame, text="Estado final:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.entry_final = ttk.Entry(self.frame, width=5)
        self.entry_final.grid(row=2, column=1, pady=5, sticky="w")

        self.info_label = ttk.Label(self.frame, text="", font=("Segoe UI", 11, "italic"))
        self.info_label.grid(row=3, column=0, columnspan=4, pady=10)

        # Imagen del grafo con fondo claro
        self.grafo_label = tk.Label(self.frame, bg="#F3F6FB")
        self.grafo_label.grid(row=4, column=0, columnspan=4, pady=10)

        # Info del autómata
        self.estados_label = ttk.Label(self.frame, text="", font=("Segoe UI", 10), justify="center")
        self.estados_label.grid(row=5, column=0, columnspan=4, pady=10)

        self.entry_final.bind("<Return>", lambda e: self.actualizar_todo())
        self.actualizar_todo()

    def actualizar_todo(self):
        estado_inicial = self.entry_inicio.get().upper() or "A"
        estado_final = self.entry_final.get().upper() or "J"

        ruta_optima, peso_total = generar_mapa(estado_inicial, estado_final)
        self.mostrar_grafo(ruta_optima)

        conjunto_estados = sorted(list(G.nodes))
        transiciones = [f"δ({a},{b})={data['weight']}" for (a, b, data) in G.edges(data=True)]

        texto_info = (
            f"Estado inicial: {estado_inicial}\n"
            f"Estado final: {estado_final}\n"
            f"Conjunto de estados: {', '.join(conjunto_estados)}\n\n"
            f"Transiciones (peso):\n" + "\n".join(transiciones)
        )

        if ruta_optima:
            self.info_label.config(
                text=f"Ruta óptima: {' → '.join(ruta_optima)} | Peso total: {peso_total}",
                foreground="#007AFF"
            )
        else:
            self.info_label.config(text="⚠️ No hay ruta disponible.", foreground="#C62828")

        self.estados_label.config(text=texto_info)
        threading.Thread(target=lambda: webbrowser.open("file://" + os.path.abspath("simulacion_ruta_auto.html"))).start()

    def mostrar_grafo(self, ruta_optima):
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(G, seed=42)
        weights = nx.get_edge_attributes(G, "weight")

        nx.draw_networkx_nodes(G, pos, node_color="#007AFF", node_size=800, alpha=0.9)
        nx.draw_networkx_labels(G, pos, font_color="white", font_size=12, font_weight="bold")
        nx.draw_networkx_edges(G, pos, width=2, edge_color="#B0BEC5", alpha=0.6)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=weights, font_color="#37474F", font_size=10)

        if ruta_optima:
            edges_optimos = list(zip(ruta_optima[:-1], ruta_optima[1:]))
            nx.draw_networkx_edges(G, pos, edgelist=edges_optimos, width=4, edge_color="#007AFF")

        plt.axis("off")
        buf = BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", facecolor="#F3F6FB")
        buf.seek(0)
        plt.close()
        img = Image.open(buf)
        img = img.resize((720, 520))
        self.tk_img = ImageTk.PhotoImage(img)
        self.grafo_label.config(image=self.tk_img)

# ===============================
# EJECUCIÓN
# ===============================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
