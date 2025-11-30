import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import Canvas
from FATPartition import FATPartition


class FATCalculatorGUI:
    """Interface graphique pour le calculateur de partition FAT."""

    def __init__(self, root):
        self.root = root
        self.root.title("Calculateur FAT - Offsets et Secteurs")

        # Mettre en plein écran
        self.root.attributes('-zoomed', True)  # Pour Linux
        # Alternative pour Windows/Mac : self.root.state('zoomed')

        self.partition = None

        # Création de l'interface
        self.create_widgets()

    def create_widgets(self):
        """Crée tous les widgets de l'interface."""

        # Frame principale avec padding
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # Titre
        title = ttk.Label(
            main_frame,
            text="Calculateur d'Offsets pour Partition FAT",
            font=("Helvetica", 16, "bold"),
            bootstyle="primary"
        )
        title.pack(pady=(0, 20))

        # Frame pour les paramètres
        params_frame = ttk.Labelframe(
            main_frame,
            text="Paramètres de la Partition",
            padding=15,
            bootstyle="info"
        )
        params_frame.pack(fill=X, pady=(0, 15))

        # Définition des paramètres avec valeurs par défaut
        self.params = [
            ("Octets par secteur", "octets_per_sector", "512"),
            ("Secteurs par cluster", "sectors_per_cluster", "4"),
            ("Secteurs réservés", "reserved_sectors", "4"),
            ("Nombre de zones FAT", "fat_count", "2"),
            ("Secteurs par zone FAT", "sectors_per_fat", "246"),
            ("Entrées du répertoire racine", "root_entries", "512"),
        ]

        self.entries = {}

        # Création des champs de saisie
        for i, (label_text, var_name, default_value) in enumerate(self.params):
            row = i // 2
            col = (i % 2) * 2

            label = ttk.Label(params_frame, text=label_text + ":")
            label.grid(row=row, column=col, sticky=W, padx=(0, 10), pady=5)

            entry = ttk.Entry(params_frame, width=15, bootstyle="info")
            entry.insert(0, default_value)
            entry.grid(row=row, column=col + 1, sticky=EW, pady=5, padx=(0, 20))

            self.entries[var_name] = entry

        # Configuration des colonnes pour qu'elles s'étendent
        params_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(3, weight=1)

        # Bouton de calcul
        calc_button = ttk.Button(
            main_frame,
            text="Calculer les Informations",
            command=self.calculate_partition,
            bootstyle="success",
            width=30
        )
        calc_button.pack(pady=10)

        # Frame pour les résultats
        results_frame = ttk.Labelframe(
            main_frame,
            text="Informations de la Partition",
            padding=15,
            bootstyle="success"
        )
        results_frame.pack(fill=BOTH, expand=YES, pady=(0, 15))

        # Frame conteneur pour diviser en deux colonnes
        results_container = ttk.Frame(results_frame)
        results_container.pack(fill=BOTH, expand=YES)

        # Colonne gauche : Zone de texte
        left_frame = ttk.Frame(results_container)
        left_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 10))

        # Zone de texte pour afficher les résultats
        self.results_text = ttk.Text(
            left_frame,
            height=12,
            width=50,
            font=("Courier", 10),
            wrap=NONE
        )
        self.results_text.pack(fill=BOTH, expand=YES)

        # Scrollbar pour la zone de texte
        scrollbar = ttk.Scrollbar(self.results_text, orient=VERTICAL, command=self.results_text.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.results_text.config(yscrollcommand=scrollbar.set)

        # Colonne droite : Cartographie visuelle
        right_frame = ttk.Frame(results_container)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=YES)

        # Titre de la cartographie
        map_title = ttk.Label(right_frame, text="Cartographie de la Partition", font=("Helvetica", 11, "bold"))
        map_title.pack(pady=(0, 10))

        # Canvas pour la cartographie
        self.map_canvas = Canvas(right_frame, bg="white", relief=SOLID, borderwidth=1)
        self.map_canvas.pack(fill=BOTH, expand=YES)

        # Légende
        legend_frame = ttk.Frame(right_frame)
        legend_frame.pack(fill=X, pady=(10, 0))

        self.create_legend(legend_frame)

        # Frame pour la recherche de cluster
        cluster_frame = ttk.Labelframe(
            main_frame,
            text="Recherche d'Offset de Cluster",
            padding=15,
            bootstyle="warning"
        )
        cluster_frame.pack(fill=X)

        # Champ de saisie du cluster
        cluster_input_frame = ttk.Frame(cluster_frame)
        cluster_input_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(cluster_input_frame, text="Numéro de cluster:").pack(side=LEFT, padx=(0, 10))

        self.cluster_entry = ttk.Entry(cluster_input_frame, width=15, bootstyle="warning")
        self.cluster_entry.insert(0, "2")
        self.cluster_entry.pack(side=LEFT, padx=(0, 10))

        search_button = ttk.Button(
            cluster_input_frame,
            text="Rechercher",
            command=self.search_cluster,
            bootstyle="warning"
        )
        search_button.pack(side=LEFT)

        # Zone de texte pour afficher le résultat du cluster (sélectionnable)
        self.cluster_result = ttk.Text(
            cluster_frame,
            height=2,
            font=("Courier", 10, "bold"),
            wrap=WORD
        )
        self.cluster_result.pack(fill=X, pady=(10, 0))

    def create_legend(self, parent):
        """Crée la légende des couleurs de la cartographie."""
        legend_items = [
            ("Boot Sector", "#FFD700"),  # Jaune (Gold)
            ("Reserved", "#FF4444"),      # Rouge
            ("FAT 1", "#90EE90"),        # Vert clair
            ("FAT 2", "#006400"),        # Vert foncé
            ("Root Dir", "#FFA500"),     # Orange
            ("Data", "#4169E1")          # Bleu royal
        ]

        for i, (label, color) in enumerate(legend_items):
            # Frame pour chaque élément de légende
            item_frame = ttk.Frame(parent)
            item_frame.pack(side=LEFT, padx=5)

            # Carré de couleur
            color_box = Canvas(item_frame, width=15, height=15, bg=color, relief=SOLID, borderwidth=1)
            color_box.pack(side=LEFT, padx=(0, 3))

            # Label
            ttk.Label(item_frame, text=label, font=("Helvetica", 8)).pack(side=LEFT)

    def draw_partition_map(self):
        """Dessine la cartographie visuelle de la partition."""
        if not self.partition:
            return

        # Effacer le canvas
        self.map_canvas.delete("all")

        # Taille du canvas
        canvas_width = self.map_canvas.winfo_width()
        canvas_height = self.map_canvas.winfo_height()

        # Si le canvas n'est pas encore affiché, utiliser une taille par défaut
        if canvas_width <= 1:
            canvas_width = 500
        if canvas_height <= 1:
            canvas_height = 400

        # Calculer le nombre total de secteurs à afficher
        total_sectors = self.partition.first_data_sector + 200  # Afficher aussi une partie de la zone data

        # Taille des carrés (plus grands)
        square_size = 15
        spacing = 2

        # Largeur fixe : nombre de carrés par ligne basé sur la structure de la partition
        # On veut que toutes les zones importantes soient visibles
        squares_per_row = 40  # Largeur fixe de 40 carrés par ligne

        # Calculer combien de secteurs représente chaque carré
        sectors_per_square = max(1, total_sectors // (squares_per_row * 15))

        # Position de départ
        x_offset = 10
        y_offset = 10
        current_x = x_offset
        current_y = y_offset

        # Dictionnaire pour stocker les informations de chaque carré
        self.square_info = {}

        # Dessiner les secteurs
        current_sector = 0
        square_index = 0

        while current_sector < total_sectors:
            # Déterminer la couleur et le type selon le secteur
            if current_sector == 0:
                # Boot sector
                color = "#FFD700"  # Jaune
                sector_type = "Boot Sector"
                sector_range = f"Secteur {current_sector}"
            elif current_sector < self.partition.reserved_sectors:
                # Reserved sectors
                color = "#FF4444"  # Rouge
                sector_type = "Reserved Sectors"
                sector_range = f"Secteurs {current_sector}-{current_sector + sectors_per_square - 1}"
            elif current_sector < self.partition.reserved_sectors + self.partition.sectors_per_fat:
                # FAT 1
                color = "#90EE90"  # Vert clair
                sector_type = "FAT 1"
                sector_range = f"Secteurs {current_sector}-{current_sector + sectors_per_square - 1}"
            elif current_sector < self.partition.reserved_sectors + (2 * self.partition.sectors_per_fat):
                # FAT 2
                color = "#006400"  # Vert foncé
                sector_type = "FAT 2"
                sector_range = f"Secteurs {current_sector}-{current_sector + sectors_per_square - 1}"
            elif current_sector < self.partition.first_data_sector:
                # Root directory
                color = "#FFA500"  # Orange
                sector_type = "Root Directory"
                sector_range = f"Secteurs {current_sector}-{current_sector + sectors_per_square - 1}"
            else:
                # Data zone
                color = "#4169E1"  # Bleu royal
                sector_type = "Data Zone"
                sector_range = f"Secteurs {current_sector}-{current_sector + sectors_per_square - 1}"

            # Dessiner le carré
            rect_id = self.map_canvas.create_rectangle(
                current_x, current_y,
                current_x + square_size, current_y + square_size,
                fill=color, outline="gray", width=1
            )

            # Stocker les informations pour le tooltip
            self.square_info[rect_id] = {
                'type': sector_type,
                'range': sector_range,
                'color': color
            }

            # Passer au carré suivant
            current_x += square_size + spacing
            square_index += 1

            # Nouvelle ligne après squares_per_row carrés
            if square_index % squares_per_row == 0:
                current_x = x_offset
                current_y += square_size + spacing

            current_sector += sectors_per_square

        # Ajouter un texte indiquant l'échelle
        scale_text = f"1 carré = {sectors_per_square} secteur(s) | Largeur: {squares_per_row} carrés"
        self.map_canvas.create_text(
            canvas_width // 2, current_y + square_size + 20,
            text=scale_text,
            font=("Helvetica", 9),
            fill="black"
        )

        # Créer le tooltip (initialement invisible)
        self.tooltip = self.map_canvas.create_text(
            0, 0, text="", font=("Helvetica", 9, "bold"),
            fill="black", anchor="nw", state="hidden"
        )
        self.tooltip_bg = self.map_canvas.create_rectangle(
            0, 0, 0, 0, fill="lightyellow", outline="black", state="hidden"
        )

        # Bind les événements de souris
        self.map_canvas.bind("<Motion>", self.on_mouse_move)
        self.map_canvas.bind("<Leave>", self.on_mouse_leave)

    def on_mouse_move(self, event):
        """Affiche le tooltip au survol d'un carré."""
        # Trouver le carré sous le curseur
        items = self.map_canvas.find_overlapping(event.x, event.y, event.x, event.y)

        # Chercher un carré (rectangle) avec des informations
        for item in items:
            if item in self.square_info:
                info = self.square_info[item]
                tooltip_text = f"{info['type']}\n{info['range']}"

                # Positionner et afficher le tooltip
                x = event.x + 15
                y = event.y + 15

                self.map_canvas.itemconfig(self.tooltip, text=tooltip_text, state="normal")
                self.map_canvas.coords(self.tooltip, x, y)

                # Calculer la taille du fond
                bbox = self.map_canvas.bbox(self.tooltip)
                if bbox:
                    self.map_canvas.coords(self.tooltip_bg,
                                          bbox[0] - 3, bbox[1] - 3,
                                          bbox[2] + 3, bbox[3] + 3)
                    self.map_canvas.itemconfig(self.tooltip_bg, state="normal")
                    self.map_canvas.tag_raise(self.tooltip)

                return

        # Si aucun carré n'est trouvé, cacher le tooltip
        self.map_canvas.itemconfig(self.tooltip, state="hidden")
        self.map_canvas.itemconfig(self.tooltip_bg, state="hidden")

    def on_mouse_leave(self, event):
        """Cache le tooltip quand la souris quitte le canvas."""
        self.map_canvas.itemconfig(self.tooltip, state="hidden")
        self.map_canvas.itemconfig(self.tooltip_bg, state="hidden")

    def calculate_partition(self):
        """Calcule et affiche les informations de la partition."""
        try:
            # Récupération des valeurs
            params_values = {}
            for var_name, entry in self.entries.items():
                params_values[var_name] = int(entry.get())

            # Création de l'objet partition
            self.partition = FATPartition(
                octets_per_sector=params_values['octets_per_sector'],
                sectors_per_cluster=params_values['sectors_per_cluster'],
                reserved_sectors=params_values['reserved_sectors'],
                fat_count=params_values['fat_count'],
                sectors_per_fat=params_values['sectors_per_fat'],
                root_entries=params_values['root_entries']
            )

            # Affichage des résultats
            self.display_results()

            # Dessiner la cartographie
            self.root.after(100, self.draw_partition_map)  # Petit délai pour que le canvas soit bien dimensionné

        except ValueError as e:
            self.results_text.delete(1.0, END)
            self.results_text.insert(1.0, f"Erreur: Veuillez entrer des nombres valides.\n{str(e)}")

    def display_results(self):
        """Affiche les informations de la partition dans la zone de texte."""
        if not self.partition:
            return

        self.results_text.delete(1.0, END)

        info = self.partition.get_info()

        result = "=" * 70 + "\n"
        result += "INFORMATIONS DE LA PARTITION FAT\n"
        result += "=" * 70 + "\n\n"

        result += f"Octets par secteur         : {info['octets_per_sector']}\n"
        result += f"Secteurs par cluster       : {info['sectors_per_cluster']}\n"
        result += f"Taille d'un cluster        : {info['cluster_size_bytes']} octets\n\n"

        result += f"Secteurs réservés          : {info['reserved_sectors']}\n"
        result += f"Nombre de zones FAT        : {info['fat_count']}\n"
        result += f"Secteurs par zone FAT      : {info['sectors_per_fat']}\n"
        result += f"Secteurs FAT totaux        : {info['fat_allocated_sectors']}\n\n"

        result += f"Entrées répertoire racine  : {info['root_entries']}\n"
        result += f"Secteurs répertoire racine : {info['root_directory_sectors']}\n\n"

        result += "-" * 70 + "\n"
        result += f"1er secteur de données     : {info['first_data_sector']}\n"
        result += f"Offset zone de données     : {info['data_zone_offset']} octets (0x{info['data_zone_offset']:X})\n"
        result += "=" * 70 + "\n"

        self.results_text.insert(1.0, result)

    def search_cluster(self):
        """Recherche et affiche l'offset d'un cluster spécifique."""
        # Effacer le contenu précédent
        self.cluster_result.delete(1.0, END)

        if not self.partition:
            self.cluster_result.insert(1.0, "Veuillez d'abord calculer les informations de la partition.")
            return

        try:
            cluster_number = int(self.cluster_entry.get())
            offset = self.partition.get_cluster_offset(cluster_number)

            result = f"Cluster {cluster_number} → Offset: {offset} octets (0x{offset:X})"
            self.cluster_result.insert(1.0, result)

        except ValueError as e:
            self.cluster_result.insert(1.0, f"Erreur: {str(e)}")


def main():
    """Point d'entrée de l'application GUI."""
    # Création de la fenêtre principale avec un thème moderne
    root = ttk.Window(themename="cosmo")
    app = FATCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
