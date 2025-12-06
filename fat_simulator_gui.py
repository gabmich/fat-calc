"""
FAT Simulator - Application GUI principale
Permet d'ouvrir une image .raw FAT16 et de visualiser/éditer la structure
"""

import sys
import struct
from typing import Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QFileDialog, QLabel,
                              QSplitter, QGroupBox, QScrollArea, QTextEdit,
                              QSpinBox, QComboBox, QMessageBox, QTabWidget,
                              QFrame, QLineEdit, QListWidget, QListWidgetItem, QCheckBox,
                              QProgressDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QPainter, QColor, QPen, QPixmap

from fat16_parser import FAT16Parser, MBRPartition
from hex_viewer import HexViewer
from fat_chain_editor import FATChainEditor
# from fat_table_viewer import FATTableViewer  # Non utilisé - onglet supprimé


class PartitionMapWidget(QWidget):
    """Widget pour visualiser la carte de la partition"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parser: Optional[FAT16Parser] = None
        self.setMinimumHeight(350)
        self.squares_per_row = 80  # Valeur par défaut, sera recalculée
        self.square_size = 10
        self.spacing = 1
        self.highlighted_sectors = []  # Liste de tuples (sector, color, label)
        self.sector_positions = {}  # Mapping secteur -> (x, y)
        self.x_offset = 10
        self.y_offset = 10
        self.empty_sectors = set()  # Cache des secteurs vides (remplis de 0x00)
        self.map_cache = None  # Cache pixmap de la carte
        self.cache_valid = False  # Indique si le cache est valide
        self.last_width = 0  # Pour détecter les vrais changements de taille
        self.last_height = 0

    def set_parser(self, parser: FAT16Parser):
        """Définit le parser FAT16 à visualiser"""
        self.parser = parser
        # Scanner les secteurs vides (une seule fois au chargement)
        self._scan_empty_sectors()
        # Invalider le cache car on a un nouveau parser
        self.cache_valid = False
        # Initialiser last_width pour éviter un rebuild inutile
        self.last_width = self.width()
        self.last_height = self.height()
        self.update()

    def _scan_empty_sectors(self):
        """Scanne les secteurs de données pour identifier ceux qui sont vides (remplis de 0x00)"""
        if not self.parser or not self.parser.boot_sector:
            return

        self.empty_sectors.clear()
        bs = self.parser.boot_sector

        # Scanner uniquement les secteurs de données
        first_data_sector = bs.first_data_sector
        total_sectors = min(bs.total_sectors, 10000)  # Limité comme dans paintEvent

        print(f"[PartitionMap] Scanning empty sectors from {first_data_sector} to {total_sectors}...")
        start_time = __import__('time').time()

        scanned_count = 0
        empty_count = 0

        for sector_num in range(first_data_sector, total_sectors):
            try:
                # Lire le secteur
                sector_data = self.parser.read_sector(sector_num)

                # Vérifier si tous les octets sont à 0x00
                if all(b == 0x00 for b in sector_data):
                    self.empty_sectors.add(sector_num)
                    empty_count += 1

                scanned_count += 1

            except Exception as e:
                # En cas d'erreur, ignorer ce secteur
                print(f"[PartitionMap] Error reading sector {sector_num}: {e}")
                continue

        elapsed = (__import__('time').time() - start_time) * 1000  # en ms
        print(f"[PartitionMap] Scan complete: {scanned_count} sectors scanned, {empty_count} empty sectors found in {elapsed:.1f} ms")

    def calculate_squares_per_row(self):
        """Calcule le nombre de carrés par ligne selon la largeur disponible"""
        widget_width = self.width()
        if widget_width <= 1:
            return 80  # Valeur par défaut

        # Largeur disponible = largeur totale - marges
        available_width = widget_width - (self.x_offset * 2)

        # Nombre de carrés = largeur disponible / (taille carré + espacement)
        squares = max(10, available_width // (self.square_size + self.spacing))

        return squares

    def highlight_positions(self, fat_sector: int, data_sector: int, cluster_number: int):
        """Met en évidence deux positions : entrée FAT et cluster de données"""
        self.highlighted_sectors = [
            (fat_sector, QColor("#8B00FF"), f"FAT ENTRY {cluster_number}"),  # Violet pour FAT
            (data_sector, QColor("#FF0000"), f"CLUSTER {cluster_number}")     # Rouge pour données
        ]
        # Ne PAS invalider le cache - les surbrillances sont dessinées par-dessus
        self.update()  # Juste déclencher un repaint sans invalider le cache

    def clear_highlight(self):
        """Efface la mise en évidence"""
        self.highlighted_sectors = []
        self.update()

    def resizeEvent(self, event):
        """Redessine la carte lors du redimensionnement"""
        super().resizeEvent(event)

        # OPTIMISATION: N'invalider le cache QUE si la largeur a vraiment changé
        # (car la hauteur est calculée automatiquement)
        new_width = self.width()
        new_height = self.height()

        # Tolérance de 5 pixels pour éviter les invalidations inutiles
        width_changed = abs(new_width - self.last_width) > 5

        if width_changed:
            print(f"[PARTITION MAP] resizeEvent: width changed from {self.last_width} to {new_width}, invalidating cache")
            self.cache_valid = False
            self.last_width = new_width
            self.last_height = new_height
            self.update()
        # Sinon, pas besoin de reconstruire le cache

    def paintEvent(self, event):
        """Dessine la carte de la partition avec cache pour meilleures performances"""
        import time
        start = time.time()

        if not self.parser or not self.parser.boot_sector:
            super().paintEvent(event)
            return

        # Si le cache n'est pas valide, le reconstruire
        if not self.cache_valid:
            t1 = time.time()
            self._rebuild_cache()
            print(f"[PARTITION MAP] _rebuild_cache: {(time.time()-t1)*1000:.1f}ms")

        # Dessiner le cache sur le widget
        painter = QPainter(self)
        if self.map_cache:
            painter.drawPixmap(0, 0, self.map_cache)

        # Dessiner les surbrillances PAR-DESSUS le cache
        for sector, highlight_color, label in self.highlighted_sectors:
            if sector in self.sector_positions:
                hx, hy = self.sector_positions[sector]

                # Bordure épaisse
                painter.setPen(QPen(highlight_color, 3))
                painter.drawRect(
                    hx - 2, hy - 2,
                    self.square_size + 4, self.square_size + 4
                )

                # Label au-dessus
                text_x = hx + self.square_size // 2
                text_y = hy - 5

                # Fond du label
                text_rect = painter.fontMetrics().boundingRect(label)
                bg_rect = text_rect.adjusted(-3, -3, 3, 3)
                bg_rect.moveCenter(text_rect.center())
                bg_rect.moveTop(text_y - text_rect.height())
                bg_rect.moveLeft(text_x - text_rect.width() // 2)

                painter.fillRect(bg_rect, highlight_color)
                painter.setPen(QColor("#FFFFFF"))
                painter.drawRect(bg_rect)

                # Texte du label
                painter.setFont(painter.font())
                painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, label)

        painter.end()

        elapsed = (time.time() - start) * 1000
        if elapsed > 10:  # Only print if > 10ms
            print(f"[PARTITION MAP] paintEvent TOTAL: {elapsed:.1f}ms (cache_valid={self.cache_valid})")

    def _rebuild_cache(self):
        """Reconstruit le cache pixmap de la carte (opération lourde)"""
        bs = self.parser.boot_sector

        # Calculer dynamiquement le nombre de carrés par ligne
        self.squares_per_row = self.calculate_squares_per_row()

        current_x = self.x_offset
        current_y = self.y_offset

        total_sectors = bs.total_sectors
        current_sector = 0
        square_index = 0

        # Couleurs
        colors = {
            'boot': QColor("#FFD700"),      # Jaune
            'reserved': QColor("#FF4444"),  # Rouge
            'fat1': QColor("#90EE90"),      # Vert clair
            'fat2': QColor("#006400"),      # Vert foncé
            'root': QColor("#FFA500"),      # Orange
            'data': QColor("#4169E1"),      # Bleu royal (données pleines)
            'data_empty': QColor("#87CEEB") # Bleu clair (données vides)
        }

        # Effacer le mapping des positions
        self.sector_positions.clear()

        # Calculer la taille nécessaire du pixmap
        # On doit d'abord calculer la hauteur finale
        temp_y = current_y
        temp_sector = 0
        temp_index = 0
        while temp_sector < total_sectors and temp_sector <= 10000:
            if temp_index % self.squares_per_row == 0 and temp_index > 0:
                temp_y += self.square_size + self.spacing
            temp_sector += 1
            temp_index += 1

        total_height = temp_y + self.square_size + 60  # +60 pour la légende
        self.setMinimumHeight(total_height)

        # Créer le pixmap
        self.map_cache = QPixmap(self.width(), total_height)
        self.map_cache.fill(Qt.GlobalColor.white)  # Fond blanc

        # Dessiner dans le pixmap
        cache_painter = QPainter(self.map_cache)

        while current_sector < total_sectors:
            # Déterminer la couleur selon la zone
            if current_sector == 0:
                color = colors['boot']
            elif current_sector < bs.reserved_sectors:
                color = colors['reserved']
            elif current_sector < bs.reserved_sectors + bs.sectors_per_fat:
                color = colors['fat1']
            elif current_sector < bs.reserved_sectors + (2 * bs.sectors_per_fat):
                color = colors['fat2']
            elif current_sector < bs.first_data_sector:
                color = colors['root']
            else:
                # Zone de données : différencier vide vs plein
                if current_sector in self.empty_sectors:
                    color = colors['data_empty']  # Bleu clair pour secteurs vides
                else:
                    color = colors['data']  # Bleu foncé pour secteurs pleins

            # Stocker la position du secteur
            self.sector_positions[current_sector] = (current_x, current_y)

            # Dessiner le carré
            cache_painter.fillRect(
                current_x, current_y,
                self.square_size, self.square_size,
                color
            )

            # Contour
            cache_painter.setPen(QColor("#CCCCCC"))
            cache_painter.drawRect(
                current_x, current_y,
                self.square_size, self.square_size
            )

            # Passer au carré suivant
            current_x += self.square_size + self.spacing
            square_index += 1

            # Nouvelle ligne
            if square_index % self.squares_per_row == 0:
                current_x = self.x_offset
                current_y += self.square_size + self.spacing

            current_sector += 1

            # Limiter le nombre de secteurs affichés pour la performance
            if current_sector > 10000:
                break

        # Légende
        legend_y = current_y + 20
        legend_x = self.x_offset

        legends = [
            ('Boot', colors['boot']),
            ('Reserved', colors['reserved']),
            ('FAT1', colors['fat1']),
            ('FAT2', colors['fat2']),
            ('Root', colors['root']),
            ('Data (full)', colors['data']),
            ('Data (empty)', colors['data_empty'])
        ]

        for label, color in legends:
            # Carré de couleur
            cache_painter.fillRect(legend_x, legend_y, 15, 15, color)
            cache_painter.setPen(QColor("#000000"))
            cache_painter.drawRect(legend_x, legend_y, 15, 15)

            # Label
            cache_painter.drawText(legend_x + 20, legend_y + 12, label)
            legend_x += 110

        cache_painter.end()

        # Marquer le cache comme valide
        self.cache_valid = True


class SearchWorker(QThread):
    """Thread worker pour effectuer la recherche textuelle en arrière-plan"""

    # Signaux pour communiquer avec le thread principal
    progress_update = pyqtSignal(int, int)  # (current, total)
    result_found = pyqtSignal(dict)  # Émet chaque résultat trouvé
    search_finished = pyqtSignal(int)  # Émet le nombre total de résultats

    def __init__(self, parser, search_text, case_sensitive, max_results=100):
        super().__init__()
        self.parser = parser
        self.search_text = search_text
        self.case_sensitive = case_sensitive
        self.max_results = max_results
        self.cancelled = False
        self.results_count = 0

    def cancel(self):
        """Annuler la recherche"""
        self.cancelled = True

    def run(self):
        """Exécute la recherche dans un thread séparé"""
        try:
            bs = self.parser.boot_sector

            # Encoder le texte de recherche
            search_bytes = self.search_text.encode('utf-8')
            if not self.case_sensitive:
                search_bytes = search_bytes.lower()

            data_start_offset = bs.first_data_sector * bs.bytes_per_sector
            cluster_size = bs.sectors_per_cluster * bs.bytes_per_sector

            # 1. Chercher dans le Root Directory
            if not self.cancelled:
                try:
                    root_data = self.parser.read_root_directory()
                    root_offset = (bs.reserved_sectors + bs.num_fats * bs.sectors_per_fat) * bs.bytes_per_sector

                    search_root_data = root_data if self.case_sensitive else root_data.lower()
                    offset = 0
                    while True and self.results_count < self.max_results and not self.cancelled:
                        pos = search_root_data.find(search_bytes, offset)
                        if pos == -1:
                            break

                        absolute_offset = root_offset + pos
                        context_start = max(0, pos - 20)
                        context_end = min(len(root_data), pos + len(search_bytes) + 20)
                        context = root_data[context_start:context_end]
                        context_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in context)

                        result = {
                            'cluster': 'ROOT',
                            'offset': absolute_offset,
                            'position_in_cluster': pos,
                            'match_length': len(search_bytes),
                            'context': context_str,
                            'root_data': root_data
                        }

                        self.result_found.emit(result)
                        self.results_count += 1
                        offset = pos + 1

                except Exception as e:
                    print(f"Erreur lors de la recherche dans le Root Directory: {e}")

            # 2. Parcourir tous les clusters
            total_clusters = bs.total_clusters
            for cluster_num in range(2, total_clusters + 2):
                if self.cancelled or self.results_count >= self.max_results:
                    break

                # Émettre la progression tous les 50 clusters
                if (cluster_num - 2) % 50 == 0:
                    self.progress_update.emit(cluster_num - 2, total_clusters)

                try:
                    cluster_data = self.parser.read_cluster(cluster_num)
                    search_data = cluster_data if self.case_sensitive else cluster_data.lower()

                    offset = 0
                    while True:
                        pos = search_data.find(search_bytes, offset)
                        if pos == -1:
                            break

                        cluster_offset = (cluster_num - 2) * cluster_size
                        absolute_offset = data_start_offset + cluster_offset + pos

                        context_start = max(0, pos - 20)
                        context_end = min(len(cluster_data), pos + len(search_bytes) + 20)
                        context = cluster_data[context_start:context_end]
                        context_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in context)

                        result = {
                            'cluster': cluster_num,
                            'offset': absolute_offset,
                            'position_in_cluster': pos,
                            'match_length': len(search_bytes),
                            'context': context_str
                        }

                        self.result_found.emit(result)
                        self.results_count += 1

                        if self.results_count >= self.max_results:
                            break

                        offset = pos + 1

                except Exception:
                    continue

            # Émettre la progression finale
            self.progress_update.emit(total_clusters, total_clusters)

        except Exception as e:
            print(f"Erreur dans le thread de recherche: {e}")

        finally:
            # Toujours émettre le signal de fin
            self.search_finished.emit(self.results_count)


class FATSimulatorGUI(QMainWindow):
    """Application principale du simulateur FAT"""

    def __init__(self):
        super().__init__()
        self.parser: Optional[FAT16Parser] = None
        self.fat_data: bytes = b''
        self.current_cluster: int = 2
        self.search_worker = None
        self.search_progress_dialog = None
        self.search_results = []
        self.setup_ui()

    def setup_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("FAT16 Simulator - Forensic Analysis Tool")
        self.setGeometry(100, 100, 1400, 900)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Fichier")

        open_action = QAction("Ouvrir Image .raw", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_raw_image)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        quit_action = QAction("Quitter", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)  # Marges minimales
        main_layout.setSpacing(5)  # Espacement minimal
        central_widget.setLayout(main_layout)

        # Barre d'outils en haut (compacte)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(10)

        self.open_button = QPushButton("📂 Ouvrir Image .raw")
        self.open_button.clicked.connect(self.open_raw_image)
        self.open_button.setMaximumHeight(30)  # Limiter la hauteur
        toolbar_layout.addWidget(self.open_button)

        self.save_modifications_button = QPushButton("💾 Enregistrer les Modifications")
        self.save_modifications_button.clicked.connect(self.save_hex_modifications)
        self.save_modifications_button.setMaximumHeight(30)
        self.save_modifications_button.setEnabled(False)  # Désactivé par défaut
        self.save_modifications_button.setStyleSheet("QPushButton:enabled { background-color: #FF9800; color: white; font-weight: bold; }")
        toolbar_layout.addWidget(self.save_modifications_button)

        self.status_label = QLabel("Aucune image chargée")
        self.status_label.setStyleSheet("font-weight: bold;")  # Retirer le padding
        self.status_label.setMaximumHeight(30)
        toolbar_layout.addWidget(self.status_label)

        toolbar_layout.addStretch()

        main_layout.addLayout(toolbar_layout)

        # Splitter principal horizontal (3 colonnes)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # === COLONNE GAUCHE: Informations + Éditeur de chaîne ===
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Informations de la partition
        info_group = QGroupBox("Informations de la Partition")
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(5, 5, 5, 5)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        # Pas de limitation de hauteur, prend toute la place disponible
        info_layout.addWidget(self.info_text)

        info_group.setLayout(info_layout)
        left_layout.addWidget(info_group, 2)  # Stretch factor = 2 (plus d'espace)

        # Section de recherche de cluster unifiée (compacte)
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        search_frame.setStyleSheet("background-color: #E8F4F8; padding: 5px;")
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(8, 5, 8, 5)

        search_layout.addWidget(QLabel("🔍 Recherche cluster:"))
        self.search_cluster_input = QLineEdit()
        self.search_cluster_input.setPlaceholderText("Ex: 2, 0x02, 0200")
        self.search_cluster_input.setMaximumWidth(100)
        self.search_cluster_input.returnPressed.connect(self.unified_cluster_search)
        search_layout.addWidget(self.search_cluster_input)

        self.search_format_combo = QComboBox()
        self.search_format_combo.addItems(["Décimal", "Hexadécimal", "Little Endian", "Big Endian"])
        self.search_format_combo.setMaximumWidth(120)
        search_layout.addWidget(self.search_format_combo)

        self.search_button = QPushButton("🔍 Chercher")
        self.search_button.clicked.connect(self.unified_cluster_search)
        search_layout.addWidget(self.search_button)

        # Zone de résultat compacte (1 ligne, sélectionnable)
        self.search_result_label = QLineEdit("Entrez un numéro de cluster pour voir ses informations")
        self.search_result_label.setReadOnly(True)
        self.search_result_label.setStyleSheet("QLineEdit { color: #666; font-size: 9pt; background-color: transparent; border: none; }")
        search_layout.addWidget(self.search_result_label, 1)

        search_frame.setLayout(search_layout)
        left_layout.addWidget(search_frame)

        # Section de recherche de texte
        text_search_frame = QFrame()
        text_search_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        text_search_frame.setStyleSheet("background-color: #FFF3E0; padding: 5px;")
        text_search_layout = QVBoxLayout()
        text_search_layout.setContentsMargins(8, 5, 8, 5)
        text_search_layout.setSpacing(5)

        # Ligne de recherche
        search_input_layout = QHBoxLayout()
        search_input_layout.addWidget(QLabel("🔎 Recherche texte:"))
        self.text_search_input = QLineEdit()
        self.text_search_input.setPlaceholderText("Texte à rechercher...")
        self.text_search_input.returnPressed.connect(self.search_text_in_data)
        search_input_layout.addWidget(self.text_search_input)

        self.text_search_button = QPushButton("🔎 Chercher")
        self.text_search_button.clicked.connect(self.search_text_in_data)
        search_input_layout.addWidget(self.text_search_button)

        # Case à cocher pour la sensibilité à la casse
        self.case_sensitive_checkbox = QCheckBox("Sensible à la casse")
        self.case_sensitive_checkbox.setChecked(False)  # Décochée par défaut
        search_input_layout.addWidget(self.case_sensitive_checkbox)

        text_search_layout.addLayout(search_input_layout)

        # Zone de résultats (scrollable, hauteur limitée)
        self.text_search_results = QListWidget()
        self.text_search_results.setMaximumHeight(120)
        self.text_search_results.itemClicked.connect(self.on_text_search_result_clicked)
        self.text_search_results.currentItemChanged.connect(self.on_text_search_result_changed)
        self.text_search_results.setStyleSheet("QListWidget { background-color: white; border: 1px solid #FFB74D; }")
        text_search_layout.addWidget(self.text_search_results)

        text_search_frame.setLayout(text_search_layout)
        left_layout.addWidget(text_search_frame)

        # Éditeur de chaîne
        chain_group = QGroupBox("Éditeur de Chaîne FAT")
        chain_group_layout = QVBoxLayout()
        chain_group_layout.setContentsMargins(5, 5, 5, 5)

        self.chain_editor = FATChainEditor()
        self.chain_editor.cluster_selected.connect(self.on_chain_cluster_selected)
        self.chain_editor.chain_modified.connect(self.on_chain_modified)
        self.chain_editor.save_requested.connect(self.save_fat_chain)
        chain_group_layout.addWidget(self.chain_editor)

        chain_group.setLayout(chain_group_layout)
        left_layout.addWidget(chain_group, 1)  # Stretch factor = 1 (1/3 de l'espace)

        left_panel.setLayout(left_layout)
        main_splitter.addWidget(left_panel)

        # === COLONNE MILIEU: Hex viewer (1/3 de la largeur, toute la hauteur) ===
        hex_group = QGroupBox("Contenu du Cluster Sélectionné")
        hex_layout = QVBoxLayout()
        hex_layout.setContentsMargins(5, 5, 5, 5)

        # Contrôle pour ajuster le nombre d'octets par ligne
        hex_control_layout = QHBoxLayout()
        hex_control_layout.addWidget(QLabel("Octets/ligne:"))
        self.bytes_per_line_combo = QComboBox()
        self.bytes_per_line_combo.addItems(["8", "16", "32"])
        self.bytes_per_line_combo.setCurrentText("8")
        self.bytes_per_line_combo.currentTextChanged.connect(self.on_bytes_per_line_changed)
        self.bytes_per_line_combo.setMaximumWidth(80)
        hex_control_layout.addWidget(self.bytes_per_line_combo)
        hex_control_layout.addStretch()
        hex_layout.addLayout(hex_control_layout)

        self.chain_hex_viewer = HexViewer(bytes_per_line=8)
        self.chain_hex_viewer.set_title("Sélectionnez un cluster pour voir son contenu")
        # Connecter le signal de changement du mode édition pour activer/désactiver le bouton de sauvegarde
        self.chain_hex_viewer.edit_checkbox.stateChanged.connect(self.on_edit_mode_changed)
        hex_layout.addWidget(self.chain_hex_viewer)

        hex_group.setLayout(hex_layout)
        main_splitter.addWidget(hex_group)

        # === COLONNE DROITE: Carte de la partition (1/3 de la largeur) ===
        map_group = QGroupBox("Carte de la Partition")
        map_layout = QVBoxLayout()
        map_layout.setContentsMargins(5, 5, 5, 5)

        self.partition_map = PartitionMapWidget()
        self.map_scroll_area = QScrollArea()
        self.map_scroll_area.setWidget(self.partition_map)
        self.map_scroll_area.setWidgetResizable(True)  # True pour adapter la largeur
        self.map_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.map_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Pas de scroll horizontal
        map_layout.addWidget(self.map_scroll_area)

        map_group.setLayout(map_layout)
        main_splitter.addWidget(map_group)

        # Proportions: gauche=2, milieu=1, droite=1 (50%, 25%, 25%)
        main_splitter.setSizes([600, 300, 300])

        main_layout.addWidget(main_splitter, 1)  # Stretch factor = 1 pour prendre toute la place

    def reset_ui(self):
        """Réinitialise l'interface utilisateur"""
        # Effacer l'éditeur de chaîne (sans confirmation)
        self.chain_editor.set_chain([])
        self.chain_editor.set_search_result("Recherchez un cluster pour voir ses offsets")

        # Effacer le hex viewer
        self.chain_hex_viewer.clear()
        self.chain_hex_viewer.set_title("Sélectionnez un cluster pour voir son contenu")

        # Effacer le champ de recherche
        self.search_cluster_input.clear()
        self.search_result_label.setText("Entrez un numéro de cluster pour voir ses informations")
        self.search_result_label.setStyleSheet("color: #666; font-size: 9pt; padding: 2px;")

        # Effacer la recherche de texte
        self.text_search_input.clear()
        self.text_search_results.clear()

        # Effacer les mises en évidence sur la cartographie
        self.partition_map.clear_highlight()

    def open_raw_image(self):
        """Ouvre une image .raw"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir une image disque",
            "",
            "Images disque (*.raw *.img *.dd);;Tous les fichiers (*)"
        )

        if not file_path:
            return

        # Réinitialiser l'interface avant de charger une nouvelle image
        self.reset_ui()

        try:
            # Ouvrir le parser
            self.parser = FAT16Parser(file_path)
            self.parser.open()

            # Lire le MBR
            partitions = self.parser.read_mbr()

            # Chercher une partition FAT16
            fat16_partition = None
            for partition in partitions:
                if partition.is_fat16():
                    fat16_partition = partition
                    break

            if fat16_partition:
                # Lire le boot sector de la partition
                offset = fat16_partition.start_lba * 512
                self.parser.read_boot_sector(offset)
            else:
                # Essayer de lire directement comme une image de partition
                self.parser.read_boot_sector(0)

            # Configurer le hex viewer avec la taille des secteurs
            if self.parser.boot_sector:
                self.chain_hex_viewer.set_bytes_per_sector(self.parser.boot_sector.bytes_per_sector)

            # Lire la FAT
            self.fat_data = self.parser.read_fat(1)

            # Afficher les informations
            self.display_partition_info()

            # Mettre à jour la carte
            self.partition_map.set_parser(self.parser)

            # Mettre à jour le statut
            self.status_label.setText(f"✓ Image chargée: {file_path}")
            self.status_label.setStyleSheet("padding: 5px; font-weight: bold; color: green;")

            # Activer les contrôles
            self.enable_controls(True)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir l'image:\n{str(e)}")
            self.status_label.setText("❌ Erreur lors du chargement")
            self.status_label.setStyleSheet("padding: 5px; font-weight: bold; color: red;")

    def display_partition_info(self):
        """Affiche les informations de la partition"""
        if not self.parser or not self.parser.boot_sector:
            return

        info = self.parser.get_info_dict()
        bs = self.parser.boot_sector

        detected_type = info.get('detected_fat_type', 'Unknown')
        text = "=" * 60 + "\n"
        text += f"INFORMATIONS DE LA PARTITION {detected_type}\n"
        text += "=" * 60 + "\n\n"

        text += f"Type détecté:              {detected_type}\n"
        text += f"Type de système (boot):    {info['fs_type']}\n"
        text += f"Label du volume:           {info['volume_label']}\n"
        text += f"ID du volume:              {info['volume_id']}\n\n"

        text += f"Octets par secteur:        {info['bytes_per_sector']}\n"
        text += f"Secteurs par cluster:      {info['sectors_per_cluster']}\n"
        text += f"Secteurs réservés:         {info['reserved_sectors']}\n"
        text += f"Nombre de FATs:            {info['num_fats']}\n"
        text += f"Secteurs par FAT:          {info['sectors_per_fat']}\n"
        text += f"Entrées root directory:    {info['root_entries']}\n\n"

        text += "-" * 60 + "\n"
        text += f"Secteurs root directory:   {info['root_dir_sectors']}\n"
        text += f"Premier secteur données:   {info['first_data_sector']}\n"
        text += f"Secteurs de données:       {info['data_sectors']}\n"
        text += f"Clusters totaux:           {info['total_clusters']}\n"
        text += f"Secteurs totaux:           {info['total_sectors']}\n"
        text += "=" * 60 + "\n\n"

        # Informations sur les zones
        text += "CARTOGRAPHIE DES ZONES (en secteurs)\n"
        text += "-" * 60 + "\n"
        text += f"Boot Sector:               0\n"
        text += f"Reserved Sectors:          1 - {bs.reserved_sectors - 1}\n"
        text += f"FAT 1:                     {bs.reserved_sectors} - {bs.reserved_sectors + bs.sectors_per_fat - 1}\n"
        text += f"FAT 2:                     {bs.reserved_sectors + bs.sectors_per_fat} - {bs.reserved_sectors + 2*bs.sectors_per_fat - 1}\n"
        text += f"Root Directory:            {bs.reserved_sectors + 2*bs.sectors_per_fat} - {bs.first_data_sector - 1}\n"
        text += f"Data Zone:                 {bs.first_data_sector}+\n"

        self.info_text.setPlainText(text)

    # Méthodes update_hex_view_controls et display_hex_view supprimées
    # (onglet Hex Viewer standalone supprimé)

    def save_fat_chain(self):
        """Sauvegarde la chaîne FAT modifiée dans l'image"""
        # TODO: Implémenter la sauvegarde réelle dans le fichier .raw
        QMessageBox.information(
            self,
            "Non implémenté",
            "La sauvegarde des modifications n'est pas encore implémentée.\n"
            "Cette fonctionnalité sera ajoutée dans une future version."
        )

    def on_chain_modified(self, chain: list):
        """Callback quand la chaîne FAT est modifiée"""
        # Pour l'instant, juste afficher un message
        print(f"Chaîne modifiée: {chain}")

    # Méthodes on_fat_table_* supprimées (onglet Table FAT supprimé)

    def on_bytes_per_line_changed(self, value: str):
        """Callback quand le nombre d'octets par ligne change"""
        bytes_per_line = int(value)
        self.chain_hex_viewer.set_bytes_per_line(bytes_per_line)

    def on_edit_mode_changed(self, state):
        """Callback quand le mode édition change"""
        # Activer le bouton de sauvegarde seulement si le mode édition est activé
        self.save_modifications_button.setEnabled(self.chain_hex_viewer.edit_mode)

    def on_chain_cluster_selected(self, cluster_number: int):
        """Callback quand un cluster est sélectionné dans la chaîne"""
        # Afficher le contenu du cluster dans le hex viewer de l'onglet chaîne
        if not self.parser:
            return

        try:
            bs = self.parser.boot_sector

            # Lire le contenu du cluster
            data = self.parser.read_cluster(cluster_number)
            offset = bs.first_data_sector * bs.bytes_per_sector
            offset += (cluster_number - 2) * bs.sectors_per_cluster * bs.bytes_per_sector

            # Afficher dans le hex viewer de la chaîne (sans highlights)
            self.chain_hex_viewer.highlight_ranges = []  # Effacer les highlights avant d'afficher
            self.chain_hex_viewer.set_title(f"Cluster {cluster_number} (Offset: 0x{offset:X})")
            self.chain_hex_viewer.set_data(data, offset)

            # Calculer les secteurs pour la mise en évidence
            # 1. Secteur de l'entrée FAT (dans FAT1)
            fat_entry_offset = bs.reserved_sectors * bs.bytes_per_sector + (cluster_number * 2)
            fat_sector = fat_entry_offset // bs.bytes_per_sector

            # 2. Secteur du cluster de données
            data_sector = bs.first_data_sector + (cluster_number - 2) * bs.sectors_per_cluster

            # Mettre en évidence dans la cartographie
            self.partition_map.highlight_positions(fat_sector, data_sector, cluster_number)

            # Scroller jusqu'au cluster dans la carte
            if data_sector in self.partition_map.sector_positions:
                hx, hy = self.partition_map.sector_positions[data_sector]
                # Centrer le cluster dans la vue
                self.map_scroll_area.ensureVisible(hx, hy, 100, 100)

        except Exception as e:
            self.chain_hex_viewer.set_title(f"Erreur: {str(e)}")
            self.chain_hex_viewer.clear()
            self.partition_map.clear_highlight()

    def unified_cluster_search(self):
        """Recherche unifiée : charge chaîne + calcule offsets + mise en évidence"""
        # Vider les résultats et le champ de recherche de texte
        self.text_search_results.clear()
        self.text_search_input.clear()

        if not self.parser or not self.fat_data:
            error_msg = "❌ Veuillez d'abord ouvrir une image .raw"
            self.chain_editor.set_search_result(error_msg)
            self.search_result_label.setText(error_msg)
            self.search_result_label.setStyleSheet("QLineEdit { color: #D32F2F; font-weight: bold; font-size: 9pt; background-color: transparent; border: none; }")
            return

        try:
            bs = self.parser.boot_sector
            input_value = self.search_cluster_input.text().strip()

            if not input_value:
                error_msg = "❌ Veuillez entrer un numéro de cluster"
                self.chain_editor.set_search_result(error_msg)
                self.search_result_label.setText(error_msg)
                self.search_result_label.setStyleSheet("QLineEdit { color: #D32F2F; font-weight: bold; font-size: 9pt; background-color: transparent; border: none; }")
                return

            # Déterminer le format et convertir
            format_choice = self.search_format_combo.currentText()

            if format_choice == "Décimal":
                cluster_number = int(input_value)
            elif format_choice == "Hexadécimal":
                # Accepter avec ou sans préfixe 0x
                if input_value.startswith("0x") or input_value.startswith("0X"):
                    cluster_number = int(input_value, 16)
                else:
                    cluster_number = int(input_value, 16)
            elif format_choice == "Little Endian":
                # Format Little Endian : "0200" signifie 0x0002
                if len(input_value) % 2 != 0:
                    input_value = "0" + input_value
                byte_list = bytes.fromhex(input_value)
                cluster_number = int.from_bytes(byte_list, byteorder='little')
            elif format_choice == "Big Endian":
                # Format Big Endian : "0002" signifie 0x0002
                if len(input_value) % 2 != 0:
                    input_value = "0" + input_value
                byte_list = bytes.fromhex(input_value)
                cluster_number = int.from_bytes(byte_list, byteorder='big')
            else:
                raise ValueError("Format inconnu")

            # Valider le cluster
            if cluster_number < 2:
                error_msg = "❌ Le numéro de cluster doit être >= 2"
                self.chain_editor.set_search_result(error_msg)
                self.search_result_label.setText(error_msg)
                self.search_result_label.setStyleSheet("QLineEdit { color: #D32F2F; font-weight: bold; font-size: 9pt; background-color: transparent; border: none; }")
                return

            # 1. Charger la chaîne FAT
            chain = self.parser.parse_fat_chain(self.fat_data, cluster_number)
            self.chain_editor.set_chain(chain)

            # 2. Calculer les offsets
            fat_entry_offset = bs.reserved_sectors * bs.bytes_per_sector + (cluster_number * 2)
            data_offset = bs.first_data_sector * bs.bytes_per_sector
            data_offset += (cluster_number - 2) * bs.sectors_per_cluster * bs.bytes_per_sector

            # Calculer les secteurs
            fat_sector = fat_entry_offset // bs.bytes_per_sector
            data_sector = bs.first_data_sector + (cluster_number - 2) * bs.sectors_per_cluster

            # 3. Afficher résultat dans l'éditeur de chaîne
            result = f"✅ Cluster {cluster_number} | FAT Entry: {fat_entry_offset} (0x{fat_entry_offset:X}) | Data Offset: {data_offset} (0x{data_offset:X}) | Chaîne: {len(chain)} cluster(s)"
            self.chain_editor.set_search_result(result)

            # Message court dans la barre de recherche
            self.search_result_label.setText(f"✅ Cluster {cluster_number} trouvé")
            self.search_result_label.setStyleSheet("QLineEdit { color: #1B5E20; font-weight: bold; font-size: 9pt; background-color: transparent; border: none; }")

            # 4. Mettre en évidence dans la cartographie
            self.partition_map.highlight_positions(fat_sector, data_sector, cluster_number)

            # Scroller jusqu'au cluster dans la carte
            if data_sector in self.partition_map.sector_positions:
                hx, hy = self.partition_map.sector_positions[data_sector]
                # Centrer le cluster dans la vue
                self.map_scroll_area.ensureVisible(hx, hy, 100, 100)

        except ValueError as e:
            error_msg = f"❌ Erreur de format: {str(e)}"
            self.chain_editor.set_search_result(error_msg)
            self.search_result_label.setText("❌ Erreur de format")
            self.search_result_label.setStyleSheet("QLineEdit { color: #D32F2F; font-weight: bold; font-size: 9pt; background-color: transparent; border: none; }")
            self.partition_map.clear_highlight()
        except Exception as e:
            error_msg = f"❌ Erreur: {str(e)}"
            self.chain_editor.set_search_result(error_msg)
            self.search_result_label.setText("❌ Erreur")
            self.search_result_label.setStyleSheet("QLineEdit { color: #D32F2F; font-weight: bold; font-size: 9pt; background-color: transparent; border: none; }")
            self.partition_map.clear_highlight()

    def search_text_in_data(self):
        """Recherche un texte dans la zone de données de la partition"""
        if not self.parser:
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord ouvrir une image .raw")
            return

        search_text = self.text_search_input.text()
        if not search_text:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un texte à rechercher")
            return

        # Si une recherche est déjà en cours, l'annuler
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.cancel()
            self.search_worker.wait()

        # Effacer les résultats précédents
        self.text_search_results.clear()
        self.search_results = []

        # Vider le champ de recherche de cluster et son résultat
        self.search_cluster_input.clear()
        self.search_result_label.setText("Entrez un numéro de cluster pour voir ses informations")
        self.search_result_label.setStyleSheet("QLineEdit { color: #666; font-size: 9pt; background-color: transparent; border: none; }")

        try:
            case_sensitive = self.case_sensitive_checkbox.isChecked()
            max_results = 100

            # Créer le worker thread
            self.search_worker = SearchWorker(self.parser, search_text, case_sensitive, max_results)

            # Connecter les signaux
            self.search_worker.progress_update.connect(self.on_search_progress)
            self.search_worker.result_found.connect(self.on_search_result_found)
            self.search_worker.search_finished.connect(self.on_search_finished)

            # Créer et afficher la boîte de dialogue de progression
            total_clusters = self.parser.boot_sector.total_clusters
            self.search_progress_dialog = QProgressDialog(
                "Recherche en cours...",
                "Annuler",
                0,
                total_clusters,
                self
            )
            self.search_progress_dialog.setWindowTitle("Recherche textuelle")
            self.search_progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.search_progress_dialog.canceled.connect(self.on_search_cancelled)
            self.search_progress_dialog.setMinimumDuration(0)  # Afficher immédiatement
            self.search_progress_dialog.setValue(0)

            # Démarrer la recherche
            self.search_worker.start()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du démarrage de la recherche:\n{str(e)}")

    def on_search_progress(self, current, total):
        """Mise à jour de la progression de la recherche"""
        if self.search_progress_dialog and not self.search_progress_dialog.wasCanceled():
            try:
                self.search_progress_dialog.setValue(current)
                self.search_progress_dialog.setLabelText(f"Recherche en cours... ({current}/{total} clusters)")
            except (AttributeError, RuntimeError):
                # La boîte de dialogue a été fermée, ignorer
                pass

    def on_search_result_found(self, result):
        """Callback quand un résultat est trouvé"""
        self.search_results.append(result)
        item_text = f"Cluster {result['cluster']} @ 0x{result['offset']:08X} ({result['offset']}) - ...{result['context']}..."
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, result)
        self.text_search_results.addItem(item)

    def on_search_finished(self, results_count):
        """Callback quand la recherche est terminée"""
        # Déconnecter les signaux pour éviter les mises à jour tardives
        if self.search_worker:
            try:
                self.search_worker.progress_update.disconnect()
                self.search_worker.result_found.disconnect()
                self.search_worker.search_finished.disconnect()
            except (TypeError, RuntimeError):
                # Signaux déjà déconnectés, ignorer
                pass

        # Fermer la boîte de dialogue de progression
        if self.search_progress_dialog:
            try:
                self.search_progress_dialog.close()
            except (AttributeError, RuntimeError):
                pass
            self.search_progress_dialog = None

        # Sélectionner le premier résultat si disponible
        if results_count > 0:
            self.text_search_results.setCurrentRow(0)
            max_results = 100
            QMessageBox.information(
                self,
                "Recherche terminée",
                f"✅ {results_count} occurrence(s) trouvée(s)" +
                (f"\n(Limité aux {max_results} premières)" if results_count >= max_results else "")
            )
        else:
            QMessageBox.information(self, "Recherche terminée", "❌ Aucune occurrence trouvée")

    def on_search_cancelled(self):
        """Callback quand l'utilisateur annule la recherche"""
        if self.search_worker:
            self.search_worker.cancel()
            # Attendre que le thread se termine proprement
            self.search_worker.wait()

    def on_text_search_result_changed(self, current_item, previous_item):
        """Callback quand la sélection d'un résultat change (clic ou navigation clavier)"""
        if current_item:
            self.on_text_search_result_clicked(current_item)

    def on_text_search_result_clicked(self, item):
        """Callback quand un résultat de recherche est cliqué"""
        if not item:
            return

        result = item.data(Qt.ItemDataRole.UserRole)
        if not result:
            return

        import time
        start_time = time.time()

        try:
            bs = self.parser.boot_sector
            cluster_num = result['cluster']
            absolute_offset = result['offset']

            print(f"\n[PERF] Clic sur résultat - Cluster {cluster_num}")

            # Cas spécial : résultat dans le Root Directory
            if cluster_num == 'ROOT':
                # 1. Pas de chaîne FAT pour le root directory
                self.chain_editor.set_chain([])

                # 2. Afficher le root directory dans le hex viewer
                root_data = result.get('root_data', b'')
                root_offset = (bs.reserved_sectors + bs.num_fats * bs.sectors_per_fat) * bs.bytes_per_sector

                self.chain_hex_viewer.set_title(f"Root Directory (Offset: 0x{root_offset:X}) - Résultat de recherche")
                self.chain_hex_viewer.set_data(root_data, root_offset)

                # 2b. Mettre en évidence le texte trouvé
                position = result['position_in_cluster']
                match_length = result.get('match_length', 0)
                if match_length > 0:
                    self.chain_hex_viewer.highlight_range(position, match_length)

                # 3. Mettre en évidence le root directory dans la carte
                root_start_sector = bs.reserved_sectors + bs.num_fats * bs.sectors_per_fat
                self.partition_map.clear_highlight()
                # On pourrait mettre en évidence le root directory ici si besoin

                # 4. Afficher le résultat
                result_msg = f"✅ ROOT DIRECTORY | Offset: {absolute_offset} (0x{absolute_offset:X}) | Position: {position}"
                self.chain_editor.set_search_result(result_msg)

            else:
                # Cas normal : résultat dans un cluster de données
                # 1. Trouver le début de la chaîne FAT et charger toute la chaîne
                t1 = time.time()
                # D'abord, trouver le premier cluster de la chaîne
                chain_start = self.parser.find_chain_start(self.fat_data, cluster_num)
                print(f"[PERF]   find_chain_start: {(time.time()-t1)*1000:.1f}ms (found {chain_start} from {cluster_num})")

                # Ensuite, parser toute la chaîne depuis le début
                t1b = time.time()
                chain = self.parser.parse_fat_chain(self.fat_data, chain_start)
                self.chain_editor.set_chain(chain)
                print(f"[PERF]   parse_fat_chain + set_chain: {(time.time()-t1b)*1000:.1f}ms (total chain: {len(chain)} clusters)")

                # 2. Lire et afficher le contenu du cluster dans le hex viewer
                t2 = time.time()
                cluster_data = self.parser.read_cluster(cluster_num)
                print(f"[PERF]   read_cluster: {(time.time()-t2)*1000:.1f}ms")

                cluster_offset = bs.first_data_sector * bs.bytes_per_sector + (cluster_num - 2) * bs.sectors_per_cluster * bs.bytes_per_sector

                t3 = time.time()
                self.chain_hex_viewer.set_title(f"Cluster {cluster_num} (Offset: 0x{cluster_offset:X}) - Résultat de recherche")
                print(f"[PERF]   set_title: {(time.time()-t3)*1000:.1f}ms")

                t4 = time.time()
                self.chain_hex_viewer.set_data(cluster_data, cluster_offset)
                print(f"[PERF]   set_data (HEX VIEWER): {(time.time()-t4)*1000:.1f}ms")

                # 2b. Mettre en évidence le texte trouvé dans le hex viewer
                position_in_cluster = result['position_in_cluster']
                match_length = result.get('match_length', 0)
                if match_length > 0:
                    t5 = time.time()
                    self.chain_hex_viewer.highlight_range(position_in_cluster, match_length)
                    print(f"[PERF]   highlight_range: {(time.time()-t5)*1000:.1f}ms")

                # 3. Calculer les secteurs pour la mise en évidence
                fat_entry_offset = bs.reserved_sectors * bs.bytes_per_sector + (cluster_num * 2)
                fat_sector = fat_entry_offset // bs.bytes_per_sector
                data_sector = bs.first_data_sector + (cluster_num - 2) * bs.sectors_per_cluster

                # 4. Mettre en évidence dans la cartographie
                t6 = time.time()
                self.partition_map.highlight_positions(fat_sector, data_sector, cluster_num)
                print(f"[PERF]   partition_map.highlight_positions: {(time.time()-t6)*1000:.1f}ms")

                # 5. Scroller jusqu'au cluster dans la carte
                if data_sector in self.partition_map.sector_positions:
                    t7 = time.time()
                    hx, hy = self.partition_map.sector_positions[data_sector]
                    self.map_scroll_area.ensureVisible(hx, hy, 100, 100)
                    print(f"[PERF]   ensureVisible: {(time.time()-t7)*1000:.1f}ms")

                # 6. Afficher le résultat dans l'éditeur de chaîne
                t8 = time.time()
                result_msg = f"✅ Cluster {cluster_num} | Offset: {absolute_offset} (0x{absolute_offset:X}) | Position dans cluster: {result['position_in_cluster']}"
                self.chain_editor.set_search_result(result_msg)
                print(f"[PERF]   set_search_result: {(time.time()-t8)*1000:.1f}ms")

            print(f"[PERF] TOTAL: {(time.time()-start_time)*1000:.1f}ms\n")

        except Exception as e:
            print(f"[PERF] ERREUR après {(time.time()-start_time)*1000:.1f}ms: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'affichage du résultat:\n{str(e)}")

    def enable_controls(self, enabled: bool):
        """Active ou désactive les contrôles"""
        self.search_button.setEnabled(enabled)
        self.search_cluster_input.setEnabled(enabled)
        self.search_format_combo.setEnabled(enabled)
        self.text_search_button.setEnabled(enabled)
        self.text_search_input.setEnabled(enabled)
        self.case_sensitive_checkbox.setEnabled(enabled)

    def save_hex_modifications(self):
        """Enregistre les modifications hexadécimales dans le fichier image"""
        if not self.parser:
            QMessageBox.warning(self, "Erreur", "Aucune image n'est chargée")
            return

        # Parser les modifications du hex viewer
        print("[DEBUG] Parsing modifications...")
        if not self.chain_hex_viewer.parse_and_apply_edits():
            print("[DEBUG] Parsing failed")
            return  # Le parsing a échoué, le message d'erreur a déjà été affiché

        # Vérifier s'il y a des modifications
        modifications = self.chain_hex_viewer.get_modified_data()
        print(f"[DEBUG] Found {len(modifications)} modifications: {modifications}")

        if not modifications:
            QMessageBox.information(self, "Aucune modification", "Aucune modification à enregistrer")
            return

        # Afficher un dialogue de confirmation
        reply = QMessageBox.warning(
            self,
            "⚠️ ATTENTION - Sauvegarde des modifications",
            f"Vous êtes sur le point d'écrire {len(modifications)} octets modifiés dans le fichier image.\n\n"
            "AVERTISSEMENT:\n"
            "• Cette opération va MODIFIER DIRECTEMENT le fichier image\n"
            "• Les modifications sont IRRÉVERSIBLES\n"
            "• Le système de fichiers peut être CORROMPU si les modifications sont incorrectes\n"
            "• Il est FORTEMENT RECOMMANDÉ d'avoir une sauvegarde\n\n"
            "Voulez-vous vraiment continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Rouvrir le fichier en mode écriture
            print("[DEBUG] Reopening file in write mode...")
            self.parser.reopen_writable()
            print(f"[DEBUG] File reopened, mode: {self.parser.file_handle.mode}")

            # Écrire chaque modification
            total_written = 0
            for offset, byte_value in modifications.items():
                print(f"[DEBUG] Writing byte 0x{byte_value:02X} at offset 0x{offset:X}")
                bytes_written = self.parser.write_bytes_at_offset(offset, bytes([byte_value]))
                print(f"[DEBUG] Bytes written: {bytes_written}")
                total_written += 1

            print(f"[DEBUG] Total written: {total_written}")

            # Fermer et rouvrir en mode lecture
            print("[DEBUG] Closing and reopening in read mode...")
            self.parser.close()
            self.parser.open()

            # Relire le boot sector
            partition_offset = self.parser.current_partition_offset
            print(f"[DEBUG] Re-reading boot sector at offset {partition_offset}")
            self.parser.read_boot_sector(partition_offset)

            # Effacer les modifications du hex viewer
            self.chain_hex_viewer.clear_modifications()

            # Désactiver le bouton de sauvegarde
            self.save_modifications_button.setEnabled(False)

            # Rafraîchir l'affichage
            self.chain_hex_viewer.set_data(self.chain_hex_viewer.data, self.chain_hex_viewer.current_offset)

            print("[DEBUG] Save complete!")
            QMessageBox.information(
                self,
                "✅ Succès",
                f"{total_written} octets ont été écrits avec succès dans le fichier image.\n\n"
                "Le fichier a été mis à jour."
            )

        except Exception as e:
            print(f"[DEBUG] Exception during save: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de l'écriture des modifications:\n{str(e)}\n\n"
                "Le fichier peut être dans un état incohérent."
            )

    def closeEvent(self, event):
        """Gère la fermeture de l'application"""
        if self.parser:
            self.parser.close()
        event.accept()


def main():
    """Point d'entrée de l'application"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Style moderne

    window = FATSimulatorGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
