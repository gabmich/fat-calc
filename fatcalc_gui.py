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

        # Type de FAT (en premier, sur toute la largeur)
        fat_type_frame = ttk.Frame(params_frame)
        fat_type_frame.grid(row=0, column=0, columnspan=4, sticky=EW, pady=(0, 10))

        ttk.Label(fat_type_frame, text="Type de FAT:", font=("Helvetica", 10, "bold")).pack(side=LEFT, padx=(0, 10))

        self.fat_type_var = ttk.StringVar(value="FAT16")
        fat_type_combo = ttk.Combobox(
            fat_type_frame,
            textvariable=self.fat_type_var,
            values=["FAT12", "FAT16", "FAT32"],
            state="readonly",
            width=10,
            bootstyle="info"
        )
        fat_type_combo.pack(side=LEFT)

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

        # Création des champs de saisie (commencer à la ligne 1)
        for i, (label_text, var_name, default_value) in enumerate(self.params):
            row = (i // 2) + 1  # +1 car la ligne 0 est pour le type FAT
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

        # Frame pour les boutons de calcul et réinitialisation
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=10)

        # Bouton de calcul
        calc_button = ttk.Button(
            buttons_frame,
            text="Calculer les Informations",
            command=self.calculate_partition,
            bootstyle="success",
            width=30
        )
        calc_button.pack(side=LEFT, padx=(0, 10))

        # Bouton de réinitialisation
        reset_button = ttk.Button(
            buttons_frame,
            text="Réinitialiser",
            command=self.reset_all,
            bootstyle="danger",
            width=20
        )
        reset_button.pack(side=LEFT)

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

        # Frame pour le canvas et la scrollbar
        canvas_frame = ttk.Frame(right_frame)
        canvas_frame.pack(fill=BOTH, expand=YES)

        # Canvas pour la cartographie
        self.map_canvas = Canvas(canvas_frame, bg="white", relief=SOLID, borderwidth=1)
        self.map_canvas.pack(side=LEFT, fill=BOTH, expand=YES)

        # Scrollbar verticale
        map_scrollbar = ttk.Scrollbar(canvas_frame, orient=VERTICAL, command=self.map_canvas.yview)
        map_scrollbar.pack(side=RIGHT, fill=Y)
        self.map_canvas.configure(yscrollcommand=map_scrollbar.set)

        # Légende
        legend_frame = ttk.Frame(right_frame)
        legend_frame.pack(fill=X, pady=(10, 0))

        self.create_legend(legend_frame)

        # Frame conteneur pour les trois sections de recherche avec grid
        search_container = ttk.Frame(main_frame)
        search_container.pack(fill=X, pady=(0, 0))

        # Configurer les colonnes pour qu'elles aient le même poids (largeur égale)
        search_container.columnconfigure(0, weight=1)
        search_container.columnconfigure(1, weight=1)
        search_container.columnconfigure(2, weight=1)

        # Frame GAUCHE : Recherche d'offset de cluster
        cluster_frame = ttk.Labelframe(
            search_container,
            text="Cluster → Offset",
            padding=15,
            bootstyle="warning"
        )
        cluster_frame.grid(row=0, column=0, sticky=EW, padx=(0, 5))

        # Champ de saisie du cluster
        cluster_input_frame = ttk.Frame(cluster_frame)
        cluster_input_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(cluster_input_frame, text="N° cluster:").pack(side=LEFT, padx=(0, 10))

        self.cluster_entry = ttk.Entry(cluster_input_frame, width=12, bootstyle="warning")
        self.cluster_entry.insert(0, "2")
        self.cluster_entry.pack(side=LEFT, padx=(0, 10))
        # Permettre de rechercher avec la touche Entrée
        self.cluster_entry.bind("<Return>", lambda e: self.search_cluster())

        search_button = ttk.Button(
            cluster_input_frame,
            text="Chercher",
            command=self.search_cluster,
            bootstyle="warning"
        )
        search_button.pack(side=LEFT)

        # Zone de texte pour afficher le résultat du cluster (sélectionnable)
        self.cluster_result = ttk.Text(
            cluster_frame,
            height=2,
            font=("Courier", 9, "bold"),
            wrap=WORD
        )
        self.cluster_result.pack(fill=X, pady=(10, 0))

        # Frame MILIEU : Recherche de cluster depuis offset
        offset_frame = ttk.Labelframe(
            search_container,
            text="Offset → Cluster",
            padding=15,
            bootstyle="success"
        )
        offset_frame.grid(row=0, column=1, sticky=EW, padx=(5, 5))

        # Champ de saisie de l'offset
        offset_input_frame = ttk.Frame(offset_frame)
        offset_input_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(offset_input_frame, text="Offset:").pack(side=LEFT, padx=(0, 10))

        self.offset_entry = ttk.Entry(offset_input_frame, width=12, bootstyle="success")
        self.offset_entry.insert(0, "270336")
        self.offset_entry.pack(side=LEFT, padx=(0, 10))
        # Permettre de rechercher avec la touche Entrée
        self.offset_entry.bind("<Return>", lambda e: self.search_cluster_from_offset())

        search_offset_button = ttk.Button(
            offset_input_frame,
            text="Chercher",
            command=self.search_cluster_from_offset,
            bootstyle="success"
        )
        search_offset_button.pack(side=LEFT)

        # Zone de texte pour afficher le résultat de la recherche d'offset
        self.offset_result = ttk.Text(
            offset_frame,
            height=2,
            font=("Courier", 9, "bold"),
            wrap=WORD
        )
        self.offset_result.pack(fill=X, pady=(10, 0))

        # Frame DROITE : Recherche d'index dans la FAT
        fat_index_frame = ttk.Labelframe(
            search_container,
            text="Cluster → Index FAT",
            padding=15,
            bootstyle="info"
        )
        fat_index_frame.grid(row=0, column=2, sticky=EW, padx=(5, 0))

        # Champ de saisie du cluster pour recherche FAT
        fat_input_frame = ttk.Frame(fat_index_frame)
        fat_input_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(fat_input_frame, text="N° cluster:").pack(side=LEFT, padx=(0, 10))

        self.fat_cluster_entry = ttk.Entry(fat_input_frame, width=8, bootstyle="info")
        self.fat_cluster_entry.insert(0, "2")
        self.fat_cluster_entry.pack(side=LEFT, padx=(0, 10))
        # Permettre de rechercher avec la touche Entrée
        self.fat_cluster_entry.bind("<Return>", lambda e: self.search_fat_index())

        # Dropdown pour choisir FAT1 ou FAT2
        ttk.Label(fat_input_frame, text="FAT:").pack(side=LEFT, padx=(5, 5))
        self.fat_number_var = ttk.StringVar(value="1")
        fat_combo = ttk.Combobox(
            fat_input_frame,
            textvariable=self.fat_number_var,
            values=["1", "2"],
            state="readonly",
            width=3,
            bootstyle="info"
        )
        fat_combo.pack(side=LEFT, padx=(0, 5))

        search_fat_button = ttk.Button(
            fat_input_frame,
            text="Chercher",
            command=self.search_fat_index,
            bootstyle="info"
        )
        search_fat_button.pack(side=LEFT)

        # Zone de texte pour afficher le résultat de la recherche FAT
        self.fat_result = ttk.Text(
            fat_index_frame,
            height=2,
            font=("Courier", 9, "bold"),
            wrap=WORD
        )
        self.fat_result.pack(fill=X, pady=(10, 0))

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
        # Utiliser le calcul automatique basé sur le type de FAT
        total_sectors = self.partition.total_sectors

        # Taille des carrés
        square_size = 15
        spacing = 2

        # Largeur fixe : nombre de carrés par ligne
        squares_per_row = 80  # Largeur fixe de 80 carrés par ligne

        # 1 carré = 1 secteur pour un maximum de détails
        sectors_per_square = 1

        # Position de départ
        x_offset = 10
        y_offset = 10
        current_x = x_offset
        current_y = y_offset

        # Dictionnaire pour stocker les informations de chaque carré
        self.square_info = {}
        self.sector_to_rect = {}  # Mapping secteur -> rectangle ID

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
                fill=color, outline="gray", width=1,
                tags="sector_rect"
            )

            # Stocker les informations pour le tooltip et la recherche
            self.square_info[rect_id] = {
                'type': sector_type,
                'range': sector_range,
                'color': color,
                'start_sector': current_sector,
                'end_sector': current_sector + sectors_per_square - 1,
                'x': current_x,
                'y': current_y,
                'size': square_size
            }

            # Mapping secteur -> rectangle pour la recherche
            for s in range(current_sector, current_sector + sectors_per_square):
                if s < total_sectors:
                    self.sector_to_rect[s] = rect_id

            # Passer au carré suivant
            current_x += square_size + spacing
            square_index += 1

            # Nouvelle ligne après squares_per_row carrés
            if square_index % squares_per_row == 0:
                current_x = x_offset
                current_y += square_size + spacing

            current_sector += sectors_per_square

        # Calculer la largeur totale nécessaire
        total_width = x_offset + (squares_per_row * (square_size + spacing)) + 10

        # Ajouter un texte indiquant l'échelle
        scale_text = f"1 carré = {sectors_per_square} secteur(s) | Largeur: {squares_per_row} carrés"
        self.map_canvas.create_text(
            total_width // 2, current_y + square_size + 20,
            text=scale_text,
            font=("Helvetica", 9),
            fill="black"
        )

        # Configurer la scrollregion pour permettre le défilement
        total_height = current_y + square_size + 50
        self.map_canvas.configure(scrollregion=(0, 0, total_width, total_height))

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

        # Bind le scroll de la molette
        self.map_canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.map_canvas.bind("<Button-4>", self.on_mousewheel)  # Linux scroll up
        self.map_canvas.bind("<Button-5>", self.on_mousewheel)  # Linux scroll down

        # Variables pour la mise en évidence du cluster
        self.highlighted_rect = None
        self.highlight_marker = None

    def on_mousewheel(self, event):
        """Gère le défilement avec la molette de la souris."""
        # Windows/MacOS
        if event.num == 4 or event.delta > 0:
            self.map_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.map_canvas.yview_scroll(1, "units")

    def on_mouse_move(self, event):
        """Affiche le tooltip au survol d'un carré."""
        # Ajuster les coordonnées pour le scroll
        canvas_x = self.map_canvas.canvasx(event.x)
        canvas_y = self.map_canvas.canvasy(event.y)

        # Trouver le carré sous le curseur
        items = self.map_canvas.find_overlapping(canvas_x, canvas_y, canvas_x, canvas_y)

        # Chercher un carré (rectangle) avec des informations
        for item in items:
            if item in self.square_info:
                info = self.square_info[item]
                tooltip_text = f"{info['type']}\n{info['range']}"

                # Positionner et afficher le tooltip (ajuster pour le scroll)
                x = canvas_x + 15
                y = canvas_y + 15

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

    def highlight_cluster(self, cluster_number):
        """Met en évidence un cluster sur la cartographie."""
        if not self.partition:
            return

        # Effacer la mise en évidence précédente
        self.clear_highlight()

        # Calculer le secteur correspondant au cluster
        cluster_sector = self.partition.first_data_sector + (cluster_number - 2) * self.partition.sectors_per_cluster

        # Trouver le rectangle correspondant à ce secteur
        if cluster_sector not in self.sector_to_rect:
            # Le cluster n'est pas visible dans la cartographie
            return

        rect_id = self.sector_to_rect[cluster_sector]
        info = self.square_info.get(rect_id)

        if not info:
            return

        # Stocker le rectangle mis en évidence
        self.highlighted_rect = rect_id

        # Créer un marqueur visuel autour du carré
        x, y = info['x'], info['y']
        size = info['size']

        # Bordure épaisse rouge vif
        self.highlight_marker = self.map_canvas.create_rectangle(
            x - 2, y - 2,
            x + size + 2, y + size + 2,
            outline="#FF0000", width=4,
            tags="highlight"
        )

        # Ajouter un texte "CLUSTER X" au-dessus du carré
        text_x = x + size // 2
        text_y = y - 10

        self.highlight_text_bg = self.map_canvas.create_rectangle(
            text_x - 40, text_y - 10,
            text_x + 40, text_y + 10,
            fill="#FF0000", outline="black", width=2,
            tags="highlight"
        )

        self.highlight_text = self.map_canvas.create_text(
            text_x, text_y,
            text=f"CLUSTER {cluster_number}",
            font=("Helvetica", 9, "bold"),
            fill="white",
            tags="highlight"
        )

        # Scroller automatiquement vers le cluster
        # Calculer le pourcentage de position du cluster
        canvas_height = float(self.map_canvas.cget("height"))
        scroll_region = self.map_canvas.cget("scrollregion").split()
        if scroll_region and len(scroll_region) == 4:
            total_height = float(scroll_region[3])
            if total_height > 0:
                # Centrer le cluster dans la vue
                scroll_position = max(0, min(1, (y - canvas_height / 2) / total_height))
                self.map_canvas.yview_moveto(scroll_position)

    def clear_highlight(self):
        """Efface la mise en évidence du cluster."""
        # Supprimer tous les éléments avec le tag "highlight"
        self.map_canvas.delete("highlight")
        self.highlighted_rect = None
        self.highlight_marker = None

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
                root_entries=params_values['root_entries'],
                fat_type=self.fat_type_var.get()
            )

            # Affichage des résultats
            self.display_results()

            # Effacer les recherches précédentes
            self.cluster_result.delete(1.0, END)
            self.offset_result.delete(1.0, END)
            self.fat_result.delete(1.0, END)

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

        result += f"Type de FAT                : {info['fat_type']}\n"
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
        result += f"Offset zone de données     : {info['data_zone_offset']} octets (0x{info['data_zone_offset']:X})\n\n"

        result += "CALCUL AUTOMATIQUE (basé sur le type de FAT)\n"
        result += "-" * 70 + "\n"
        result += f"Entrées FAT totales        : {info['total_fat_entries']}\n"
        result += f"Clusters de données        : {info['total_data_clusters']}\n"
        result += f"Secteurs de données        : {info['total_data_sectors']}\n"
        result += f"TOTAL secteurs partition   : {info['total_sectors']}\n"
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

            # Mettre en évidence le cluster sur la cartographie
            self.highlight_cluster(cluster_number)

        except ValueError as e:
            self.cluster_result.insert(1.0, f"Erreur: {str(e)}")
            # Effacer la mise en évidence en cas d'erreur
            self.clear_highlight()

    def search_cluster_from_offset(self):
        """Recherche et affiche le cluster correspondant à un offset."""
        # Effacer le contenu précédent
        self.offset_result.delete(1.0, END)

        if not self.partition:
            self.offset_result.insert(1.0, "Veuillez d'abord calculer les informations de la partition.")
            return

        try:
            # Lire l'offset (support décimal et hexadécimal)
            offset_str = self.offset_entry.get().strip()
            if offset_str.startswith("0x") or offset_str.startswith("0X"):
                offset = int(offset_str, 16)
            else:
                offset = int(offset_str)

            # Obtenir le cluster et la position dans le cluster
            cluster_number, offset_dans_cluster = self.partition.get_cluster_from_offset(offset)

            result = f"Offset {offset} (0x{offset:X}) → Cluster {cluster_number} + {offset_dans_cluster} octets"
            self.offset_result.insert(1.0, result)

            # Mettre en évidence le cluster sur la cartographie
            self.highlight_cluster(cluster_number)

        except ValueError as e:
            self.offset_result.insert(1.0, f"Erreur: {str(e)}")
            # Effacer la mise en évidence en cas d'erreur
            self.clear_highlight()

    def search_fat_index(self):
        """Recherche et affiche l'offset de l'entrée d'un cluster dans la FAT."""
        # Effacer le contenu précédent
        self.fat_result.delete(1.0, END)

        if not self.partition:
            self.fat_result.insert(1.0, "Veuillez d'abord calculer les informations de la partition.")
            return

        try:
            cluster_number = int(self.fat_cluster_entry.get())
            fat_number = int(self.fat_number_var.get())
            offset = self.partition.get_fat_entry_offset(cluster_number, fat_number)

            result = f"Cluster {cluster_number} dans FAT{fat_number} → Offset: {offset} octets (0x{offset:X})"
            self.fat_result.insert(1.0, result)

        except ValueError as e:
            self.fat_result.insert(1.0, f"Erreur: {str(e)}")

    def reset_all(self):
        """Réinitialise toutes les vues et calculs."""
        # Réinitialiser la partition
        self.partition = None

        # Effacer la zone de texte des résultats
        self.results_text.delete(1.0, END)
        self.results_text.insert(1.0, "Veuillez entrer les paramètres et cliquer sur 'Calculer les Informations'")

        # Effacer la cartographie
        self.map_canvas.delete("all")

        # Effacer les zones de recherche
        self.cluster_result.delete(1.0, END)
        self.offset_result.delete(1.0, END)
        self.fat_result.delete(1.0, END)

        # Remettre les valeurs par défaut dans les champs de recherche
        self.cluster_entry.delete(0, END)
        self.cluster_entry.insert(0, "2")

        self.offset_entry.delete(0, END)
        self.offset_entry.insert(0, "270336")

        self.fat_cluster_entry.delete(0, END)
        self.fat_cluster_entry.insert(0, "2")

        self.fat_number_var.set("1")

        # Effacer les highlights
        self.clear_highlight()

        # Réinitialiser les variables de highlight
        self.highlighted_rect = None
        self.highlight_marker = None


def main():
    """Point d'entrée de l'application GUI."""
    # Création de la fenêtre principale avec un thème moderne
    root = ttk.Window(themename="cosmo")
    app = FATCalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
