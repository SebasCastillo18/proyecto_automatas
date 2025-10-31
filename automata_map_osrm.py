import customtkinter as ctk
import networkx as nx
import matplotlib.pyplot as plt
import threading
import time
import folium
import webbrowser
import os
from io import BytesIO
from PIL import Image

# ---------------------- CONFIGURACIÓN INICIAL ----------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

INITIAL_STATE = "A"
FINAL_STATES = {"E"}

# Grafo con pesos (minutos)
G = nx.DiGraph()
edges = [
    ("A", "B", 4),
    ("A", "C", 2),
    ("B", "C", 1),
    ("B", "D", 5),
    ("C", "D", 8),
    ("C", "E", 10),
    ("D", "E", 2)
]
for u, v, w in edges:
    G.add_edge(u, v, weight=w)

# Coordenadas simuladas (lat, lon)
coords = {
    "A": (6.2442, -75.5812),
    "B": (6.2500, -75.5600),
    "C": (6.2600, -75.5700),
    "D": (6.2700, -75.5900),
    "E": (6.2800, -75.6000)
}

# ---------------------- INTERFAZ PRINCIPAL ----------------------

class AutomataApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Rutas con Autómata - Profesional 🚗")
        self.geometry("1050x700")

        self.G = G
        self.pos = nx.spring_layout(self.G, seed=42)
        self._create_ui()

    # ---------------------- INTERFAZ ----------------------
    def _create_ui(self):
        title = ctk.CTkLabel(self, text="🚦 Simulador de Rutas Inteligentes", font=("Arial", 26, "bold"))
        title.pack(pady=10)

        info_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=15)
        info_frame.pack(pady=15, padx=10, fill="x")

        ctk.CTkLabel(info_frame, text="Estado inicial:", font=("Arial", 14)).grid(row=0, column=0, padx=10, pady=10)
        self.entry_start = ctk.CTkEntry(info_frame, placeholder_text="Ej: A", width=100)
        self.entry_start.grid(row=0, column=1, padx=5, pady=10)

        ctk.CTkLabel(info_frame, text="Estado final:", font=("Arial", 14)).grid(row=0, column=2, padx=10, pady=10)
        self.entry_end = ctk.CTkEntry(info_frame, placeholder_text="Ej: E", width=100)
        self.entry_end.grid(row=0, column=3, padx=5, pady=10)

        self.entry_end.bind("<Return>", lambda e: self._simulate_route())

        self.graph_label = ctk.CTkLabel(self, text="")
        self.graph_label.pack(pady=15)

        self._draw_graph()

    # ---------------------- GRAFO ----------------------
    def _draw_graph(self, path_edges=None):
        if threading.current_thread() is not threading.main_thread():
            self.after(0, lambda: self._draw_graph(path_edges))
            return

        plt.figure(figsize=(5, 4))
        plt.axis("off")

        edge_colors = []
        for (u, v) in self.G.edges():
            if path_edges and (u, v) in path_edges:
                edge_colors.append("#facc15")  # Ruta óptima
            else:
                edge_colors.append("#94a3b8")

        node_colors = []
        for n in self.G.nodes():
            if n in FINAL_STATES:
                node_colors.append("#16a34a")
            elif n == INITIAL_STATE:
                node_colors.append("#2563eb")
            else:
                node_colors.append("#60a5fa")

        nx.draw_networkx(
            self.G, pos=self.pos,
            node_color=node_colors,
            edge_color=edge_colors,
            node_size=600,
            with_labels=True,
            arrows=True
        )

        edge_labels = {(u, v): f"{self.G[u][v]['weight']} min" for u, v in self.G.edges()}
        nx.draw_networkx_edge_labels(self.G, pos=self.pos, edge_labels=edge_labels, font_size=8)

        buf = BytesIO()
        plt.savefig(buf, format="png", transparent=True)
        plt.close()
        buf.seek(0)
        img = Image.open(buf)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 400))
        self.graph_label.configure(image=ctk_img)
        self.graph_label.image = ctk_img

    # ---------------------- SIMULACIÓN ----------------------
    def _simulate_route(self):
        start = self.entry_start.get().strip().upper()
        end = self.entry_end.get().strip().upper()

        if start not in self.G.nodes or end not in self.G.nodes:
            ctk.CTkMessagebox(title="Error", message="Estados no válidos.")
            return

        try:
            path = nx.dijkstra_path(self.G, source=start, target=end, weight="weight")
            path_edges = list(zip(path[:-1], path[1:]))
            self._draw_graph(path_edges)
            threading.Thread(target=self._animate_car, args=(path,), daemon=True).start()
        except nx.NetworkXNoPath:
            ctk.CTkMessagebox(title="Sin conexión", message="No existe ruta entre los estados seleccionados.")

    # ---------------------- ANIMACIÓN CON MOVIMIENTO REAL ----------------------
    def _animate_car(self, path):
        m = folium.Map(location=coords[path[0]], zoom_start=14, tiles="CartoDB Positron")

        # Todos los caminos posibles
        for (u, v) in self.G.edges():
            line_coords = [coords[u], coords[v]]
            weight = self.G[u][v]['weight']
            midpoint = ((coords[u][0] + coords[v][0]) / 2, (coords[u][1] + coords[v][1]) / 2)
            folium.PolyLine(line_coords, color="gray", weight=2, opacity=0.5).add_to(m)
            folium.map.Marker(
                location=midpoint,
                icon=folium.DivIcon(html=f"<div style='font-size:10px;color:#f8fafc'>{weight} min</div>")
            ).add_to(m)

        # Ruta óptima resaltada
        route_coords = [coords[n] for n in path]
        folium.PolyLine(route_coords, color="orange", weight=6, opacity=0.9).add_to(m)

        # Nodos
        for node, (lat, lon) in coords.items():
            folium.CircleMarker(location=(lat, lon),
                                radius=7,
                                color="#3b82f6" if node not in FINAL_STATES else "#16a34a",
                                fill=True, fill_color="#3b82f6",
                                popup=f"Estado {node}").add_to(m)

        # Animación del coche en tiempo real (HTML + JS)
        car_lat, car_lon = coords[path[0]]
        js_positions = []
        for i in range(len(path) - 1):
            lat1, lon1 = coords[path[i]]
            lat2, lon2 = coords[path[i + 1]]
            steps = 30
            for j in range(steps):
                lat = lat1 + (lat2 - lat1) * (j / steps)
                lon = lon1 + (lon2 - lon1) * (j / steps)
                js_positions.append([lat, lon])

        # JavaScript de animación
        js_code = f"""
        <script>
        var carIcon = L.icon({{
            iconUrl: 'https://cdn-icons-png.flaticon.com/512/743/743131.png',
            iconSize: [35, 35]
        }});
        var car = L.marker([{car_lat}, {car_lon}], {{icon: carIcon}}).addTo({{_map}});
        var path = {js_positions};
        let i = 0;
        function moveCar() {{
            if (i < path.length) {{
                car.setLatLng(path[i]);
                i++;
                setTimeout(moveCar, 150);
            }}
        }}
        moveCar();
        </script>
        """

        m.get_root().html.add_child(folium.Element(js_code))

        map_path = "simulacion_ruta_animada.html"
        m.save(map_path)
        webbrowser.open("file://" + os.path.abspath(map_path))

# ---------------------- EJECUCIÓN ----------------------
if __name__ == "__main__":
    app = AutomataApp()
    app.mainloop()
