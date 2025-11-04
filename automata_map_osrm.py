import tkinter as tk
import customtkinter as ctk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import folium
import random
import webbrowser
import os
import threading

class AutomataMapApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Simulación de Rutas con Autómatas - Vista Satelital 🚗")
        self.geometry("1200x750")
        ctk.set_appearance_mode("dark")

        # ---- FRAME PRINCIPAL ----
        self.frame_main = ctk.CTkFrame(self, corner_radius=15)
        self.frame_main.pack(padx=20, pady=20, fill="both", expand=True)

        self.title_label = ctk.CTkLabel(
            self.frame_main, text="AUTÓMATA DE RUTAS - MODO SATELITAL",
            font=("Arial Rounded MT Bold", 24)
        )
        self.title_label.pack(pady=15)

        # Entradas
        self.start_entry = ctk.CTkEntry(self.frame_main, placeholder_text="Estado inicial (ej: A)", width=200)
        self.start_entry.pack(pady=5)

        self.end_entry = ctk.CTkEntry(self.frame_main, placeholder_text="Estado final (ej: I)", width=200)
        self.end_entry.pack(pady=5)

        # Vincular tecla Enter a la actualización completa
        self.start_entry.bind("<Return>", lambda e: self._recalculate())
        self.end_entry.bind("<Return>", lambda e: self._recalculate())

        self.result_label = ctk.CTkLabel(self.frame_main, text="", font=("Arial", 16))
        self.result_label.pack(pady=10)

        # Crear grafo y dibujar
        self._create_graph()
        self._generate_random_weights()
        self._draw_graph()

        self.graph_label = ctk.CTkLabel(self.frame_main, text="", font=("Consolas", 14))
        self.graph_label.pack(pady=10)
        self._update_graph_info()

        # Generar mapa inicial
        threading.Thread(target=self._generate_map, daemon=True).start()

    # ------------------ CREAR GRAFO ------------------
    def _create_graph(self):
        self.G = nx.Graph()
        nodes = [chr(i) for i in range(65, 74)]  # A-I
        self.G.add_nodes_from(nodes)
        edges = [
            ("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("B", "E"),
            ("C", "F"), ("E", "G"), ("F", "G"), ("D", "H"), ("G", "H"), ("H", "I"), ("E", "I")
        ]
        self.G.add_edges_from(edges)

    # ------------------ PESOS ALEATORIOS ------------------
    def _generate_random_weights(self):
        for u, v in self.G.edges():
            self.G[u][v]['weight'] = random.randint(1, 3)

    # ------------------ DIBUJAR GRAFO ------------------
    def _draw_graph(self):
        plt.close('all')
        fig, ax = plt.subplots(figsize=(5.5, 4))
        pos = nx.spring_layout(self.G, seed=42)

        # Todos los caminos posibles
        nx.draw_networkx_edges(self.G, pos, ax=ax, edge_color='gray', width=2, alpha=0.5)
        nx.draw_networkx_nodes(self.G, pos, ax=ax, node_size=800, node_color="#1E90FF")
        nx.draw_networkx_labels(self.G, pos, ax=ax, font_color='white', font_size=10)

        # Ruta óptima
        start_state = self.start_entry.get().strip().upper() or "A"
        end_state = self.end_entry.get().strip().upper() or "I"

        try:
            path = nx.shortest_path(self.G, source=start_state, target=end_state, weight='weight')
        except nx.NetworkXNoPath:
            path = []

        if path:
            edges_opt = list(zip(path, path[1:]))
            nx.draw_networkx_edges(self.G, pos, edgelist=edges_opt, ax=ax,
                                   edge_color="#00FFFF", width=4, alpha=0.9)

        ax.set_title("Grafo de Rutas y Camino Óptimo", fontsize=12, color="white")
        ax.set_axis_off()

        # Limpiar canvas previo si existe
        if hasattr(self, "graph_canvas"):
            self.graph_canvas.get_tk_widget().destroy()

        self.graph_canvas = FigureCanvasTkAgg(fig, master=self.frame_main)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().pack(pady=10)

    # ------------------ INFO TEXTUAL ------------------
    def _update_graph_info(self):
        info = "⚙️ Conjunto de estados: {" + ", ".join(sorted(self.G.nodes())) + "}\n"
        info += "🔤 Alfabeto: {0, 1}\n"
        info += "⚖️ Pesos (aleatorios):\n"
        for u, v, w in self.G.edges(data='weight'):
            info += f"  δ({u}, {v}) = {w}\n"
        self.graph_label.configure(text=info)

    # ------------------ MAPA ------------------
    def _generate_map(self):
        start_state = self.start_entry.get().strip().upper() or "A"
        end_state = self.end_entry.get().strip().upper() or "I"

        positions = {
            "A": (4.712, -74.113), "B": (4.713, -74.110), "C": (4.711, -74.107),
            "D": (4.715, -74.108), "E": (4.716, -74.105), "F": (4.710, -74.103),
            "G": (4.717, -74.100), "H": (4.718, -74.097), "I": (4.719, -74.095)
        }

        m = folium.Map(location=positions[start_state], zoom_start=15, tiles="Esri.WorldImagery")

        # Todos los caminos posibles
        for u, v, data in self.G.edges(data=True):
            folium.PolyLine([positions[u], positions[v]], color="gray", weight=3, opacity=0.5).add_to(m)

        # Ruta óptima
        try:
            path = nx.shortest_path(self.G, source=start_state, target=end_state, weight='weight')
            total_weight = nx.shortest_path_length(self.G, source=start_state, target=end_state, weight='weight')
        except nx.NetworkXNoPath:
            path = []
            total_weight = None

        if path:
            coords = [positions[n] for n in path]
            folium.PolyLine(coords, color="#00FFFF", weight=6, opacity=0.9,
                            tooltip=f"Ruta óptima (peso total: {total_weight})").add_to(m)

            for i, n in enumerate(path):
                folium.CircleMarker(location=positions[n],
                                    radius=8,
                                    color="#00FFFF" if i in [0, len(path)-1] else "#39FF14",
                                    fill=True, fill_opacity=0.9,
                                    popup=f"Estado {n}").add_to(m)

            transition_info = " → ".join(path)
            result_text = (
                f"🏁 Estado inicial: {path[0]}\n"
                f"🎯 Estado final: {path[-1]}\n"
                f"🛣️ Ruta óptima: {transition_info}\n"
                f"⚖️ Peso total: {total_weight}\n"
                f"δ({', '.join(path[:-1])}) → {path[-1]}"
            )
            self.result_label.configure(text=result_text)

        map_path = "simulacion_auto_visible.html"
        m.save(map_path)
        webbrowser.open("file://" + os.path.abspath(map_path))

    # ------------------ RECALCULAR ------------------
    def _recalculate(self):
        """Recalcula todo al presionar Enter"""
        self._generate_random_weights()
        self._draw_graph()
        self._update_graph_info()
        threading.Thread(target=self._generate_map, daemon=True).start()


if __name__ == "__main__":
    app = AutomataMapApp()
    app.mainloop()
