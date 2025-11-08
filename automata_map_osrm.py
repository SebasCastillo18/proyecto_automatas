import os
import tkinter as tk
from tkinter import ttk, Canvas, Scrollbar
import folium
from folium.plugins import AntPath
from folium.features import CustomIcon
import random
import networkx as nx
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation

# Mapa legible nombre por nodo
lugares_medellin = {
    "A": "Estadio Atanasio Girardot",
    "B": "Parque de los Pies Descalzos",
    "C": "Plaza Botero",
    "D": "Museo de Antioquia",
    "E": "Comuna 13",
    "F": "Parque Explora",
    "G": "Jardín Botánico",
    "H": "Pueblito Paisa",
    "I": "Cerro Nutibara",
    "J": "Mercado Minorista",
    "K": "Biblioteca Pública Piloto",
    "L": "Parque de San Antonio",
    "M": "Parque de las Luces",
    "N": "Parque Arví",
    "O": "Plaza de Cisneros",
    "P": "Museo Casa de la Memoria",
    "Q": "La 70",
    "R": "Catedral Metropolitana",
    "S": "Teatro Pablo Tobón Uribe",
    "T": "Parque de la Presidenta",
    "U": "Parque Bolívar",
    "V": "Museo El Castillo",
    "W": "Archivo Histórico Medellín",
    "X": "Universidad de Antioquia",
    "Y": "Mirador de Las Palmas",
    "Z": "Parque Norte",
    "AA": "Barrio Laureles",
    "BB": "Barrio Envigado"
}

coordenadas_puntos = {
    "A": (6.2442, -75.5812), "B": (6.2460, -75.5760), "C": (6.2547, -75.5711),
    "D": (6.2514, -75.5816), "E": (6.2208, -75.5850), "F": (6.2620, -75.5600),
    "G": (6.2420, -75.5650), "H": (6.2630, -75.5605), "I": (6.2730, -75.5740),
    "J": (6.2480, -75.5810), "K": (6.2700, -75.5700), "L": (6.2590, -75.5700),
    "M": (6.2580, -75.5720), "N": (6.2890, -75.5680), "O": (6.2480, -75.5900),
    "P": (6.2640, -75.5800), "Q": (6.2300, -75.5900), "R": (6.2530, -75.5805),
    "S": (6.2595, -75.5640), "T": (6.2625, -75.5750), "U": (6.2600, -75.5660),
    "V": (6.2540, -75.5660), "W": (6.2500, -75.5770), "X": (6.2470, -75.5790),
    "Y": (6.2700, -75.5600), "Z": (6.2800, -75.5700),
    "AA": (6.2400, -75.5700), "BB": (6.2350, -75.5800),
    "CC": (6.2700, -75.5900), "DD": (6.2800, -75.6000), "EE": (6.2600, -75.6000)
}

def generar_grafo_medellin():
    G = nx.Graph()
    for nodo, coord in coordenadas_puntos.items():
        G.add_node(nodo, pos=coord)
    conexiones = [
        ("A", "B"), ("A", "F"), ("B", "F"), ("B", "H"), ("F", "G"), ("F", "E"),
        ("E", "C"), ("C", "D"), ("C", "I"), ("I", "J"), ("H", "J"), ("G", "E"),
        ("H", "I"), ("J", "K"), ("K", "L"), ("L", "M"), ("M", "N"), ("N", "O"),
        ("O", "P"), ("P", "Q"), ("Q", "R"), ("R", "S"), ("S", "T"), ("T", "U"),
        ("U", "V"), ("V", "W"), ("W", "X"), ("X", "Y"), ("Y", "Z"), ("Z", "A"),
        ("Z", "AA"), ("AA", "BB"), ("BB", "CC"), ("CC", "DD"), ("DD", "EE"),
        ("EE", "P"), ("BB", "Q"), ("AA", "G"), ("CC", "N"), ("DD", "O"),
        ("EE", "M"), ("AA", "X"), ("BB", "Y"), ("CC", "V"), ("DD", "U"),
    ]
    for n1, n2 in conexiones:
        peso = random.randint(1, 3)  # ajustado según solicitud
        G.add_edge(n1, n2, weight=peso, blocked=False)
    return G

def generar_mapa_waze(start, end, G):
    posiciones = nx.get_node_attributes(G, "pos")
    try:
        caminos = list(nx.all_simple_paths(G, source=start, target=end))
    except nx.NetworkXNoPath:
        caminos = []
    if not caminos:
        mapa = folium.Map(location=(6.2442, -75.5812), zoom_start=14)
        folium.Marker(location=(6.2442, -75.5812), popup="No hay rutas posibles").add_to(mapa)
        mapa.save("simulacion_waze.html")
        file_path = os.path.abspath("simulacion_waze.html")
        webbrowser.open(f"file://{file_path}")
        return [], 0, mapa
    caminos_disp = [p for p in caminos if all(not G[u][v].get('blocked', False) for u,v in zip(p[:-1], p[1:]))]
    if not caminos_disp:
        mapa = folium.Map(location=(6.2442, -75.5812), zoom_start=14)
        folium.Marker(location=(6.2442, -75.5812), popup="No hay rutas disponibles por bloqueo").add_to(mapa)
        mapa.save("simulacion_waze.html")
        file_path = os.path.abspath("simulacion_waze.html")
        webbrowser.open(f"file://{file_path}")
        return [], 0, mapa
    ruta = min(caminos_disp, key=lambda p: sum(G[u][v]['weight'] for u,v in zip(p[:-1], p[1:])))
    peso = sum(G[u][v]['weight'] for u,v in zip(ruta[:-1], ruta[1:]))

    mapa = folium.Map(location=posiciones[start], zoom_start=14)
    for path in caminos_disp:
        pts = [posiciones[n] for n in path]
        folium.PolyLine(pts, color='gray', weight=3, opacity=0.4).add_to(mapa)
    coords = [posiciones[n] for n in ruta]
    folium.PolyLine(coords, color="#00FFFF", weight=8, opacity=0.9).add_to(mapa)
    AntPath(locations=coords, dash_array=[20, 30], delay=300, color='#00FFFF', pulse_color='#005757', weight=9, opacity=0.9).add_to(mapa)
    for n, (lat, lon) in coordenadas_puntos.items():
        folium.Marker(location=(lat, lon), popup=n, icon=folium.Icon(color="blue", icon="info-sign")).add_to(mapa)
    for u,v,d in G.edges(data=True):
        if d.get('blocked', False):
            folium.PolyLine([posiciones[u], posiciones[v]], color='red', weight=5, opacity=0.7, dash_array='5').add_to(mapa)
    mapa.save("simulacion_waze.html")
    file_path = os.path.abspath("simulacion_waze.html")
    webbrowser.open(f"file://{file_path}")
    return ruta, peso, mapa

class GrafoAnimado:
    def __init__(self, frame, on_edge_click):
        self.fig, self.ax = plt.subplots(figsize=(20,16))
        self.ax.set_facecolor("#0E1E25")
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=15, pady=15)
        self.anim = None
        self.G = None
        self.pos = None
        self.ruta_optima = None
        self.on_edge_click = on_edge_click
        self.canvas.mpl_connect("button_press_event", self._handle_click)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)


    def _handle_click(self, event):
        if self.G is None or self.pos is None or event.xdata is None or event.ydata is None:
            return
        tol = 0.0005
        x_click, y_click = event.xdata, event.ydata
        for u,v in self.G.edges():
            x1,y1 = self.pos[u]
            x2,y2 = self.pos[v]
            dx, dy = x2 - x1, y2 - y1
            if dx==dy==0:
                continue
            t = max(0, min(1, ((x_click - x1)*dx + (y_click - y1)*dy) / (dx*dx + dy*dy)))
            proj_x, proj_y = x1 + t*dx, y1 + t*dy
            dist = ((proj_x - x_click)**2 + (proj_y - y_click)**2)**0.5
            if dist < tol:
                self.on_edge_click(u,v)
                break


    def animar(self, G, ruta_optima):
        self.G = G
        self.ruta_optima = ruta_optima
        self.pos = nx.get_node_attributes(G, "pos")
        edge_labels = nx.get_edge_attributes(G, "weight")


        grados = dict(G.degree())
        def update(frame):
            self.ax.clear()
            node_colors = []
            node_sizes = []
            for node in G.nodes():
                if ruta_optima and node == ruta_optima[frame]:
                    node_colors.append("#00FFFF")
                    node_sizes.append(2000 + 40*grados[node])
                else:
                    node_colors.append("#00B8D4")
                    node_sizes.append(1500 + 30*grados[node])


            nx.draw_networkx_nodes(G, self.pos, node_color=node_colors, node_size=node_sizes, alpha=0.9, ax=self.ax)
            nx.draw_networkx_labels(G, self.pos, font_color="white", font_size=18, font_weight="bold", ax=self.ax)


            blocked_edges = [(u,v) for u,v,d in G.edges(data=True) if d.get("blocked", False)]
            nx.draw_networkx_edges(G, self.pos, edgelist=blocked_edges, width=8, edge_color="red", style="dotted", alpha=0.7, ax=self.ax)


            normal_edges = [(u,v) for u,v,d in G.edges(data=True) if not d.get("blocked", False)]
            nx.draw_networkx_edges(G, self.pos, edgelist=normal_edges, width=5, edge_color="#555555", alpha=0.6, ax=self.ax)


            nx.draw_networkx_edge_labels(G, self.pos, edge_labels=edge_labels, font_color="#FFD700", font_size=20, font_weight="bold", bbox=dict(facecolor="#1B263B", edgecolor="none", alpha=0.9), ax=self.ax)


            if frame < len(ruta_optima) - 1:
                tramo = [(ruta_optima[frame], ruta_optima[frame + 1])]
                nx.draw_networkx_edges(G, self.pos, edgelist=tramo, width=12, edge_color="#00FFFF", alpha=0.9, ax=self.ax)

            self.ax.set_axis_off()
            self.fig.tight_layout()


        if self.anim:
            self.anim.event_source.stop()
        self.anim = animation.FuncAnimation(self.fig, update, frames=len(ruta_optima),
                                            interval=900, repeat=True)
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
        self.start_combo = ttk.Combobox(self.frame, values=[f"{k} - {v}" for k,v in lugares_medellin.items()], width=35, state="readonly")
        self.start_combo.grid(row=1, column=1, padx=10, pady=10)
        self.start_combo.set("A - Estadio Atanasio Girardot")
        ttk.Label(self.frame, text="Estado final:").grid(row=2, column=0, sticky="e", padx=10, pady=10)
        self.end_combo = ttk.Combobox(self.frame, values=[f"{k} - {v}" for k,v in lugares_medellin.items()], width=35, state="readonly")
        self.end_combo.grid(row=2, column=1, padx=10, pady=10)
        self.end_combo.set("J - Mercado Minorista")

        self.start_combo.bind("<<ComboboxSelected>>", lambda e: self._on_combo_change())
        self.end_combo.bind("<<ComboboxSelected>>", lambda e: self._on_combo_change())

        self.resultado_label = ttk.Label(self.frame, text="", style="Result.TLabel", justify="center", wraplength=1000)
        self.resultado_label.grid(row=3, column=0, columnspan=3, pady=20)

        self.grafo_container = ttk.Frame(self.frame)
        self.grafo_container.grid(row=4, column=0, columnspan=3, pady=20)

        self.grafo_animado = GrafoAnimado(self.grafo_container, self.toggle_arista)

        self.pos = None
        self.G = None
        self.ruta_optima = None
        self.start = None
        self.end = None

        self._recalculate()

    def _on_combo_change(self):
        self.start = self.start_combo.get().split(" - ")[0]
        self.end = self.end_combo.get().split(" - ")[0]
        self._recalculate()

    def toggle_arista(self, u, v):
        if self.G[u][v].get("blocked", False):
            self.G[u][v]["blocked"] = False
        else:
            self.G[u][v]["blocked"] = True

        caminos_posibles = list(nx.all_simple_paths(self.G, source=self.start, target=self.end))
        caminos_posibles = [
            p for p in caminos_posibles if all(not self.G[u][v].get("blocked", False) for u, v in zip(p[:-1], p[1:]))
        ]

        if not caminos_posibles:
            self.resultado_label.config(text=f"No hay rutas disponibles tras bloquear la ruta {u} - {v}.")
            self.grafo_animado.animar(self.G, [])
            return

        self.ruta_optima = min(
            caminos_posibles,
            key=lambda p: sum(self.G[u][v]["weight"] for u, v in zip(p[:-1], p[1:])),
        )
        peso_total = sum(self.G[u][v]["weight"] for u, v in zip(self.ruta_optima[:-1], self.ruta_optima[1:]))

        estados = ", ".join(sorted(self.G.nodes()))
        alfabeto = "{1, 2, 3}"

        transiciones = []
        for i in range(len(self.ruta_optima) - 1):
            peso = self.G[self.ruta_optima[i]][self.ruta_optima[i + 1]]["weight"]
            transiciones.append(f"δ({self.ruta_optima[i]}, {peso}) → {self.ruta_optima[i + 1]}")
        funcion_transicion = "\n".join(transiciones)

        self.resultado_label.config(
            text=(
                f"Estado inicial: {self.start}   |   Estado final: {self.end}\n"
                f"Conjunto de estados: {{{estados}}}\n"
                f"Alfabeto Σ: {alfabeto}\n\n"
                f"Ruta óptima: {' → '.join(self.ruta_optima)}   |   Peso total: {peso_total}\n\n"
                f"Función de transición δ:\n{funcion_transicion}"
            )
        )

        self.grafo_animado.animar(self.G, self.ruta_optima)

        posiciones = self.pos if self.pos else coordenadas_puntos
        mapa = folium.Map(location=posiciones[self.start], zoom_start=14, tiles="OpenStreetMap")

        car_icon_url = 'https://cdn-icons-png.flaticon.com/512/743/743922.png'
        from folium.features import CustomIcon

        if self.ruta_optima:
            coord_inicio = [posiciones[self.ruta_optima[0]][0], posiciones[self.ruta_optima[0]][1]]
            car_icon = CustomIcon(car_icon_url, icon_size=(40, 40))
            folium.Marker(location=coord_inicio, icon=car_icon, popup="Inicio ruta").add_to(mapa)

        for nombre, (lat, lon) in coordenadas_puntos.items():
            folium.Marker(location=(lat, lon), popup=nombre, icon=folium.Icon(color="blue", icon="info-sign")).add_to(mapa)

        for path in caminos_posibles:
            puntos = [posiciones[n] for n in path]
            folium.PolyLine(puntos, color="gray", weight=3, opacity=0.4).add_to(mapa)

        coords = [posiciones[n] for n in self.ruta_optima]
        folium.PolyLine(coords, color="#00FFFF", weight=8, opacity=0.9).add_to(mapa)

        AntPath(
            locations=coords,
            dash_array=[20, 30],
            delay=300,
            color="#00FFFF",
            pulse_color="#005757",
            weight=9,
            opacity=0.9,
        ).add_to(mapa)

        for u_, v_, d_ in self.G.edges(data=True):
            if d_.get("blocked", False):
                folium.PolyLine(
                    [posiciones[u_], posiciones[v_]],
                    color="red",
                    weight=5,
                    opacity=0.7,
                    dash_array="5",
                ).add_to(mapa)

        for nodo, (lat, lon) in posiciones.items():
            folium.CircleMarker(
                location=(lat, lon),
                radius=8,
                color="white" if nodo not in self.ruta_optima else "#00FFFF",
                fill=True,
                fill_color="#00FFFF" if nodo in self.ruta_optima else "gray",
                fill_opacity=1.0,
                popup=f"Estado {nodo}",
            ).add_to(mapa)

        mapa.save("simulacion_waze.html")
        import os
        file_path = os.path.abspath("simulacion_waze.html")
        webbrowser.open(f"file://{file_path}")

    def _recalculate(self):
        self.start = self.start_combo.get().split(" - ")[0]
        self.end = self.end_combo.get().split(" - ")[0]

        self.G = generar_grafo_medellin()
        self.ruta_optima, peso_total, _ = generar_mapa_waze(self.start, self.end, self.G)
        self.pos = coordenadas_puntos

        estados = ", ".join(sorted(self.G.nodes()))
        alfabeto = "{1, 2, 3}"

        if self.ruta_optima:
            transiciones = []
            for i in range(len(self.ruta_optima) - 1):
                peso = self.G[self.ruta_optima[i]][self.ruta_optima[i + 1]]["weight"]
                transiciones.append(f"δ({self.ruta_optima[i]}, {peso}) → {self.ruta_optima[i + 1]}")
            funcion_transicion = "\n".join(transiciones)

            self.resultado_label.config(
                text=(
                    f"Estado inicial: {self.start}   |   Estado final: {self.end}\n"
                    f"Conjunto de estados: {{{estados}}}\n"
                    f"Alfabeto Σ: {alfabeto}\n\n"
                    f"Ruta óptima: {' → '.join(self.ruta_optima)}   |   Peso total: {peso_total}\n\n"
                    f"Función de transición δ:\n{funcion_transicion}"
                )
            )
        else:
            self.resultado_label.config(text=f"No hay rutas disponibles desde {self.start} hasta {self.end}.")

        self.grafo_animado.animar(self.G, self.ruta_optima)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
