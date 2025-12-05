"""
Widget personnalisé pour afficher des données en hexadécimal
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtCore import Qt


class HexViewer(QWidget):
    """Widget pour afficher des données en format hexadécimal"""

    def __init__(self, parent=None, bytes_per_line=16):
        super().__init__(parent)
        self.data = b''
        self.current_offset = 0  # Stocker l'offset courant
        self.bytes_per_line = bytes_per_line  # Configurable: 8, 16, 32, etc.
        self.highlight_ranges = []  # Liste de tuples (start, length) à mettre en évidence
        self.setup_ui()

    def setup_ui(self):
        """Initialise l'interface du hex viewer"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Label pour le titre
        self.title_label = QLabel("Contenu Hexadécimal")
        self.title_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.title_label)

        # Zone de texte pour l'affichage hexadécimal
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Police monospace pour alignement correct
        font = QFont("Courier New", 9)
        self.text_edit.setFont(font)

        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def set_title(self, title: str):
        """Définit le titre du hex viewer"""
        self.title_label.setText(title)

    def set_data(self, data: bytes, offset: int = 0):
        """
        Affiche les données en format hexadécimal

        Args:
            data: Les données à afficher
            offset: L'offset de départ pour l'affichage des adresses
        """
        self.data = data
        self.current_offset = offset  # Store for refresh
        self.text_edit.clear()

        if not data:
            self.text_edit.setPlainText("Aucune donnée à afficher")
            return

        html_lines = []
        html_lines.append('<pre style="font-family: Courier New; font-size: 9pt;">')

        # En-tête
        header = "Offset    "
        for i in range(self.bytes_per_line):
            header += f"{i:02X} "
        header += " " * 2 + "ASCII"
        html_lines.append(f'<span style="color: #0066CC; font-weight: bold;">{header}</span>')
        html_lines.append("-" * (10 + (self.bytes_per_line * 3) + 2 + self.bytes_per_line))

        # Données
        for i in range(0, len(data), self.bytes_per_line):
            line = data[i:i + self.bytes_per_line]
            address = offset + i

            # Offset (adresse)
            line_html = f'<span style="color: #666666;">{address:08X}</span>  '

            # Octets en hexadécimal
            hex_part = ""
            for j, byte in enumerate(line):
                byte_pos = i + j
                is_highlighted = any(start <= byte_pos < start + length
                                    for start, length in self.highlight_ranges)

                if is_highlighted:
                    hex_part += f'<span style="background-color: #FFFF00; font-weight: bold;">{byte:02X}</span> '
                else:
                    hex_part += f"{byte:02X} "

            # Padding si ligne incomplète
            hex_part += "   " * (self.bytes_per_line - len(line))

            line_html += hex_part + " "

            # Représentation ASCII
            ascii_part = ""
            for j, byte in enumerate(line):
                byte_pos = i + j
                is_highlighted = any(start <= byte_pos < start + length
                                    for start, length in self.highlight_ranges)

                if 32 <= byte < 127:
                    char = chr(byte)
                else:
                    char = "."

                if is_highlighted:
                    ascii_part += f'<span style="background-color: #FFFF00; color: #000000; font-weight: bold;">{char}</span>'
                else:
                    ascii_part += char

            line_html += f'<span style="color: #009900;">{ascii_part}</span>'
            html_lines.append(line_html)

        html_lines.append('</pre>')
        html = '\n'.join(html_lines)

        self.text_edit.setHtml(html)

        # Remonter en haut
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.text_edit.setTextCursor(cursor)

    def highlight_range(self, start: int, length: int, scroll_to: bool = True):
        """
        Met en évidence une plage d'octets

        Args:
            start: Position de départ (relative au début des données affichées)
            length: Nombre d'octets à mettre en évidence
            scroll_to: Si True, scrolle automatiquement vers la zone mise en évidence
        """
        self.highlight_ranges = [(start, length)]
        # Rafraîchir l'affichage si des données sont présentes
        if self.data:
            self.set_data(self.data, self.current_offset)
            if scroll_to:
                self.scroll_to_position(start)

    def scroll_to_position(self, byte_position: int):
        """
        Scrolle le hex viewer vers une position d'octet spécifique

        Args:
            byte_position: Position de l'octet (relative au début des données)
        """
        if not self.data or byte_position < 0 or byte_position >= len(self.data):
            return

        # Calculer la ligne où se trouve cet octet
        # Ligne 0 = en-tête, ligne 1 = séparateur, lignes de données commencent à 2
        line_number = (byte_position // self.bytes_per_line) + 2

        # Obtenir le curseur
        cursor = self.text_edit.textCursor()

        # Se déplacer au début du document
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        # Se déplacer vers la ligne cible
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.MoveOperation.Down)

        # Positionner le curseur
        self.text_edit.setTextCursor(cursor)

        # Centrer la vue sur le curseur
        self.text_edit.ensureCursorVisible()

    def clear_highlights(self):
        """Efface toutes les mises en évidence"""
        self.highlight_ranges = []
        # Rafraîchir l'affichage si des données sont présentes
        if self.data:
            self.set_data(self.data, self.current_offset)

    def clear(self):
        """Efface le contenu du hex viewer"""
        self.data = b''
        self.highlight_ranges = []
        self.text_edit.clear()

    def set_bytes_per_line(self, bytes_per_line: int):
        """
        Change le nombre d'octets par ligne (8, 16, 32, etc.)
        et rafraîchit l'affichage si des données sont présentes
        """
        self.bytes_per_line = bytes_per_line
        if self.data:
            # Rafraîchir l'affichage avec les nouvelles données
            current_data = self.data
            offset = 0  # On pourrait stocker l'offset aussi si nécessaire
            self.set_data(current_data, offset)
