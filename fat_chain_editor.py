"""
Widget for visualizing and editing FAT chains
"""

from typing import List, Optional, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QScrollArea, QFrame, QLineEdit, QMessageBox,
                              QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QAction


class ClusterBlock(QLabel):
    """Widget representing a cluster in a FAT chain"""

    clicked = pyqtSignal(int)
    right_clicked = pyqtSignal(int, object)  # cluster_number, QPoint

    def __init__(self, cluster_number: int, position: int, is_last: bool = False, parent=None):
        super().__init__(parent)
        self.cluster_number = cluster_number
        self.position = position
        self.is_last = is_last  # Is this cluster the last one (EOF)?
        self.is_broken = False
        self.setup_ui()

    def setup_ui(self):
        """Configures the block's appearance"""
        self.setFixedSize(80, 50)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        self.update_display()
        # Note: setCursor may cause warnings with some Qt versions
        try:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        except:
            pass  # Ignore if it doesn't work

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def update_display(self):
        """Updates the cluster display"""
        if self.is_last:
            # This cluster is the last one (EOF)
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
                }
            """)

    def set_last(self, is_last: bool):
        """Marks this block as last (EOF)"""
        self.is_last = is_last
        self.update_display()

    def set_broken(self, is_broken: bool):
        """Marks this block as broken"""
        self.is_broken = is_broken
        self.update_display()

    def mousePressEvent(self, event):
        """Handles cluster click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.cluster_number)
            print(f"[ClusterBlock] Clicked cluster {self.cluster_number}")

    def _show_context_menu(self, pos):
        """Shows the context menu"""
        self.right_clicked.emit(self.cluster_number, self.mapToGlobal(pos))


class FATChainEditor(QWidget):
    """Widget for editing a FAT chain"""

    chain_modified = pyqtSignal(list)  # New cluster chain
    cluster_selected = pyqtSignal(int)  # Selected cluster
    save_requested = pyqtSignal()  # Signal to request save

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chain: List[int] = []
        self.cluster_blocks: List[ClusterBlock] = []
        self.on_cluster_click: Optional[Callable] = None
        self.setup_ui()

    def setup_ui(self):
        """Initializes the interface"""
        layout = QVBoxLayout()

        # Header with buttons
        header_layout = QHBoxLayout()

        header_layout.addStretch()

        # Button to add a cluster
        self.add_button = QPushButton("➕ Add Cluster")
        self.add_button.clicked.connect(self.show_add_cluster_dialog)
        header_layout.addWidget(self.add_button)

        # Note: The "Add EOF" button has been removed
        # Use right-click on a cluster → "Mark as last (EOF)"

        # Button to clear
        self.clear_button = QPushButton("🗑️ Clear All")
        self.clear_button.clicked.connect(self.clear_chain)
        header_layout.addWidget(self.clear_button)

        # Button to save
        self.save_button = QPushButton("💾 Save")
        self.save_button.clicked.connect(self.save_requested.emit)
        header_layout.addWidget(self.save_button)

        layout.addLayout(header_layout)

        # Search result (FAT offset + Data offset)
        self.search_result_label = QLineEdit("Search for a cluster to see its offsets")
        self.search_result_label.setReadOnly(True)
        self.search_result_label.setStyleSheet("QLineEdit { padding: 5px; background-color: #E8F4F8; border: 1px solid #90CAF9; border-radius: 3px; color: #1565C0; font-size: 9pt; }")
        layout.addWidget(self.search_result_label)

        # Scrollable area to display the chain
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

        # Chain information
        self.info_label = QLabel("No chain loaded")
        self.info_label.setStyleSheet("padding: 5px; background-color: #E9ECEF; border-radius: 3px;")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def set_chain(self, chain: List[int]):
        """Sets the cluster chain to display"""
        self.chain = chain.copy()
        self.refresh_display()

    def set_search_result(self, text: str):
        """Sets the search result text"""
        self.search_result_label.setText(text)
        # Style according to message type
        if text.startswith("✅") or "Cluster" in text:
            self.search_result_label.setStyleSheet("QLineEdit { padding: 5px; background-color: #E7F5E9; border: 1px solid #81C784; border-radius: 3px; color: #2E7D32; font-size: 9pt; font-weight: bold; }")
        elif text.startswith("❌"):
            self.search_result_label.setStyleSheet("QLineEdit { padding: 5px; background-color: #FFEBEE; border: 1px solid #EF5350; border-radius: 3px; color: #C62828; font-size: 9pt; font-weight: bold; }")
        else:
            self.search_result_label.setStyleSheet("QLineEdit { padding: 5px; background-color: #E8F4F8; border: 1px solid #90CAF9; border-radius: 3px; color: #1565C0; font-size: 9pt; }")

    def refresh_display(self):
        """Refreshes the chain display"""
        # Clear ALL child widgets from the layout
        while self.chain_layout.count():
            item = self.chain_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
                # Otherwise it's a spacer or other layout item, ignore it

        self.cluster_blocks.clear()

        if not self.chain:
            # Display a message for empty chain
            empty_label = QLabel("Empty chain - Click 'Add Cluster' to start")
            empty_label.setStyleSheet("padding: 20px; color: #999; font-style: italic;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.chain_layout.addWidget(empty_label)
            self.chain_layout.addStretch()
            self.info_label.setText("Empty chain")
            return

        # Create widgets for each cluster
        for i, cluster in enumerate(self.chain):
            # Check if it's the last cluster
            is_last = (i == len(self.chain) - 1)

            # Cluster block
            block = ClusterBlock(cluster, i, is_last)
            block.clicked.connect(self._on_cluster_clicked)
            block.right_clicked.connect(self._on_cluster_right_clicked)

            self.cluster_blocks.append(block)
            self.chain_layout.addWidget(block)

            # Add an arrow between clusters (except after the last one)
            if i < len(self.chain) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet("font-size: 20pt; color: #495057; padding: 0 5px;")
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.chain_layout.addWidget(arrow)

        # Add a stretch at the end
        self.chain_layout.addStretch()

        # Update information
        total_size = len(self.chain)
        cluster_list = ', '.join(map(str, self.chain[:10]))  # Limit to 10 for display
        if len(self.chain) > 10:
            cluster_list += f", ... ({len(self.chain) - 10} more)"
        self.info_label.setText(f"Chain: {total_size} cluster(s) | Clusters: {cluster_list}")

    def _on_cluster_clicked(self, cluster_number: int):
        """Callback when a cluster is clicked"""
        self.cluster_selected.emit(cluster_number)
        if self.on_cluster_click:
            self.on_cluster_click(cluster_number)

    def _on_cluster_right_clicked(self, cluster_number: int, pos: QPoint):
        """Callback when a cluster is right-clicked"""
        menu = QMenu(self)

        # Find the cluster's position in the chain
        try:
            cluster_position = self.chain.index(cluster_number)
        except ValueError:
            cluster_position = -1

        # Action to view content
        view_action = QAction(f"👁️ View cluster {cluster_number} content", self)
        view_action.triggered.connect(lambda: self._on_cluster_clicked(cluster_number))
        menu.addAction(view_action)

        menu.addSeparator()

        # Action to mark as EOF (last)
        if cluster_position >= 0:
            mark_eof_action = QAction(f"🔚 Mark as last (EOF)", self)
            mark_eof_action.triggered.connect(lambda: self._mark_as_eof(cluster_position))
            menu.addAction(mark_eof_action)

        menu.addSeparator()

        # Action to remove cluster
        remove_action = QAction(f"🗑️ Remove cluster {cluster_number}", self)
        remove_action.triggered.connect(lambda: self._remove_cluster_by_value(cluster_number))
        menu.addAction(remove_action)

        menu.exec(pos)

    def _remove_cluster_by_value(self, cluster_number: int):
        """Removes the first occurrence of a cluster from the chain"""
        try:
            # Find the position
            position = self.chain.index(cluster_number)
            self.remove_cluster_at(position)
        except ValueError:
            pass

    def _mark_as_eof(self, position: int):
        """Marks a cluster as EOF (last in the chain)"""
        if 0 <= position < len(self.chain):
            # Truncate the chain at this position (keep up to and including position)
            self.chain = self.chain[:position + 1]
            self.refresh_display()
            self.chain_modified.emit(self.chain)

            QMessageBox.information(
                self,
                "Marked as EOF",
                f"Cluster {self.chain[position]} is now the last in the chain.\n"
                f"All following clusters have been removed."
            )

    def add_cluster(self, cluster_number: int):
        """Adds a cluster to the end of the chain"""
        self.chain.append(cluster_number)
        self.refresh_display()
        self.chain_modified.emit(self.chain)

    # Method add_eof() removed - use _mark_as_eof() instead via right-click

    def show_add_cluster_dialog(self):
        """Shows a dialog to add a cluster"""
        from PyQt6.QtWidgets import QInputDialog

        cluster_number, ok = QInputDialog.getInt(
            self,
            "Add Cluster",
            "Cluster number:",
            2,  # Default value
            2,  # Minimum
            65535  # Maximum for FAT16
        )

        if ok:
            self.add_cluster(cluster_number)

    def clear_chain(self):
        """Clears the entire chain"""
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Are you sure you want to clear the entire chain?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.chain.clear()
            self.refresh_display()
            self.chain_modified.emit(self.chain)

    def remove_cluster_at(self, index: int):
        """Removes a cluster at the given index"""
        if 0 <= index < len(self.chain):
            removed = self.chain.pop(index)
            self.refresh_display()
            self.chain_modified.emit(self.chain)
            QMessageBox.information(
                self,
                "Cluster Removed",
                f"Cluster {removed} has been removed from position {index}"
            )

