import customtkinter as ctk
import folium
import networkx as nx
import webbrowser
import threading
import os
import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt

# ------------------------------------
# Configuración base del autómata
# ------------------------------------
ALPHABET = {"camino", "ruta", "vía"}
INITIAL_STATE = "A"
FINAL_STATES = {"E"}

# Coordenadas (ejemplo: Medellín)
coords = {
    "A": (6.25184, -75.56359),  # Medellín
    "B": (6.2442, -75.5812),    # Laureles
    "C": (6.2705, -75.5721),    # Robledo
    "D": (6.237, -75.575),
    "E": (6.2308, -75.5906)     # Poblado
}

# Grafo con pesos (minutos)
G = nx.Graph()
edges = [
    ("A", "B", 5),
    ("A", "C", 7),
    ("B", "C", 3),
    ("B", "D", 6),
    ("C", "D", 4),
    ("D", "E", 5),
    ("C", "E", 8)
]
G.add_weighted_edges_from(edges)


# ------------------------------------
# Clase principal
# ------------------------------------
class AutomataMapApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Autómata de Rutas - Simulación Satelital en Tiempo Real")
        self.geometry("1000x780")
        ctk.set_appearance_mode("dark")

        self.G = G
        self.pos = nx.spring_layout(self.G, seed=42)

        self._build_ui()
        self._draw_graph()

    def _build_ui(self):
        frame = ctk.CTkFrame(self, corner_radius=20)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        title = ctk.CTkLabel(frame, text="🚘 Simulador de Rutas Satelital - Calles Reales (OSRM)",
                             font=("Arial Rounded MT Bold", 22))
        title.pack(pady=10)

        self.start_entry = ctk.CTkEntry(frame, placeholder_text="Estado inicial (A)", width=200)
        self.start_entry.pack(pady=5)
        self.end_entry = ctk.CTkEntry(frame, placeholder_text="Estado final (E)", width=200)
        self.end_entry.pack(pady=5)

        info = ctk.CTkLabel(frame, text=f"Alfabeto: {ALPHABET}\n"
                                        f"Estado inicial: {INITIAL_STATE}\n"
                                        f"Estados finales: {FINAL_STATES}\n"
                                        f"Conjunto de estados: {list(coords.keys())}",
                            font=("Arial", 14))
        info.pack(pady=10)

        self.graph_label = ctk.CTkLabel(frame, text="")
        self.graph_label.pack(pady=10)

        # Nueva área de resultados
        self.result_label = ctk.CTkLabel(frame, text="", justify="left",
                                         font=("Consolas", 14), text_color="#e5e7eb")
        self.result_label.pack(pady=10)

        self.bind("<Return>", lambda e: self._on_enter())

    def _draw_graph(self, path_edges=None):
        plt.figure(figsize=(5, 4))
        plt.axis("off")

        edge_colors = []
        for (u, v) in self.G.edges():
            edge_colors.append("#facc15" if path_edges and (u, v) in path_edges else "#94a3b8")

        node_colors = []
        for n in self.G.nodes():
            if n in FINAL_STATES:
                node_colors.append("#16a34a")
            elif n == INITIAL_STATE:
                node_colors.append("#2563eb")
            else:
                node_colors.append("#60a5fa")

        nx.draw_networkx(self.G, pos=self.pos, node_color=node_colors, edge_color=edge_colors,
                         node_size=600, with_labels=True)
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

    def _on_enter(self):
        start = self.start_entry.get().strip().upper()
        end = self.end_entry.get().strip().upper()
        if start not in coords or end not in coords:
            return
        path = nx.shortest_path(self.G, source=start, target=end, weight="weight")
        path_edges = list(zip(path, path[1:]))
        self._draw_graph(path_edges)
        threading.Thread(target=lambda: self._simulate_real_route(path), daemon=True).start()

    # -------------------------------------------------
    # Simulación real con OSRM + auto + resumen final
    # -------------------------------------------------
    def _simulate_real_route(self, path):
        start = coords[path[0]]
        end = coords[path[-1]]

        url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
        try:
            response = requests.get(url)
            data = response.json()
            route_coords = data["routes"][0]["geometry"]["coordinates"]
        except Exception as e:
            print("Error al obtener ruta:", e)
            return

        m = folium.Map(location=start, zoom_start=15, tiles="Esri.WorldImagery")

        # Todas las rutas posibles del grafo
        for (u, v) in self.G.edges():
            folium.PolyLine([coords[u], coords[v]], color="white", weight=2, opacity=0.6).add_to(m)

        # Ruta óptima
        folium.PolyLine([(lat, lon) for lon, lat in route_coords], color="yellow", weight=6, opacity=0.9).add_to(m)

        # Nodos
        for node, (lat, lon) in coords.items():
            folium.CircleMarker(location=(lat, lon),
                                radius=7,
                                color="#38bdf8" if node not in FINAL_STATES else "#22c55e",
                                fill=True,
                                fill_color="#38bdf8",
                                popup=f"Estado {node}").add_to(m)

        # Simulación del vehículo en tiempo real
        car_icon = "https://cdn-icons-png.flaticon.com/512/743/743131.png"
        js_code = f"""
        <script>
        map.whenReady(function() {{
            var carIcon = L.icon({{
                iconUrl: '{car_icon}',
                iconSize: [40, 40],
                iconAnchor: [20, 20]
            }});

            var coords = {[(lat, lon) for lon, lat in route_coords]};
            var marker = L.marker(coords[0], {{icon: carIcon}}).addTo(map);
            var index = 0;

            function moveCar() {{
                if (index < coords.length) {{
                    marker.setLatLng(coords[index]);
                    index++;
                    setTimeout(moveCar, 80);
                }}
            }}
            moveCar();
        }});
        </script>
        """
        m.get_root().html.add_child(folium.Element(js_code))

        map_path = "simulacion_auto_tiempo_real.html"
        m.save(map_path)
        webbrowser.open("file://" + os.path.abspath(map_path))

        # Al finalizar: mostrar resumen del recorrido
        transiciones = []
        for i in range(len(path) - 1):
            transiciones.append(f"δ({path[i]}, camino) → {path[i + 1]}")

        resumen = (f"📍 Estado inicial: {path[0]}\n"
                   f"🏁 Estado final: {path[-1]}\n"
                   f"🛣️ Estados recorridos: {', '.join(path)}\n"
                   f"⚙️ Función de transición:\n  " + "\n  ".join(transiciones))

        self.after(1000, lambda: self.result_label.configure(text=resumen))


# ------------------------------------
# Ejecutar
# ------------------------------------
if __name__ == "__main__":
    app = AutomataMapApp()
    app.mainloop()
