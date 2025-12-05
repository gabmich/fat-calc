"""
Widget pour visualiser la table FAT complète avec tous les indices/clusters
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QScrollArea, QGridLayout, QLineEdit, QPushButton,
                              QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QSize
from PyQt6.QtGui import QDrag, QPainter, QColor, QPen, QFont
import struct


class ClusterCell(QLabel):
    """Widget représentant un cluster dans la table FAT (draggable)"""

    clicked = pyqtSignal(int)  # Signal émis quand le cluster est cliqué
    double_clicked = pyqtSignal(int)  # Signal émis quand le cluster est double-cliqué

    def __init__(self, cluster_index: int, next_cluster: int, parent=None):
        super().__init__(parent)
        self.cluster_index = cluster_index
        self.next_cluster = next_cluster
        self.is_selected = False
        self.setup_ui()

    def setup_ui(self):
        """Configure l'apparence de la cellule"""
        self.setFixedSize(70, 60)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.update_display()
        # Note: setCursor peut causer des warnings avec certaines versions de Qt
        try:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        except:
            pass  # Ignorer si ça ne fonctionne pas

    def update_display(self):
        """Met à jour l'affichage de la cellule"""
        # Déterminer le type de cluster
        if self.next_cluster == 0x0000:
            # Cluster libre
            color = "#E9ECEF"
            text_color = "#999"
            status = "Libre"
        elif self.next_cluster >= 0xFFF8:
            # Fin de chaîne (EOF)
            color = "#FF6B6B"
            text_color = "white"
            status = "EOF"
        elif self.next_cluster == 0xFFF7:
            # Cluster défectueux
            color = "#FFA500"
            text_color = "white"
            status = "BAD"
        elif self.next_cluster >= 0xFFF0:
            # Réservé
            color = "#FFE66D"
            text_color = "#333"
            status = "RES"
        else:
            # Cluster utilisé
            color = "#51CF66"
            text_color = "white"
            status = f"→{self.next_cluster}"

        # Si sélectionné, bordure épaisse
        if self.is_selected:
            border = "border: 3px solid #228BE6;"
        else:
            border = "border: 1px solid #CED4DA;"

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: {text_color};
                font-weight: bold;
                font-size: 8pt;
                {border}
                border-radius: 3px;
                padding: 2px;
            }}
            QLabel:hover {{
                border: 2px solid #4C6EF5;
            }}
        """)

        self.setText(f"[{self.cluster_index}]\n{status}")

    def set_selected(self, selected: bool):
        """Marque cette cellule comme sélectionnée"""
        self.is_selected = selected
        self.update_display()

    def mousePressEvent(self, event):
        """Gère le clic sur la cellule"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.cluster_index)

            # Démarrer un drag si ce n'est pas un cluster libre
            if self.next_cluster != 0x0000 and self.cluster_index >= 2:
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(str(self.cluster_index))
                drag.setMimeData(mime_data)

                # Créer une pixmap pour le drag
                pixmap = self.grab()
                drag.setPixmap(pixmap)
                drag.setHotSpot(event.position().toPoint())

                # Exécuter le drag
                drag.exec(Qt.DropAction.CopyAction)

    def mouseDoubleClickEvent(self, event):
        """Gère le double-clic sur la cellule"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.cluster_index)


class FATTableViewer(QWidget):
    """Widget pour visualiser la table FAT complète"""

    cluster_selected = pyqtSignal(int)  # Signal émis quand un cluster est sélectionné
    cluster_double_clicked = pyqtSignal(int)  # Signal émis quand un cluster est double-cliqué

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fat_data = b''
        self.cluster_cells = []
        self.selected_cluster = None
        self.clusters_per_row = 10
        self.setup_ui()

    def setup_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # En-tête avec titre et recherche
        header_layout = QHBoxLayout()

        title = QLabel("Table FAT - Tous les Clusters")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; padding: 5px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Champ de recherche
        header_layout.addWidget(QLabel("Aller au cluster:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("N° cluster")
        self.search_input.setMaximumWidth(80)
        self.search_input.returnPressed.connect(self.jump_to_cluster)
        header_layout.addWidget(self.search_input)

        self.jump_button = QPushButton("↓ Aller")
        self.jump_button.clicked.connect(self.jump_to_cluster)
        header_layout.addWidget(self.jump_button)

        layout.addLayout(header_layout)

        # Info label
        self.info_label = QLabel("Chargez une image pour afficher la table FAT")
        self.info_label.setStyleSheet("padding: 5px; background-color: #E9ECEF; border-radius: 3px;")
        layout.addWidget(self.info_label)

        # Zone scrollable pour la grille de clusters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_container.setLayout(self.grid_layout)

        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)

        # Légende
        legend_layout = QHBoxLayout()
        legend_items = [
            ("Libre", "#E9ECEF", "#999"),
            ("Utilisé", "#51CF66", "white"),
            ("EOF", "#FF6B6B", "white"),
            ("Défectueux", "#FFA500", "white"),
            ("Réservé", "#FFE66D", "#333")
        ]

        for label, bg, fg in legend_items:
            item_frame = QFrame()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(5, 2, 5, 2)

            color_box = QLabel()
            color_box.setFixedSize(15, 15)
            color_box.setStyleSheet(f"background-color: {bg}; border: 1px solid #999;")
            item_layout.addWidget(color_box)

            text = QLabel(label)
            text.setStyleSheet(f"font-size: 8pt; padding-left: 3px;")
            item_layout.addWidget(text)

            item_frame.setLayout(item_layout)
            legend_layout.addWidget(item_frame)

        legend_layout.addStretch()
        layout.addLayout(legend_layout)

        self.setLayout(layout)

    def load_fat(self, fat_data: bytes):
        """Charge et affiche la table FAT"""
        self.fat_data = fat_data

        # Effacer les anciennes cellules
        for cell in self.cluster_cells:
            cell.setParent(None)
            cell.deleteLater()
        self.cluster_cells.clear()

        # Calculer le nombre d'entrées FAT (FAT16 = 2 octets par entrée)
        num_entries = len(fat_data) // 2

        # Limiter l'affichage pour la performance (afficher max 1000 clusters)
        max_display = min(num_entries, 1000)

        # Créer les cellules
        for i in range(max_display):
            offset = i * 2
            if offset + 2 <= len(fat_data):
                next_cluster = struct.unpack('<H', fat_data[offset:offset + 2])[0]

                cell = ClusterCell(i, next_cluster)
                cell.clicked.connect(self._on_cluster_clicked)
                cell.double_clicked.connect(self._on_cluster_double_clicked)

                # Positionner dans la grille
                row = i // self.clusters_per_row
                col = i % self.clusters_per_row

                self.grid_layout.addWidget(cell, row, col)
                self.cluster_cells.append(cell)

        # Mettre à jour le label d'info
        self.info_label.setText(
            f"Table FAT chargée: {num_entries} entrées | "
            f"Affichage: {max_display} premiers clusters | "
            f"💡 Cliquez pour sélectionner, double-cliquez pour ajouter à la chaîne"
        )

    def _on_cluster_clicked(self, cluster_index: int):
        """Callback quand un cluster est cliqué"""
        # Désélectionner l'ancien cluster
        if self.selected_cluster is not None:
            for cell in self.cluster_cells:
                if cell.cluster_index == self.selected_cluster:
                    cell.set_selected(False)
                    break

        # Sélectionner le nouveau cluster
        self.selected_cluster = cluster_index
        for cell in self.cluster_cells:
            if cell.cluster_index == cluster_index:
                cell.set_selected(True)
                break

        # Émettre le signal
        self.cluster_selected.emit(cluster_index)

    def _on_cluster_double_clicked(self, cluster_index: int):
        """Callback quand un cluster est double-cliqué"""
        self.cluster_double_clicked.emit(cluster_index)

    def jump_to_cluster(self):
        """Saute à un cluster spécifique"""
        try:
            cluster_num = int(self.search_input.text())
            if 0 <= cluster_num < len(self.cluster_cells):
                # Sélectionner le cluster
                self._on_cluster_clicked(cluster_num)

                # Scroller jusqu'au cluster
                row = cluster_num // self.clusters_per_row
                # Estimer la position Y
                cell_height = 65  # Hauteur approximative d'une cellule + spacing
                y_position = row * cell_height

                # Scroller (nécessite d'accéder au QScrollArea parent)
                # Pour l'instant, on sélectionne juste le cluster
        except ValueError:
            pass

    def get_cluster_value(self, cluster_index: int) -> Optional[int]:
        """Retourne la valeur de l'entrée FAT pour un cluster donné"""
        if not self.fat_data:
            return None

        offset = cluster_index * 2
        if offset + 2 <= len(self.fat_data):
            return struct.unpack('<H', self.fat_data[offset:offset + 2])[0]
        return None

    def clear(self):
        """Efface le contenu"""
        for cell in self.cluster_cells:
            cell.setParent(None)
            cell.deleteLater()
        self.cluster_cells.clear()
        self.selected_cluster = None
        self.info_label.setText("Chargez une image pour afficher la table FAT")
