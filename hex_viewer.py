"""
Widget personnalisé pour afficher des données en hexadécimal
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel,
                              QHBoxLayout, QCheckBox, QMessageBox)
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
from PyQt6.QtCore import Qt, pyqtSignal


class HexViewer(QWidget):
    """Widget pour afficher des données en format hexadécimal"""

    data_modified = pyqtSignal(int, bytes)  # Signal: offset, new_data

    def __init__(self, parent=None, bytes_per_line=16):
        super().__init__(parent)
        self.data = b''
        self.current_offset = 0  # Stocker l'offset courant
        self.bytes_per_line = bytes_per_line  # Configurable: 8, 16, 32, etc.
        self.highlight_ranges = []  # Liste de tuples (start, length) à mettre en évidence
        self.edit_mode = False  # Mode édition activé ou non
        self.modified_data = {}  # Dictionnaire {offset: byte_value} pour les modifications
        self.bytes_per_sector = 512  # Taille d'un secteur (par défaut 512 octets)
        self.setup_ui()

    def setup_ui(self):
        """Initialise l'interface du hex viewer"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header avec titre et checkbox
        header_layout = QHBoxLayout()

        # Label pour le titre
        self.title_label = QLabel("Contenu Hexadécimal")
        self.title_label.setStyleSheet("font-weight: bold; padding: 5px;")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Checkbox pour activer le mode édition
        self.edit_checkbox = QCheckBox("Mode édition")
        self.edit_checkbox.setStyleSheet("padding: 5px; color: #D32F2F; font-weight: bold;")
        self.edit_checkbox.stateChanged.connect(self.toggle_edit_mode)
        header_layout.addWidget(self.edit_checkbox)

        layout.addLayout(header_layout)

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

        if self.edit_mode:
            # Mode édition: affichage en texte simple pour permettre l'édition
            self._set_data_editable(data, offset)
        else:
            # Mode lecture: affichage HTML avec couleurs
            self._set_data_html(data, offset)

        # Remonter en haut
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.text_edit.setTextCursor(cursor)

    def _set_data_html(self, data: bytes, offset: int):
        """Affiche les données en HTML (mode lecture)"""
        html_lines = []
        html_lines.append('<pre style="font-family: Courier New; font-size: 9pt;">')

        # En-tête
        header = "Offset    "
        for i in range(self.bytes_per_line):
            header += f"{i:02X} "
        header += " " * 2 + "ASCII"
        html_lines.append(f'<span style="color: #0066CC; font-weight: bold;">{header}</span>')
        html_lines.append("-" * (10 + (self.bytes_per_line * 3) + 2 + self.bytes_per_line))

        # Calculer les lignes par secteur
        lines_per_sector = self.bytes_per_sector // self.bytes_per_line

        # Données
        line_count = 0
        for i in range(0, len(data), self.bytes_per_line):
            # Ajouter un séparateur de secteur si nécessaire
            if line_count > 0 and line_count % lines_per_sector == 0:
                separator = '<span style="color: #BBBBBB;">' + "· " * ((10 + (self.bytes_per_line * 3) + 2 + self.bytes_per_line) // 2) + '</span>'
                html_lines.append(separator)

            line = data[i:i + self.bytes_per_line]
            address = offset + i

            # Offset (adresse)
            line_html = f'<span style="color: #666666;">{address:08X}</span>  '

            # Octets en hexadécimal
            hex_part = ""
            for j, byte in enumerate(line):
                byte_pos = i + j
                absolute_offset = offset + byte_pos

                # Vérifier si cet octet a été modifié
                if absolute_offset in self.modified_data:
                    byte = self.modified_data[absolute_offset]

                is_highlighted = any(start <= byte_pos < start + length
                                    for start, length in self.highlight_ranges)

                if absolute_offset in self.modified_data:
                    # Octet modifié: en orange
                    hex_part += f'<span style="background-color: #FF9800; font-weight: bold; color: white;">{byte:02X}</span> '
                elif is_highlighted:
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
                absolute_offset = offset + byte_pos

                # Vérifier si cet octet a été modifié
                if absolute_offset in self.modified_data:
                    byte = self.modified_data[absolute_offset]

                is_highlighted = any(start <= byte_pos < start + length
                                    for start, length in self.highlight_ranges)

                if 32 <= byte < 127:
                    char = chr(byte)
                else:
                    char = "."

                if absolute_offset in self.modified_data:
                    ascii_part += f'<span style="background-color: #FF9800; color: white; font-weight: bold;">{char}</span>'
                elif is_highlighted:
                    ascii_part += f'<span style="background-color: #FFFF00; color: #000000; font-weight: bold;">{char}</span>'
                else:
                    ascii_part += char

            line_html += f'<span style="color: #009900;">{ascii_part}</span>'
            html_lines.append(line_html)
            line_count += 1

        html_lines.append('</pre>')
        html = '\n'.join(html_lines)
        self.text_edit.setHtml(html)

    def _set_data_editable(self, data: bytes, offset: int):
        """Affiche les données en texte simple (mode édition)"""
        lines = []

        # En-tête
        header = "Offset    "
        for i in range(self.bytes_per_line):
            header += f"{i:02X} "
        header += " " * 2 + "ASCII"
        lines.append(header)
        lines.append("-" * (10 + (self.bytes_per_line * 3) + 2 + self.bytes_per_line))

        # Calculer les lignes par secteur
        lines_per_sector = self.bytes_per_sector // self.bytes_per_line

        # Données
        line_count = 0
        for i in range(0, len(data), self.bytes_per_line):
            # Ajouter un séparateur de secteur si nécessaire
            if line_count > 0 and line_count % lines_per_sector == 0:
                separator = "· " * ((10 + (self.bytes_per_line * 3) + 2 + self.bytes_per_line) // 2)
                lines.append(separator)

            line = data[i:i + self.bytes_per_line]
            address = offset + i

            # Offset (adresse)
            line_text = f"{address:08X}  "

            # Octets en hexadécimal
            hex_part = ""
            for j, byte in enumerate(line):
                byte_pos = i + j
                absolute_offset = offset + byte_pos

                # Vérifier si cet octet a été modifié
                if absolute_offset in self.modified_data:
                    byte = self.modified_data[absolute_offset]

                hex_part += f"{byte:02X} "

            # Padding si ligne incomplète
            hex_part += "   " * (self.bytes_per_line - len(line))

            line_text += hex_part + " "

            # Représentation ASCII
            ascii_part = ""
            for j, byte in enumerate(line):
                byte_pos = i + j
                absolute_offset = offset + byte_pos

                # Vérifier si cet octet a été modifié
                if absolute_offset in self.modified_data:
                    byte = self.modified_data[absolute_offset]

                if 32 <= byte < 127:
                    char = chr(byte)
                else:
                    char = "."

                ascii_part += char

            line_text += ascii_part
            lines.append(line_text)
            line_count += 1

        text = '\n'.join(lines)
        self.text_edit.setPlainText(text)

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

            # Si en mode édition, appliquer le highlighting avec QTextCharFormat
            if self.edit_mode:
                self._apply_edit_mode_highlighting()

            if scroll_to:
                self.scroll_to_position(start)

    def _apply_edit_mode_highlighting(self):
        """Applique le highlighting en mode édition en utilisant QTextCharFormat"""
        if not self.highlight_ranges or not self.edit_mode:
            return

        # Calculer le nombre de lignes d'en-tête (header + séparateur)
        header_lines = 2

        # Calculer les lignes par secteur pour tenir compte des séparateurs
        lines_per_sector = self.bytes_per_sector // self.bytes_per_line

        for start, length in self.highlight_ranges:
            for byte_offset in range(start, start + length):
                # Calculer la ligne et la colonne dans le hex viewer
                line_in_data = byte_offset // self.bytes_per_line
                byte_in_line = byte_offset % self.bytes_per_line

                # Ajouter les lignes de séparateur de secteur
                separator_lines = line_in_data // lines_per_sector
                actual_line = header_lines + line_in_data + separator_lines

                # Position dans la ligne: offset(10) + 2 espaces + (byte_in_line * 3)
                hex_col_start = 10 + (byte_in_line * 3)
                hex_col_end = hex_col_start + 2

                # Position ASCII: offset(10) + 2 + hex_bytes(bytes_per_line*3) + 2 + byte_in_line
                ascii_col = 10 + (self.bytes_per_line * 3) + 2 + byte_in_line

                # Appliquer le format de highlighting aux octets hex
                cursor = self.text_edit.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)

                # Se déplacer à la ligne
                for _ in range(actual_line):
                    cursor.movePosition(QTextCursor.MoveOperation.Down)

                # Se déplacer à la colonne hex
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, hex_col_start)
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 2)

                # Appliquer le format
                fmt = QTextCharFormat()
                fmt.setBackground(QColor("#FFFF00"))
                fmt.setFontWeight(700)  # Bold
                cursor.setCharFormat(fmt)

                # Faire pareil pour le caractère ASCII
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                for _ in range(actual_line):
                    cursor.movePosition(QTextCursor.MoveOperation.Down)
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, ascii_col)
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)
                cursor.setCharFormat(fmt)

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

    def set_bytes_per_sector(self, bytes_per_sector: int):
        """
        Définit la taille d'un secteur pour les séparateurs
        """
        self.bytes_per_sector = bytes_per_sector
        if self.data:
            self.set_data(self.data, self.current_offset)

    def toggle_edit_mode(self, state):
        """Active/désactive le mode édition avec un avertissement"""
        if state == Qt.CheckState.Checked.value:
            # Afficher un warning
            reply = QMessageBox.warning(
                self,
                "⚠️ Mode Édition - ATTENTION",
                "Vous êtes sur le point d'activer le mode édition hexadécimale.\n\n"
                "AVERTISSEMENT:\n"
                "• Les modifications seront écrites DIRECTEMENT dans le fichier image\n"
                "• Cela peut CORROMPRE le système de fichiers si mal utilisé\n"
                "• Assurez-vous d'avoir une SAUVEGARDE avant de continuer\n"
                "• Les modifications ne sont pas annulables après sauvegarde\n\n"
                "Voulez-vous vraiment activer le mode édition ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.edit_mode = True
                self.text_edit.setReadOnly(False)
                self.text_edit.setStyleSheet("QTextEdit { background-color: #FFF3E0; }")
                self.title_label.setText(self.title_label.text() + " [MODE ÉDITION]")
            else:
                # L'utilisateur a annulé, décocher la checkbox
                self.edit_checkbox.setChecked(False)
        else:
            self.edit_mode = False
            self.text_edit.setReadOnly(True)
            self.text_edit.setStyleSheet("")
            title = self.title_label.text().replace(" [MODE ÉDITION]", "")
            self.title_label.setText(title)

    def get_modified_data(self):
        """Retourne les données modifiées sous forme de dictionnaire {absolute_offset: byte_value}"""
        return self.modified_data.copy()

    def clear_modifications(self):
        """Efface toutes les modifications en attente"""
        self.modified_data.clear()

    def has_modifications(self):
        """Vérifie s'il y a des modifications en attente"""
        return len(self.modified_data) > 0

    def parse_and_apply_edits(self):
        """
        Parse le contenu texte du hex viewer et détecte les modifications
        Retourne True si le parsing a réussi, False sinon
        """
        if not self.edit_mode:
            print("[HexViewer] Not in edit mode, skipping parse")
            return True

        try:
            text = self.text_edit.toPlainText()
            lines = text.split('\n')
            print(f"[HexViewer] Parsing {len(lines)} lines")

            # Ignorer les 2 premières lignes (header et séparateur)
            if len(lines) < 3:
                print("[HexViewer] Not enough lines")
                return True

            data_lines = lines[2:]
            modifications_found = 0

            for line_num, line in enumerate(data_lines):
                if not line.strip():
                    continue

                # Format: "XXXXXXXX  HH HH HH ... ASCII"
                # Extraire l'offset et les octets hex
                parts = line.split()
                if len(parts) < 2:
                    continue

                try:
                    # Premier élément = offset
                    line_offset = int(parts[0], 16)

                    # Éléments suivants jusqu'à la partie ASCII = octets hex
                    hex_bytes = []
                    for part in parts[1:]:
                        # S'arrêter quand on atteint la partie ASCII (caractères non-hex)
                        if len(part) == 2 and all(c in '0123456789ABCDEFabcdef' for c in part):
                            hex_bytes.append(int(part, 16))
                        else:
                            # On a atteint la partie ASCII, arrêter
                            break

                    # Comparer avec les données originales
                    for i, byte_value in enumerate(hex_bytes):
                        absolute_offset = line_offset + i
                        relative_offset = absolute_offset - self.current_offset

                        # Vérifier que l'offset est dans les limites
                        if 0 <= relative_offset < len(self.data):
                            original_byte = self.data[relative_offset]

                            # Si différent, enregistrer la modification
                            if byte_value != original_byte:
                                print(f"[HexViewer] Modification detected at offset 0x{absolute_offset:X}: {original_byte:02X} -> {byte_value:02X}")
                                self.modified_data[absolute_offset] = byte_value
                                modifications_found += 1
                            elif absolute_offset in self.modified_data and byte_value == original_byte:
                                # L'utilisateur a remis la valeur originale
                                print(f"[HexViewer] Modification removed at offset 0x{absolute_offset:X}")
                                del self.modified_data[absolute_offset]

                except (ValueError, IndexError) as e:
                    # Erreur de parsing, ignorer cette ligne
                    print(f"[HexViewer] Parse error on line {line_num}: {e}")
                    continue

            print(f"[HexViewer] Parse complete: {modifications_found} new modifications, {len(self.modified_data)} total")
            return True

        except Exception as e:
            print(f"[HexViewer] Parse exception: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Erreur de parsing",
                f"Impossible de parser les modifications:\n{str(e)}\n\n"
                "Vérifiez que le format hexadécimal est correct."
            )
            return False

    def apply_modifications_to_data(self):
        """
        Applique les modifications au buffer de données interne
        Retourne les données modifiées complètes
        """
        if not self.modified_data:
            return self.data

        # Créer une copie modifiable des données
        modified_data = bytearray(self.data)

        # Appliquer les modifications
        for absolute_offset, byte_value in self.modified_data.items():
            relative_offset = absolute_offset - self.current_offset
            if 0 <= relative_offset < len(modified_data):
                modified_data[relative_offset] = byte_value

        return bytes(modified_data)
