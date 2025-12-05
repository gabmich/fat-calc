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
            for byte in line:
                hex_part += f"{byte:02X} "
            # Padding si ligne incomplète
            hex_part += "   " * (self.bytes_per_line - len(line))

            line_html += hex_part + " "

            # Représentation ASCII
            ascii_part = ""
            for byte in line:
                if 32 <= byte < 127:
                    ascii_part += chr(byte)
                else:
                    ascii_part += "."

            line_html += f'<span style="color: #009900;">{ascii_part}</span>'
            html_lines.append(line_html)

        html_lines.append('</pre>')
        html = '\n'.join(html_lines)

        self.text_edit.setHtml(html)

        # Remonter en haut
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.text_edit.setTextCursor(cursor)

    def highlight_range(self, start: int, length: int):
        """
        Met en évidence une plage d'octets
        (Fonctionnalité future pour mettre en évidence des sections spécifiques)
        """
        # TODO: Implémenter la mise en évidence de plages spécifiques
        pass

    def clear(self):
        """Efface le contenu du hex viewer"""
        self.data = b''
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
