import tkinter as tk
from tkinter import ttk, Canvas, Scrollbar
import folium
import random
import networkx as nx
from folium.plugins import AntPath
from io import BytesIO
import webbrowser
import os
from PIL import Image, ImageTk
import matplotlib.pyplot as plt

# --- Generar grafo con pesos aleatorios ---
def generar_grafo_medellin():
    G = nx.Graph()

    puntos = {
        "A": (6.2442, -75.5812),
        "B": (6.2600, -75.5780),
        "C": (6.2700, -75.5650),
        "D": (6.2400, -75.6000),
        "E": (6.2100, -75.5770),
        "F": (6.3000, -75.5550),
        "G": (6.3200, -75.5900),
        "H": (6.1800, -75.5900),
        "I": (6.1500, -75.5800),
        "J": (6.3500, -75.5700)
    }

    for nodo, coord in puntos.items():
        G.add_node(nodo, pos=coord)

    conexiones = [
        ("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"),
        ("C", "E"), ("E", "H"), ("H", "I"), ("B", "F"),
        ("F", "J"), ("D", "G"), ("G", "J"), ("E", "G"),
        ("A", "E"), ("F", "H"), ("B", "C"), ("D", "E"), ("G", "H")
    ]

    for n1, n2 in conexiones:
        peso = random.randint(1, 3)
        G.add_edge(n1, n2, weight=peso)

    return G


# --- Generar mapa tipo Waze ---
def generar_mapa_waze(start, end):
    G = generar_grafo_medellin()
    posiciones = nx.get_node_attributes(G, "pos")

    try:
        caminos_posibles = list(nx.all_simple_paths(G, source=start, target=end))
    except nx.NetworkXNoPath:
        caminos_posibles = []

    if not caminos_posibles:
        mapa = folium.Map(location=(6.2442, -75.5812), zoom_start=12, tiles="CartoDB positron")
        folium.Marker(location=(6.2442, -75.5812),
                      popup="No hay rutas posibles desde el estado inicial.").add_to(mapa)
        mapa.save("simulacion_waze.html")
        return G, [], 0

    ruta_optima = min(caminos_posibles, key=lambda p: sum(G[u][v]['weight'] for u, v in zip(p[:-1], p[1:])))
    peso_total = sum(G[u][v]['weight'] for u, v in zip(ruta_optima[:-1], ruta_optima[1:]))

    mapa = folium.Map(location=posiciones[start], zoom_start=12, tiles="CartoDB positron")

    # Todas las rutas posibles (gris)
    for path in caminos_posibles:
        puntos = [posiciones[n] for n in path]
        folium.PolyLine(puntos, color="gray", weight=3, opacity=0.4).add_to(mapa)

    # Ruta óptima animada (neón)
    puntos_optimos = [posiciones[n] for n in ruta_optima]
    AntPath(
        puntos_optimos,
        color="#00FFFF",
        weight=6,
        opacity=0.9,
        dash_array=[10, 20],
        delay=600,
        pulse_color="#00FFFF"
    ).add_to(mapa)

    # Nodos
    for nodo, (lat, lon) in posiciones.items():
        folium.CircleMarker(
            location=(lat, lon),
            radius=8,
            color="white" if nodo not in ruta_optima else "#00FFFF",
            fill=True,
            fill_color="#00FFFF" if nodo in ruta_optima else "gray",
            fill_opacity=1.0,
            popup=f"Estado {nodo}"
        ).add_to(mapa)

    mapa.save("simulacion_waze.html")

    return G, ruta_optima, peso_total


# --- Mostrar grafo visual con pesos y caminos ---
def mostrar_grafo(G, ruta_optima):
    pos = nx.spring_layout(G, seed=42, k=0.45)
    plt.figure(figsize=(13, 10))
    plt.gca().set_facecolor("#0E1E25")

    # Dibujar nodos grandes
    nx.draw_networkx_nodes(G, pos, node_color="#00B8D4", node_size=1100, alpha=0.9)
    nx.draw_networkx_labels(G, pos, font_color="white", font_size=14, font_weight="bold")

    # Dibujar todas las aristas
    edge_colors = []
    for u, v in G.edges():
        if ruta_optima and (u in ruta_optima and v in ruta_optima and abs(ruta_optima.index(u) - ruta_optima.index(v)) == 1):
            edge_colors.append("#00FFFF")
        else:
            edge_colors.append("#7A7A7A")

    nx.draw_networkx_edges(G, pos, width=3, edge_color=edge_colors, alpha=0.8)

    # Pesos en color amarillo neón
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, font_color="#FFD700",
        font_size=15, font_weight="bold",
        bbox=dict(facecolor="#1B263B", edgecolor="none", alpha=0.6)
    )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig("grafo_ruta.png", facecolor="#0E1E25", dpi=160)
    plt.close()


# --- Interfaz principal ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 Simulador de Rutas Inteligente - Estilo Waze")
        self.root.geometry("1380x980")
        self.root.configure(bg="#0E1E25")

        # Canvas con scroll
        self.canvas = Canvas(root, bg="#0E1E25", highlightthickness=0)
        self.scroll_y = Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.frame = ttk.Frame(self.canvas, padding=40, style="Main.TFrame")

        self.canvas.configure(yscrollcommand=self.scroll_y.set)
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Estilos
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Main.TFrame", background="#0E1E25")
        style.configure("TLabel", background="#0E1E25", foreground="white", font=("Segoe UI Semibold", 13))
        style.configure("TEntry", font=("Segoe UI", 12), padding=6)
        style.configure("Title.TLabel", font=("Segoe UI Bold", 24), foreground="#00E5FF", background="#0E1E25")
        style.configure("Result.TLabel", font=("Segoe UI", 12), foreground="#00FFFF", background="#0E1E25")

        # Título
        ttk.Label(self.frame, text="Simulador de Rutas Inteligente", style="Title.TLabel").grid(row=0, column=0, columnspan=3, pady=(0, 30))

        # Entradas
        ttk.Label(self.frame, text="Estado inicial:").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.start_entry = ttk.Entry(self.frame, width=6)
        self.start_entry.grid(row=1, column=1, padx=10, pady=10)
        self.start_entry.insert(0, "A")

        ttk.Label(self.frame, text="Estado final:").grid(row=2, column=0, sticky="e", padx=10, pady=10)
        self.end_entry = ttk.Entry(self.frame, width=6)
        self.end_entry.grid(row=2, column=1, padx=10, pady=10)
        self.end_entry.insert(0, "J")

        self.end_entry.bind("<Return>", lambda e: self._recalculate())

        # Resultados
        self.resultado_label = ttk.Label(self.frame, text="", style="Result.TLabel", justify="center", wraplength=1000)
        self.resultado_label.grid(row=3, column=0, columnspan=3, pady=20)

        # Imagen grafo
        self.grafo_container = tk.Frame(self.frame, bg="#13232F", bd=0, highlightthickness=0)
        self.grafo_container.grid(row=4, column=0, columnspan=3, pady=20)
        self.image_label = ttk.Label(self.grafo_container, background="#13232F")
        self.image_label.pack(padx=15, pady=15)

    def _recalculate(self):
        start = self.start_entry.get().strip().upper()
        end = self.end_entry.get().strip().upper()

        G, ruta_optima, peso_total = generar_mapa_waze(start, end)
        mostrar_grafo(G, ruta_optima)

        estados = ", ".join(sorted(G.nodes()))
        alfabeto = "{1, 2, 3}"

        # Función de transición δ
        if ruta_optima:
            transiciones = []
            for i in range(len(ruta_optima) - 1):
                peso = G[ruta_optima[i]][ruta_optima[i+1]]['weight']
                transiciones.append(f"δ({ruta_optima[i]}, {peso}) → {ruta_optima[i+1]}")
            funcion_transicion = "\n".join(transiciones)

            self.resultado_label.config(
                text=f"Estado inicial: {start}   |   Estado final: {end}\n"
                     f"Conjunto de estados: {{{estados}}}\n"
                     f"Alfabeto Σ: {alfabeto}\n\n"
                     f"Ruta óptima: {' → '.join(ruta_optima)}   |   Peso total: {peso_total}\n\n"
                     f"Función de transición δ:\n{funcion_transicion}"
            )
        else:
            self.resultado_label.config(
                text=f"No hay rutas disponibles desde {start} hasta {end}."
            )

        img = Image.open("grafo_ruta.png")
        img = img.resize((1100, 800), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk

        webbrowser.open("simulacion_waze.html")


# --- Ejecutar ---
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
