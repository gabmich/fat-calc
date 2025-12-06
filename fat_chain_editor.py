"""
Widget for visualizing and editing FAT chains
"""

from typing import List, Optional, Callable
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QScrollArea, QFrame, QLineEdit, QMessageBox,
                              QMenu, QTextEdit, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QAction, QFont


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
        self.display_mode = "grid"  # "compact", "grid", or "full" - Grid par défaut
        self.setup_ui()

    def setup_ui(self):
        """Initializes the interface"""
        layout = QVBoxLayout()

        # Header with buttons
        header_layout = QHBoxLayout()

        # View mode buttons
        view_label = QLabel("View:")
        header_layout.addWidget(view_label)

        self.compact_btn = QPushButton("📊 Compact")
        self.compact_btn.setCheckable(True)
        self.compact_btn.setChecked(False)
        self.compact_btn.clicked.connect(lambda: self.set_display_mode("compact"))
        self.compact_btn.setToolTip("Show ranges of contiguous clusters")
        header_layout.addWidget(self.compact_btn)

        self.grid_btn = QPushButton("📋 Grid")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)  # Grid par défaut
        self.grid_btn.clicked.connect(lambda: self.set_display_mode("grid"))
        self.grid_btn.setToolTip("Show all clusters in a compact grid")
        header_layout.addWidget(self.grid_btn)

        self.full_btn = QPushButton("🔍 Full")
        self.full_btn.setCheckable(True)
        self.full_btn.clicked.connect(lambda: self.set_display_mode("full"))
        self.full_btn.setToolTip("Show individual cluster blocks")
        header_layout.addWidget(self.full_btn)

        header_layout.addStretch()

        # Button to add a cluster
        self.add_button = QPushButton("➕ Add")
        self.add_button.clicked.connect(self.show_add_cluster_dialog)
        header_layout.addWidget(self.add_button)

        # Button to clear
        self.clear_button = QPushButton("🗑️ Clear")
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

    def set_display_mode(self, mode: str):
        """Changes the display mode"""
        self.display_mode = mode
        # Update button states
        self.compact_btn.setChecked(mode == "compact")
        self.grid_btn.setChecked(mode == "grid")
        self.full_btn.setChecked(mode == "full")
        # Refresh display
        self.refresh_display()

    def analyze_ranges(self):
        """Analyzes the chain to find contiguous ranges"""
        if not self.chain:
            return []

        ranges = []
        start = self.chain[0]
        prev = start
        count = 1

        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            # Check if contiguous
            if curr == prev + 1:
                count += 1
                prev = curr
            else:
                # End of range, save it
                ranges.append((start, prev, count, True))  # (start, end, count, is_contiguous)
                start = curr
                prev = curr
                count = 1

        # Add last range
        ranges.append((start, prev, count, count > 1))

        return ranges

    def calculate_fragmentation(self):
        """Calculates fragmentation percentage"""
        if len(self.chain) <= 1:
            return 0.0

        ranges = self.analyze_ranges()
        if not ranges:
            return 0.0

        # Fragmentation = nombre de fragments / nombre total de clusters
        # Plus il y a de fragments, plus c'est fragmenté
        # 0% = tout continu, 100% = tous dispersés
        num_ranges = len(ranges)
        total_clusters = len(self.chain)

        # Un fichier parfaitement continu a 1 range
        # Un fichier complètement fragmenté a N ranges (1 par cluster)
        if num_ranges == 1:
            return 0.0
        else:
            return ((num_ranges - 1) / (total_clusters - 1)) * 100.0

    def refresh_display(self):
        """Refreshes the chain display based on current mode"""
        import time
        start = time.time()

        # Clear ALL child widgets from the layout
        while self.chain_layout.count():
            item = self.chain_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()

        self.cluster_blocks.clear()

        if not self.chain:
            empty_label = QLabel("Empty chain - Click 'Add' to start")
            empty_label.setStyleSheet("padding: 20px; color: #999; font-style: italic;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.chain_layout.addWidget(empty_label)
            self.chain_layout.addStretch()
            self.info_label.setText("Empty chain")
            return

        # Display according to mode
        if self.display_mode == "compact":
            self._display_compact()
        elif self.display_mode == "grid":
            self._display_grid()
        else:  # "full"
            self._display_full()

        # Update info label
        total_size = len(self.chain)
        ranges = self.analyze_ranges()
        fragmentation = self.calculate_fragmentation()

        info_parts = []
        info_parts.append(f"Total: {total_size} cluster{'s' if total_size > 1 else ''}")
        info_parts.append(f"Ranges: {len(ranges)}")
        info_parts.append(f"Fragmentation: {fragmentation:.1f}%")
        if self.chain:
            info_parts.append(f"Start: {self.chain[0]}")
            info_parts.append(f"End: {self.chain[-1]}")

        self.info_label.setText(" | ".join(info_parts))

        elapsed = (time.time() - start) * 1000
        if elapsed > 5:
            print(f"[CHAIN EDITOR] refresh_display ({self.display_mode}): {elapsed:.1f}ms for {len(self.chain)} clusters")

    def _display_compact(self):
        """Displays chain in compact ranges view"""
        ranges = self.analyze_ranges()

        # Fragmentation bar
        fragmentation = self.calculate_fragmentation()
        frag_widget = self._create_fragmentation_bar(fragmentation)
        self.chain_layout.addWidget(frag_widget)

        # Ranges display
        for start, end, count, is_contiguous in ranges:
            if is_contiguous:
                # Contiguous range
                range_label = QLabel(f"[{start}→{end}]")
                range_label.setStyleSheet("font-weight: bold; color: #2E7D32; background-color: #E7F5E9; padding: 5px 10px; border-radius: 3px; border: 1px solid #81C784;")
                range_label.setToolTip(f"Contiguous range: {count} clusters ({start} to {end})\nLeft-click: view • Right-click: edit")
            else:
                # Single cluster
                range_label = QLabel(f"[{start}]")
                range_label.setStyleSheet("font-weight: bold; color: #1565C0; background-color: #E3F2FD; padding: 5px 10px; border-radius: 3px; border: 1px solid #90CAF9;")
                range_label.setToolTip(f"Single cluster: {start}\nLeft-click: view • Right-click: edit")

            # Make clickable
            range_label.mousePressEvent = lambda e, s=start: self._handle_compact_click(e, s)
            range_label.setCursor(Qt.CursorShape.PointingHandCursor)

            # Enable context menu
            range_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            range_label.customContextMenuRequested.connect(
                lambda pos, s=start, lbl=range_label: self._on_cluster_right_clicked(s, lbl.mapToGlobal(pos))
            )

            self.chain_layout.addWidget(range_label)

            # Add arrow if not last
            if (start, end, count, is_contiguous) != ranges[-1]:
                arrow = QLabel("→")
                arrow.setStyleSheet("font-size: 14pt; color: #666; padding: 0 3px;")
                self.chain_layout.addWidget(arrow)

        self.chain_layout.addStretch()

    def _handle_compact_click(self, event, cluster):
        """Handle clicks on compact view labels"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_cluster_clicked(cluster)

    def _display_grid(self):
        """Displays all clusters in a compact grid"""
        # Create grid layout inside a widget
        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(5, 5, 5, 5)

        # Display clusters in grid (15 columns)
        cols = 15
        for i, cluster in enumerate(self.chain):
            row = i // cols
            col = i % cols

            is_last = (i == len(self.chain) - 1)

            cluster_btn = QPushButton(str(cluster))
            cluster_btn.setFixedSize(50, 25)

            # Different style for last cluster (EOF)
            if is_last:
                cluster_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFF3E0;
                        border: 2px solid #FF9800;
                        border-radius: 2px;
                        font-size: 9pt;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #FFE0B2;
                    }
                """)
                cluster_btn.setToolTip(f"Cluster {cluster} [EOF - Last cluster]")
            else:
                cluster_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #E3F2FD;
                        border: 1px solid #90CAF9;
                        border-radius: 2px;
                        font-size: 9pt;
                    }
                    QPushButton:hover {
                        background-color: #BBDEFB;
                    }
                """)
                cluster_btn.setToolTip(f"Cluster {cluster} - Right-click for options")

            # Left click
            cluster_btn.clicked.connect(lambda checked, c=cluster: self._on_cluster_clicked(c))

            # Right click - context menu
            cluster_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            cluster_btn.customContextMenuRequested.connect(
                lambda pos, c=cluster, btn=cluster_btn: self._show_grid_context_menu(c, btn.mapToGlobal(pos))
            )

            grid_layout.addWidget(cluster_btn, row, col)

        grid_widget.setLayout(grid_layout)
        self.chain_layout.addWidget(grid_widget)
        self.chain_layout.addStretch()

    def _show_grid_context_menu(self, cluster_number: int, global_pos):
        """Shows context menu for grid mode clusters"""
        # Delegate to the same handler as full mode
        self._on_cluster_right_clicked(cluster_number, global_pos)

    def _display_full(self):
        """Displays chain with individual cluster blocks (ALL clusters)"""
        # Display ALL clusters - no limit
        for i, cluster in enumerate(self.chain):
            is_last = (i == len(self.chain) - 1)

            block = ClusterBlock(cluster, i, is_last)
            block.clicked.connect(self._on_cluster_clicked)
            block.right_clicked.connect(self._on_cluster_right_clicked)

            self.cluster_blocks.append(block)
            self.chain_layout.addWidget(block)

            # Add arrow between clusters (except after the last one)
            if i < len(self.chain) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet("font-size: 20pt; color: #495057; padding: 0 5px;")
                self.chain_layout.addWidget(arrow)

        self.chain_layout.addStretch()

        # Add a warning if the chain is very long
        if len(self.chain) > 100:
            warning = QLabel(f"⚠️ Large chain ({len(self.chain)} clusters) - Consider using Grid or Compact view for better performance")
            warning.setStyleSheet("color: #FF9800; font-style: italic; padding: 5px; background-color: #FFF3E0; border-radius: 3px;")
            warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.chain_layout.insertWidget(0, warning)

    def _create_fragmentation_bar(self, fragmentation):
        """Creates a visual fragmentation progress bar"""
        bar = QLabel()
        bar.setFixedHeight(20)
        bar.setStyleSheet("background-color: #E0E0E0; border-radius: 3px; border: 1px solid #BDBDBD;")

        # Calculate bar color based on fragmentation
        if fragmentation < 20:
            color = "#4CAF50"  # Green - low fragmentation
            text = f"█" * int((100 - fragmentation) / 5)
        elif fragmentation < 50:
            color = "#FF9800"  # Orange - moderate
            text = f"█" * int((100 - fragmentation) / 5)
        else:
            color = "#F44336"  # Red - high fragmentation
            text = f"█" * int((100 - fragmentation) / 5)

        bar_text = f"Fragmentation: {fragmentation:.1f}% " + text
        bar.setText(bar_text)
        bar.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {color}, stop:{(100-fragmentation)/100} {color}, stop:{(100-fragmentation)/100} #E0E0E0, stop:1 #E0E0E0); color: #000; font-weight: bold; padding-left: 10px; border-radius: 3px; border: 1px solid #BDBDBD;")

        return bar

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

