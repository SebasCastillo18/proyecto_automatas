import tkinter as tk
from tkinter import ttk, Canvas, Scrollbar
import folium
import random
import networkx as nx
import webbrowser
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation


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


def generar_mapa_waze(start, end):
    G = generar_grafo_medellin()
    posiciones = nx.get_node_attributes(G, "pos")
    try:
        caminos_posibles = list(nx.all_simple_paths(G, source=start, target=end))
    except nx.NetworkXNoPath:
        caminos_posibles = []
    if not caminos_posibles:
        mapa = folium.Map(location=(6.2442, -75.5812), zoom_start=12, tiles="CartoDB positron")
        folium.Marker(location=(6.2442, -75.5812), popup="No hay rutas posibles desde el estado inicial.").add_to(mapa)
        mapa.save("simulacion_waze.html")
        return G, [], 0
    ruta_optima = min(caminos_posibles, key=lambda p: sum(G[u][v]['weight'] for u, v in zip(p[:-1], p[1:])))
    peso_total = sum(G[u][v]['weight'] for u, v in zip(ruta_optima[:-1], ruta_optima[1:]))
    mapa = folium.Map(location=posiciones[start], zoom_start=12, tiles="CartoDB positron")
    for path in caminos_posibles:
        puntos = [posiciones[n] for n in path]
        folium.PolyLine(puntos, color="gray", weight=3, opacity=0.4).add_to(mapa)
    coords = [posiciones[n] for n in ruta_optima]
    folium.PolyLine(coords, color="#00FFFF", weight=8, opacity=0.9).add_to(mapa)
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


class GrafoAnimado:
    def __init__(self, frame, on_edge_click):
        self.fig, self.ax = plt.subplots(figsize=(13, 10))
        self.ax.set_facecolor("#0E1E25")
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(padx=15, pady=15)
        self.anim = None
        self.G = None
        self.pos = None
        self.ruta_optima = None
        self.on_edge_click = on_edge_click
        self.canvas.mpl_connect("button_press_event", self._handle_click)

    def _handle_click(self, event):
        if self.G is None or self.pos is None:
            return
        x_click, y_click = event.xdata, event.ydata
        if x_click is None or y_click is None:
            return
        tol = 0.05
        for u, v in self.G.edges():
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            dx, dy = x2 - x1, y2 - y1
            if dx == dy == 0:
                continue
            t = max(0, min(1, ((x_click - x1)*dx + (y_click - y1)*dy)/(dx*dx + dy*dy)))
            proj_x, proj_y = x1 + t*dx, y1 + t*dy
            dist = ((proj_x - x_click)**2 + (proj_y - y_click)**2)**0.5
            if dist < tol:
                self.on_edge_click(u, v)
                break

    def animar(self, G, ruta_optima):
        self.G = G
        self.ruta_optima = ruta_optima
        if self.pos is None:
            self.pos = nx.spring_layout(G, seed=42, k=0.45)
        edge_labels = nx.get_edge_attributes(G, "weight")

        def update(frame):
            self.ax.clear()
            nx.draw_networkx_nodes(G, self.pos, node_color="#00B8D4", node_size=1100, alpha=0.9, ax=self.ax)
            nx.draw_networkx_labels(G, self.pos, font_color="white", font_size=14, font_weight="bold", ax=self.ax)

            blocked_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("blocked", False)]
            nx.draw_networkx_edges(G, self.pos, edgelist=blocked_edges, width=4, edge_color="red", style="dotted", alpha=0.7, ax=self.ax)
            normal_edges = [(u, v) for u, v, d in G.edges(data=True) if not d.get("blocked", False)]
            nx.draw_networkx_edges(G, self.pos, edgelist=normal_edges, width=2, edge_color="#555555", alpha=0.4, ax=self.ax)

            nx.draw_networkx_edge_labels(
                G, self.pos, edge_labels=edge_labels, font_color="#FFD700",
                font_size=15, font_weight="bold",
                bbox=dict(facecolor="#1B263B", edgecolor="none", alpha=0.6), ax=self.ax
            )

            if frame < len(ruta_optima) - 1:
                tramo = [(ruta_optima[frame], ruta_optima[frame + 1])]
                nx.draw_networkx_edges(G, self.pos, edgelist=tramo, width=6, edge_color="#00FFFF", alpha=0.9, ax=self.ax)
            self.ax.set_axis_off()
            self.fig.tight_layout()

        if self.anim:
            self.anim.event_source.stop()
        self.anim = animation.FuncAnimation(self.fig, update, frames=len(ruta_optima), interval=800, repeat=True)
        self.canvas.draw()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 Simulador de Rutas Inteligente - Estilo Waze")
        self.root.geometry("1380x980")
        self.root.configure(bg="#0E1E25")

        self.canvas = Canvas(root, bg="#0E1E25", highlightthickness=0)
        self.scroll_y = Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.frame = ttk.Frame(self.canvas, padding=40, style="Main.TFrame")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Main.TFrame", background="#0E1E25")
        style.configure("TLabel", background="#0E1E25", foreground="white", font=("Segoe UI Semibold", 13))
        style.configure("TEntry", font=("Segoe UI", 12), padding=6)
        style.configure("Title.TLabel", font=("Segoe UI Bold", 24), foreground="#00E5FF", background="#0E1E25")
        style.configure("Result.TLabel", font=("Segoe UI", 12), foreground="#00FFFF", background="#0E1E25")

        ttk.Label(self.frame, text="Simulador de Rutas Inteligente", style="Title.TLabel").grid(row=0, column=0, columnspan=3, pady=(0, 30))
        ttk.Label(self.frame, text="Estado inicial:").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        self.start_entry = ttk.Entry(self.frame, width=6)
        self.start_entry.grid(row=1, column=1, padx=10, pady=10)
        self.start_entry.insert(0, "A")
        ttk.Label(self.frame, text="Estado final:").grid(row=2, column=0, sticky="e", padx=10, pady=10)
        self.end_entry = ttk.Entry(self.frame, width=6)
        self.end_entry.grid(row=2, column=1, padx=10, pady=10)
        self.end_entry.insert(0, "J")
        self.end_entry.bind("<Return>", lambda e: self._recalculate())

        self.resultado_label = ttk.Label(self.frame, text="", style="Result.TLabel", justify="center", wraplength=1000)
        self.resultado_label.grid(row=3, column=0, columnspan=3, pady=20)

        self.grafo_container = ttk.Frame(self.frame)
        self.grafo_container.grid(row=4, column=0, columnspan=3, pady=20)

        self.grafo_animado = GrafoAnimado(self.grafo_container, self.bloquear_arista)
        self.pos = None
        self.G = None
        self.ruta_optima = None
        self.start = None
        self.end = None

    def bloquear_arista(self, u, v):
        if not self.G[u][v].get("blocked", False):
            self.G[u][v]["blocked"] = True

        caminos_posibles = list(nx.all_simple_paths(self.G, source=self.start, target=self.end))
        caminos_posibles = [p for p in caminos_posibles if all(not self.G[u][v].get("blocked", False) for u, v in zip(p[:-1], p[1:]))]

        if not caminos_posibles:
            self.resultado_label.config(text=f"No hay rutas disponibles tras bloquear la ruta {u} - {v}.")
            self.grafo_animado.animar(self.G, [])
            return

        self.ruta_optima = min(caminos_posibles, key=lambda p: sum(self.G[u][v]['weight'] for u, v in zip(p[:-1], p[1:])))
        peso_total = sum(self.G[u][v]['weight'] for u, v in zip(self.ruta_optima[:-1], self.ruta_optima[1:]))

        estados = ", ".join(sorted(self.G.nodes()))
        alfabeto = "{1, 2, 3}"

        transiciones = []
        for i in range(len(self.ruta_optima) - 1):
            peso = self.G[self.ruta_optima[i]][self.ruta_optima[i + 1]]['weight']
            transiciones.append(f"δ({self.ruta_optima[i]}, {peso}) → {self.ruta_optima[i+1]}")
        funcion_transicion = "\n".join(transiciones)

        self.resultado_label.config(
            text=f"Estado inicial: {self.start}   |   Estado final: {self.end}\n"
                 f"Conjunto de estados: {{{estados}}}\n"
                 f"Alfabeto Σ: {alfabeto}\n\n"
                 f"Ruta óptima: {' → '.join(self.ruta_optima)}   |   Peso total: {peso_total}\n\n"
                 f"Función de transición δ:\n{funcion_transicion}"
        )

        self.grafo_animado.animar(self.G, self.ruta_optima)

        posiciones = self.pos if self.pos else nx.spring_layout(self.G, seed=42, k=0.45)
        self.pos = posiciones
        mapa = folium.Map(location=posiciones[self.start], zoom_start=12, tiles="CartoDB positron")

        for path in caminos_posibles:
            puntos = [posiciones[n] for n in path]
            folium.PolyLine(puntos, color="gray", weight=3, opacity=0.4).add_to(mapa)

        coords = [posiciones[n] for n in self.ruta_optima]
        folium.PolyLine(coords, color="#00FFFF", weight=8, opacity=0.9).add_to(mapa)

        for u_, v_, d_ in self.G.edges(data=True):
            if d_.get("blocked", False):
                folium.PolyLine([posiciones[u_], posiciones[v_]], color="red", weight=5, opacity=0.7, dash_array='5').add_to(mapa)

        for nodo, (lat, lon) in posiciones.items():
            folium.CircleMarker(
                location=(lat, lon),
                radius=8,
                color="white" if nodo not in self.ruta_optima else "#00FFFF",
                fill=True,
                fill_color="#00FFFF" if nodo in self.ruta_optima else "gray",
                fill_opacity=1.0,
                popup=f"Estado {nodo}"
            ).add_to(mapa)

        mapa.save("simulacion_waze.html")
        webbrowser.open("simulacion_waze.html")

    def _recalculate(self):
        self.start = self.start_entry.get().strip().upper()
        self.end = self.end_entry.get().strip().upper()
        self.G, self.ruta_optima, peso_total = generar_mapa_waze(self.start, self.end)
        self.pos = nx.spring_layout(self.G, seed=42, k=0.45)

        estados = ", ".join(sorted(self.G.nodes()))
        alfabeto = "{1, 2, 3}"

        if self.ruta_optima:
            transiciones = []
            for i in range(len(self.ruta_optima) - 1):
                peso = self.G[self.ruta_optima[i]][self.ruta_optima[i + 1]]['weight']
                transiciones.append(f"δ({self.ruta_optima[i]}, {peso}) → {self.ruta_optima[i+1]}")
            funcion_transicion = "\n".join(transiciones)

            self.resultado_label.config(
                text=f"Estado inicial: {self.start}   |   Estado final: {self.end}\n"
                     f"Conjunto de estados: {{{estados}}}\n"
                     f"Alfabeto Σ: {alfabeto}\n\n"
                     f"Ruta óptima: {' → '.join(self.ruta_optima)}   |   Peso total: {peso_total}\n\n"
                     f"Función de transición δ:\n{funcion_transicion}"
            )
        else:
            self.resultado_label.config(text=f"No hay rutas disponibles desde {self.start} hasta {self.end}.")

        self.grafo_animado.animar(self.G, self.ruta_optima)

        mapa = folium.Map(location=self.pos[self.start], zoom_start=12, tiles="CartoDB positron")

        for path in nx.all_simple_paths(self.G, source=self.start, target=self.end):
            puntos = [self.pos[n] for n in path]
            folium.PolyLine(puntos, color="gray", weight=3, opacity=0.4).add_to(mapa)

        coords = [self.pos[n] for n in self.ruta_optima]
        folium.PolyLine(coords, color="#00FFFF", weight=8, opacity=0.9).add_to(mapa)

        for u_, v_, d_ in self.G.edges(data=True):
            if d_.get("blocked", False):
                folium.PolyLine([self.pos[u_], self.pos[v_]], color="red", weight=5, opacity=0.7, dash_array='5').add_to(mapa)

        for nodo, (lat, lon) in self.pos.items():
            folium.CircleMarker(
                location=(lat, lon),
                radius=8,
                color="white" if nodo not in self.ruta_optima else "#00FFFF",
                fill=True,
                fill_color="#00FFFF" if nodo in self.ruta_optima else "gray",
                fill_opacity=1.0,
                popup=f"Estado {nodo}"
            ).add_to(mapa)

        mapa.save("simulacion_waze.html")
        webbrowser.open("simulacion_waze.html")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
