"""
Widget pour visualiser et éditer les chaînes FAT
"""

from typing import List, Optional, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QScrollArea, QFrame, QLineEdit, QMessageBox,
                              QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QAction


class ClusterBlock(QLabel):
    """Widget représentant un cluster dans une chaîne FAT"""

    clicked = pyqtSignal(int)
    right_clicked = pyqtSignal(int, object)  # cluster_number, QPoint

    def __init__(self, cluster_number: int, position: int, is_last: bool = False, parent=None):
        super().__init__(parent)
        self.cluster_number = cluster_number
        self.position = position
        self.is_last = is_last  # Ce cluster est-il le dernier (EOF) ?
        self.is_broken = False
        self.setup_ui()

    def setup_ui(self):
        """Configure l'apparence du bloc"""
        self.setFixedSize(80, 50)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.update_display()
        # Note: setCursor peut causer des warnings avec certaines versions de Qt
        try:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        except:
            pass  # Ignorer si ça ne fonctionne pas

        # Menu contextuel
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def update_display(self):
        """Met à jour l'affichage du cluster"""
        if self.is_last:
            # Ce cluster est le dernier (EOF)
            self.setText(f"Cluster\n{self.cluster_number}\n[EOF]")
            self.setStyleSheet("""
                QLabel {
                    background-color: #FF6B6B;
                    color: white;
                    font-weight: bold;
                    border: 3px solid #C92A2A;
                    border-radius: 5px;
                }
                QLabel:hover {
                    background-color: #FA5252;
                }
            """)
        elif self.is_broken:
            self.setText(f"Cluster\n{self.cluster_number}\n⚠")
            self.setStyleSheet("""
                QLabel {
                    background-color: #FFE66D;
                    color: #333;
                    font-weight: bold;
                    border: 2px dashed #FFA500;
                    border-radius: 5px;
                }
                QLabel:hover {
                    background-color: #FFD43B;
                }
            """)
        else:
            self.setText(f"Cluster\n{self.cluster_number}")
            self.setStyleSheet("""
                QLabel {
                    background-color: #51CF66;
                    color: white;
                    font-weight: bold;
                    border: 2px solid #2F9E44;
                    border-radius: 5px;
                }
                QLabel:hover {
                    background-color: #69DB7C;
                    cursor: pointer;
                }
            """)

    def set_last(self, is_last: bool):
        """Marque ce bloc comme dernier (EOF)"""
        self.is_last = is_last
        self.update_display()

    def set_broken(self, is_broken: bool):
        """Marque ce bloc comme cassé"""
        self.is_broken = is_broken
        self.update_display()

    def mousePressEvent(self, event):
        """Gère le clic sur le cluster"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.cluster_number)
            print(f"[ClusterBlock] Clicked cluster {self.cluster_number}")

    def _show_context_menu(self, pos):
        """Affiche le menu contextuel"""
        self.right_clicked.emit(self.cluster_number, self.mapToGlobal(pos))


class FATChainEditor(QWidget):
    """Widget pour éditer une chaîne FAT"""

    chain_modified = pyqtSignal(list)  # Nouvelle chaîne de clusters
    cluster_selected = pyqtSignal(int)  # Cluster sélectionné
    save_requested = pyqtSignal()  # Signal pour demander la sauvegarde

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chain: List[int] = []
        self.cluster_blocks: List[ClusterBlock] = []
        self.on_cluster_click: Optional[Callable] = None
        self.setup_ui()

    def setup_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout()

        # En-tête avec boutons
        header_layout = QHBoxLayout()

        header_layout.addStretch()

        # Bouton pour ajouter un cluster
        self.add_button = QPushButton("➕ Ajouter Cluster")
        self.add_button.clicked.connect(self.show_add_cluster_dialog)
        header_layout.addWidget(self.add_button)

        # Note: Le bouton "Ajouter EOF" a été supprimé
        # Utilisez le clic droit sur un cluster → "Marquer comme dernier (EOF)"

        # Bouton pour effacer
        self.clear_button = QPushButton("🗑️ Effacer Tout")
        self.clear_button.clicked.connect(self.clear_chain)
        header_layout.addWidget(self.clear_button)

        # Bouton pour enregistrer
        self.save_button = QPushButton("💾 Enregistrer")
        self.save_button.clicked.connect(self.save_requested.emit)
        header_layout.addWidget(self.save_button)

        layout.addLayout(header_layout)

        # Résultat de la recherche (offset FAT + offset Data)
        self.search_result_label = QLineEdit("Recherchez un cluster pour voir ses offsets")
        self.search_result_label.setReadOnly(True)
        self.search_result_label.setStyleSheet("QLineEdit { padding: 5px; background-color: #E8F4F8; border: 1px solid #90CAF9; border-radius: 3px; color: #1565C0; font-size: 9pt; }")
        layout.addWidget(self.search_result_label)

        # Zone scrollable pour afficher la chaîne
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(120)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.chain_container = QWidget()
        self.chain_layout = QHBoxLayout()
        self.chain_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.chain_layout.setContentsMargins(10, 10, 10, 10)
        self.chain_container.setLayout(self.chain_layout)

        scroll.setWidget(self.chain_container)
        layout.addWidget(scroll)

        # Informations sur la chaîne
        self.info_label = QLabel("Aucune chaîne chargée")
        self.info_label.setStyleSheet("padding: 5px; background-color: #E9ECEF; border-radius: 3px;")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def set_chain(self, chain: List[int]):
        """Définit la chaîne de clusters à afficher"""
        self.chain = chain.copy()
        self.refresh_display()

    def set_search_result(self, text: str):
        """Définit le texte du résultat de recherche"""
        self.search_result_label.setText(text)
        # Style selon le type de message
        if text.startswith("✅") or "Cluster" in text:
            self.search_result_label.setStyleSheet("QLineEdit { padding: 5px; background-color: #E7F5E9; border: 1px solid #81C784; border-radius: 3px; color: #2E7D32; font-size: 9pt; font-weight: bold; }")
        elif text.startswith("❌"):
            self.search_result_label.setStyleSheet("QLineEdit { padding: 5px; background-color: #FFEBEE; border: 1px solid #EF5350; border-radius: 3px; color: #C62828; font-size: 9pt; font-weight: bold; }")
        else:
            self.search_result_label.setStyleSheet("QLineEdit { padding: 5px; background-color: #E8F4F8; border: 1px solid #90CAF9; border-radius: 3px; color: #1565C0; font-size: 9pt; }")

    def refresh_display(self):
        """Rafraîchit l'affichage de la chaîne"""
        # Effacer TOUS les widgets enfants du layout
        while self.chain_layout.count():
            item = self.chain_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
                # Sinon c'est un spacer ou autre layout item, on l'ignore

        self.cluster_blocks.clear()

        if not self.chain:
            # Afficher un message pour chaîne vide
            empty_label = QLabel("Chaîne vide - Cliquez sur 'Ajouter Cluster' pour commencer")
            empty_label.setStyleSheet("padding: 20px; color: #999; font-style: italic;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.chain_layout.addWidget(empty_label)
            self.chain_layout.addStretch()
            self.info_label.setText("Chaîne vide")
            return

        # Créer les widgets pour chaque cluster
        for i, cluster in enumerate(self.chain):
            # Vérifier si c'est le dernier cluster
            is_last = (i == len(self.chain) - 1)

            # Bloc du cluster
            block = ClusterBlock(cluster, i, is_last)
            block.clicked.connect(self._on_cluster_clicked)
            block.right_clicked.connect(self._on_cluster_right_clicked)

            self.cluster_blocks.append(block)
            self.chain_layout.addWidget(block)

            # Ajouter une flèche entre les clusters (sauf après le dernier)
            if i < len(self.chain) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet("font-size: 20pt; color: #495057; padding: 0 5px;")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.chain_layout.addWidget(arrow)

        # Ajouter un stretch à la fin
        self.chain_layout.addStretch()

        # Mettre à jour les informations
        total_size = len(self.chain)
        cluster_list = ', '.join(map(str, self.chain[:10]))  # Limiter à 10 pour l'affichage
        if len(self.chain) > 10:
            cluster_list += f", ... ({len(self.chain) - 10} de plus)"
        self.info_label.setText(f"Chaîne: {total_size} cluster(s) | Clusters: {cluster_list}")

    def _on_cluster_clicked(self, cluster_number: int):
        """Callback quand un cluster est cliqué"""
        self.cluster_selected.emit(cluster_number)
        if self.on_cluster_click:
            self.on_cluster_click(cluster_number)

    def _on_cluster_right_clicked(self, cluster_number: int, pos: QPoint):
        """Callback quand un cluster est cliqué droit"""
        menu = QMenu(self)

        # Trouver la position du cluster dans la chaîne
        try:
            cluster_position = self.chain.index(cluster_number)
        except ValueError:
            cluster_position = -1

        # Action pour voir le contenu
        view_action = QAction(f"👁️ Voir le contenu du cluster {cluster_number}", self)
        view_action.triggered.connect(lambda: self._on_cluster_clicked(cluster_number))
        menu.addAction(view_action)

        menu.addSeparator()

        # Action pour marquer comme EOF (dernier)
        if cluster_position >= 0:
            mark_eof_action = QAction(f"🔚 Marquer comme dernier (EOF)", self)
            mark_eof_action.triggered.connect(lambda: self._mark_as_eof(cluster_position))
            menu.addAction(mark_eof_action)

        menu.addSeparator()

        # Action pour supprimer le cluster
        remove_action = QAction(f"🗑️ Supprimer le cluster {cluster_number}", self)
        remove_action.triggered.connect(lambda: self._remove_cluster_by_value(cluster_number))
        menu.addAction(remove_action)

        menu.exec(pos)

    def _remove_cluster_by_value(self, cluster_number: int):
        """Supprime la première occurrence d'un cluster de la chaîne"""
        try:
            # Trouver la position
            position = self.chain.index(cluster_number)
            self.remove_cluster_at(position)
        except ValueError:
            pass

    def _mark_as_eof(self, position: int):
        """Marque un cluster comme EOF (dernier de la chaîne)"""
        if 0 <= position < len(self.chain):
            # Tronquer la chaîne à cette position (garder jusqu'à position inclus)
            self.chain = self.chain[:position + 1]
            self.refresh_display()
            self.chain_modified.emit(self.chain)

            QMessageBox.information(
                self,
                "Marqué comme EOF",
                f"Le cluster {self.chain[position]} est maintenant le dernier de la chaîne.\n"
                f"Tous les clusters suivants ont été supprimés."
            )

    def add_cluster(self, cluster_number: int):
        """Ajoute un cluster à la fin de la chaîne"""
        self.chain.append(cluster_number)
        self.refresh_display()
        self.chain_modified.emit(self.chain)

    # Méthode add_eof() supprimée - utiliser _mark_as_eof() à la place via clic droit

    def show_add_cluster_dialog(self):
        """Affiche un dialogue pour ajouter un cluster"""
        from PyQt6.QtWidgets import QInputDialog

        cluster_number, ok = QInputDialog.getInt(
            self,
            "Ajouter un Cluster",
            "Numéro du cluster:",
            2,  # Valeur par défaut
            2,  # Minimum
            65535  # Maximum pour FAT16
        )

        if ok:
            self.add_cluster(cluster_number)

    def clear_chain(self):
        """Efface toute la chaîne"""
        reply = QMessageBox.question(
            self,
            "Confirmer",
            "Êtes-vous sûr de vouloir effacer toute la chaîne ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.chain.clear()
            self.refresh_display()
            self.chain_modified.emit(self.chain)

    def remove_cluster_at(self, index: int):
        """Supprime un cluster à l'index donné"""
        if 0 <= index < len(self.chain):
            removed = self.chain.pop(index)
            self.refresh_display()
            self.chain_modified.emit(self.chain)
            QMessageBox.information(
                self,
                "Cluster supprimé",
                f"Le cluster {removed} a été supprimé de la position {index}"
            )

