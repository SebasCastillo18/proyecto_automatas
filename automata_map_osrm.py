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
import random
import time

# ------------------------------------
# CONFIGURACIÓN DEL AUTÓMATA
# ------------------------------------
ALPHABET = {"camino", "ruta", "vía"}
INITIAL_STATE = "A"
FINAL_STATES = {"H"}

# Coordenadas (Medellín simuladas, extendidas)
coords = {
    "A": (6.25184, -75.56359),
    "B": (6.2442, -75.5812),
    "C": (6.2705, -75.5721),
    "D": (6.237, -75.575),
    "E": (6.2308, -75.5906),
    "F": (6.275, -75.585),
    "G": (6.265, -75.600),
    "H": (6.280, -75.610)
}

# Grafo con más rutas y pesos (minutos)
G = nx.Graph()
edges = [
    ("A", "B", 5), ("A", "C", 6),
    ("B", "C", 3), ("B", "D", 5),
    ("C", "D", 4), ("C", "E", 6),
    ("D", "E", 5), ("E", "F", 7),
    ("F", "G", 4), ("G", "H", 6),
    ("C", "F", 5), ("B", "E", 8),
    ("A", "F", 10), ("D", "G", 9)
]
G.add_weighted_edges_from(edges)

# ------------------------------------
# CLASE PRINCIPAL
# ------------------------------------
class AutomataMapApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Autómata de Rutas Satelital - Ruta Óptima Neón")
        self.geometry("1000x780")
        ctk.set_appearance_mode("dark")

        self.G = G
        self.pos = nx.spring_layout(self.G, seed=42)
        self._build_ui()
        self._draw_graph()

    def _build_ui(self):
        frame = ctk.CTkFrame(self, corner_radius=20)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        title = ctk.CTkLabel(frame, text="🚗 Simulador de Rutas Satelital (Ruta Óptima en Neón)",
                             font=("Arial Rounded MT Bold", 22))
        title.pack(pady=10)

        self.start_entry = ctk.CTkEntry(frame, placeholder_text="Estado inicial (A)", width=200)
        self.start_entry.pack(pady=5)
        self.end_entry = ctk.CTkEntry(frame, placeholder_text="Estado final (H)", width=200)
        self.end_entry.pack(pady=5)

        info = ctk.CTkLabel(frame, text=f"Alfabeto: {ALPHABET}\n"
                                        f"Estado inicial: {INITIAL_STATE}\n"
                                        f"Estados finales: {FINAL_STATES}\n"
                                        f"Conjunto de estados: {list(coords.keys())}",
                            font=("Arial", 14))
        info.pack(pady=10)

        self.graph_label = ctk.CTkLabel(frame, text="")
        self.graph_label.pack(pady=10)

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

        # Todos los caminos posibles
        all_paths = list(nx.all_simple_paths(self.G, source=start, target=end))
        shortest_path = nx.shortest_path(self.G, source=start, target=end, weight="weight")
        path_edges = list(zip(shortest_path, shortest_path[1:]))
        self._draw_graph(path_edges)

        threading.Thread(target=lambda: self._simulate_multiple_routes(all_paths, shortest_path), daemon=True).start()

    def _simulate_multiple_routes(self, all_paths, best_path):
        m = folium.Map(location=coords[best_path[0]], zoom_start=14, tiles="Esri.WorldImagery")

        colors = ["#f87171", "#60a5fa", "#34d399", "#facc15", "#c084fc", "#fb923c"]

        # Mostrar todas las rutas posibles (sin neón)
        for i, path in enumerate(all_paths):
            folium.PolyLine([coords[n] for n in path],
                            color=colors[i % len(colors)], weight=3, opacity=0.5,
                            tooltip=f"Ruta {i+1}: {' → '.join(path)}").add_to(m)

        # Ruta óptima resaltada en neón (efecto doble capa)
        folium.PolyLine(
            [coords[n] for n in best_path],
            color="#00ffff",  # Capa interna brillante
            weight=12,
            opacity=0.4
        ).add_to(m)
        folium.PolyLine(
            [coords[n] for n in best_path],
            color="#0ff",  # Capa externa más intensa
            weight=6,
            opacity=0.9,
            tooltip="⭐ Ruta Óptima (neón)"
        ).add_to(m)

        # Marcadores de estados
        for node, (lat, lon) in coords.items():
            folium.CircleMarker(location=(lat, lon),
                                radius=7,
                                color="#38bdf8" if node not in FINAL_STATES else "#22c55e",
                                fill=True,
                                fill_color="#38bdf8",
                                popup=f"Estado {node}").add_to(m)

        # Animación del vehículo sobre todas las rutas
        car_icon = "https://cdn-icons-png.flaticon.com/512/743/743131.png"
        js_routes = [ [coords[n] for n in path] for path in all_paths ]
        js_code = f"""
        <script>
        map.whenReady(function() {{
            var carIcon = L.icon({{
                iconUrl: '{car_icon}',
                iconSize: [40, 40],
                iconAnchor: [20, 20]
            }});
            var routes = {js_routes};
            var marker = L.marker(routes[0][0], {{icon: carIcon}}).addTo(map);
            var routeIndex = 0;
            var pointIndex = 0;

            function moveCar() {{
                if (routeIndex >= routes.length) return;
                var route = routes[routeIndex];
                if (pointIndex < route.length) {{
                    marker.setLatLng(route[pointIndex]);
                    pointIndex++;
                    setTimeout(moveCar, 600);
                }} else {{
                    routeIndex++;
                    pointIndex = 0;
                    setTimeout(moveCar, 1000);
                }}
            }}
            moveCar();
        }});
        </script>
        """
        m.get_root().html.add_child(folium.Element(js_code))

        file_path = "simulacion_ruta_neon.html"
        m.save(file_path)
        webbrowser.open("file://" + os.path.abspath(file_path))

        resumen = f"📍 Estado inicial: {best_path[0]}\n🏁 Estado final: {best_path[-1]}\n"
        resumen += f"\n🛣️ Caminos posibles:\n"
        for i, path in enumerate(all_paths):
            resumen += f"  Ruta {i+1}: {' → '.join(path)}\n"
        resumen += f"\n⭐ Ruta óptima (neón): {' → '.join(best_path)}"
        self.after(1000, lambda: self.result_label.configure(text=resumen))


# ------------------------------------
# EJECUCIÓN
# ------------------------------------
if __name__ == "__main__":
    app = AutomataMapApp()
    app.mainloop()
