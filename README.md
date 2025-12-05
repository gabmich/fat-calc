# FAT16 Simulator - Forensic Analysis Tool

Outil forensique interactif pour analyser et éditer des images disque FAT16 (.raw). Permet de visualiser la structure de la partition, inspecter le contenu en hexadécimal, et reconstituer des chaînages FAT cassés de manière ludique.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Educational-blue)

## 🎯 Fonctionnalités

### ✅ Actuellement Implémenté (FAT16)

#### 📂 Analyse d'Images Disque
- ✅ Ouverture d'images .raw, .img, .dd
- ✅ Détection automatique des partitions (MBR)
- ✅ Lecture du Boot Sector FAT16
- ✅ Extraction de tous les paramètres de partition :
  - Octets par secteur
  - Secteurs par cluster
  - Secteurs réservés
  - Nombre de zones FAT
  - Secteurs par zone FAT
  - Entrées du répertoire racine
  - Volume label et ID

#### 🗺️ Visualisation de la Partition
- ✅ Carte graphique de la partition avec code couleur :
  - 🟡 **Jaune** : Boot Sector
  - 🔴 **Rouge** : Reserved Sectors
  - 🟢 **Vert clair** : FAT 1
  - 🟢 **Vert foncé** : FAT 2
  - 🟠 **Orange** : Root Directory
  - 🔵 **Bleu** : Data Zone
- ✅ Légende interactive
- ✅ Vue 1 carré = 1 secteur (détail maximal)

#### 🔍 Hex Viewer Intégré
- ✅ Visualisation hexadécimale + ASCII
- ✅ Affichage par **Secteur** (avec numéro)
- ✅ Affichage par **Cluster** (2+)
- ✅ Affichage de la **FAT** (FAT1 ou FAT2)
- ✅ Offsets automatiques affichés
- ✅ Coloration syntaxique

#### 📊 Table FAT Complète
- ✅ **Visualisation de tous les clusters** en grille colorée
- ✅ **Code couleur intelligent** :
  - 🔲 Gris : Cluster libre
  - 🟢 Vert : Cluster utilisé (→ suivant)
  - 🔴 Rouge : EOF (fin de chaîne)
  - 🟠 Orange : Cluster défectueux
  - 🟡 Jaune : Réservé
- ✅ **Clic** sur un cluster → affichage dans le Hex Viewer
- ✅ **Double-clic** sur un cluster → ajout à la chaîne
- ✅ **Drag & drop** depuis la table vers la chaîne
- ✅ Recherche rapide (Aller au cluster)
- ✅ Sélection visuelle (bordure bleue)

#### 🔗 Éditeur de Chaîne FAT (Drag & Drop Positionnel)
- ✅ Chargement automatique d'une chaîne depuis un cluster de départ
- ✅ Visualisation graphique de la chaîne (blocs colorés + flèches)
- ✅ **Zones de drop entre chaque cluster** (📍)
- ✅ **Drag & drop positionnel** : insérer un cluster n'importe où
- ✅ **Glisser depuis la table FAT** vers la chaîne
- ✅ **Réorganiser les clusters** dans la chaîne (drag entre positions)
- ✅ Ajout manuel de clusters (bouton ➕)
- ✅ Ajout de marqueur EOF (0xFFFF) (bouton 🔚)
- ✅ **Clic** sur un cluster → affichage dans le Hex Viewer
- ✅ **Clic droit** sur un cluster → menu contextuel (Supprimer/Voir)
- ✅ Indicateur de clusters cassés (⚠)
- ✅ Effacement de la chaîne
- ✅ **Feedback visuel** pendant le drag (zones bleues)

### 🚧 Prévu Mais Non Implémenté

- ⏳ Support FAT12
- ⏳ Support FAT32
- ⏳ Sauvegarde des modifications dans l'image .raw
- ⏳ Édition directe des valeurs FAT en hexadécimal
- ⏳ Export/Import de chaînes FAT en JSON
- ⏳ Reconstruction automatique de fichiers
- ⏳ Détection automatique de corruption
- ⏳ Undo/Redo
- ⏳ Comparaison FAT1 vs FAT2

---

## 📥 Installation

### 1. Prérequis

- **Python 3.8+**
- **PyQt6** (installé via pip)

### 2. Installation

```bash
cd fat-simulator

# Créer un environnement virtuel (recommandé)
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

---

## 🚀 Utilisation

### Lancement de l'Application

```bash
# Avec le script de lancement
./run_simulator.sh

# Ou manuellement
source venv/bin/activate
python fat_simulator_gui.py
```

### Workflow Typique

1. **Ouvrir une image** :
   - Cliquez sur "📂 Ouvrir Image .raw" ou `Ctrl+O`
   - Sélectionnez votre fichier .raw, .img ou .dd
   - L'application détecte automatiquement les partitions FAT16

2. **Explorer la structure** :
   - Consultez les informations de la partition (gauche)
   - Visualisez la carte graphique (droite)

3. **Inspecter en hexadécimal** :
   - Onglet "📄 Hex Viewer"
   - Sélectionnez le type : Secteur / Cluster / FAT
   - Entrez le numéro
   - Cliquez "Afficher"

4. **Explorer la table FAT complète** :
   - Onglet "📊 Table FAT Complète"
   - Visualisez tous les clusters avec code couleur
   - **Cliquez** sur un cluster pour voir son contenu en hexa
   - **Double-cliquez** sur un cluster pour l'ajouter à la chaîne
   - **Glissez** un cluster vers la chaîne (drag & drop)
   - Utilisez "Aller au cluster" pour naviguer rapidement

5. **Reconstituer une chaîne FAT** :
   - Onglet "🔗 Éditeur de Chaîne FAT"

   **Méthode 1 - Chargement automatique :**
   - Entrez le cluster de départ (ex: 2)
   - Cliquez "📥 Charger Chaîne"
   - La chaîne s'affiche graphiquement

   **Méthode 2 - Construction manuelle :**
   - Allez dans "📊 Table FAT Complète"
   - **Glissez** des clusters depuis la table vers la chaîne
   - Déposez-les entre les clusters existants (zones +)
   - Réorganisez en glissant les clusters dans la chaîne

   **Éditer la chaîne** :
     - ➕ Ajouter un cluster manuellement (numéro)
     - 🔚 Ajouter un marqueur EOF (fin de fichier)
     - **Glisser/Déposer positionnel** : insérer n'importe où
     - **Clic** sur un cluster → voir son contenu
     - **Clic droit** → Supprimer / Voir le contenu
     - Les zones **+** (bleues au survol) = zones de drop

6. **Sauvegarder (futur)** :
   - Cliquez "💾 Sauvegarder Chaîne" (non implémenté)

---

## 📐 Architecture du Projet

```
fat-simulator/
├── fat16_parser.py          # Parser pour images .raw FAT16
├── hex_viewer.py            # Widget hex viewer (PyQt6)
├── fat_table_viewer.py      # Widget table FAT complète (grille)
├── fat_chain_editor.py      # Widget éditeur de chaîne FAT (drag & drop)
├── fat_simulator_gui.py     # Application principale (GUI)
├── create_test_image.py     # Générateur d'images de test
├── requirements.txt         # Dépendances Python
├── run_simulator.sh         # Script de lancement
├── .gitignore               # Fichiers à ignorer
└── README.md                # Documentation
```

### Composants Principaux

#### `fat16_parser.py`
- **Classes** :
  - `BootSector` : Représente le boot sector FAT16
  - `MBRPartition` : Représente une partition dans le MBR
  - `FAT16Parser` : Parser principal pour lire l'image .raw

- **Méthodes clés** :
  - `read_mbr()` : Lit le Master Boot Record
  - `read_boot_sector()` : Lit le boot sector FAT16
  - `read_sector(n)` : Lit un secteur spécifique
  - `read_cluster(n)` : Lit un cluster spécifique
  - `read_fat(1|2)` : Lit une table FAT complète
  - `parse_fat_chain(start)` : Parse une chaîne FAT
  - `get_fat_entry(cluster)` : Retourne la valeur d'une entrée FAT

#### `hex_viewer.py`
- Widget PyQt6 pour afficher des données en hexadécimal
- Format : Offset | Hex | ASCII
- Coloration syntaxique
- Support des offsets personnalisés

#### `fat_table_viewer.py`
- Widget PyQt6 pour afficher la table FAT complète
- **ClusterCell** : Cellules cliquables représentant chaque cluster
- Grille de 10 colonnes (personnalisable)
- Code couleur selon l'état du cluster
- Recherche rapide (aller au cluster)
- Support drag & drop vers la chaîne

#### `fat_chain_editor.py`
- Widget PyQt6 pour éditer des chaînes FAT
- **ClusterBlock** : Blocs draggables représentant des clusters
- **DropZone** : Zones de drop entre les clusters (insertion positionnelle)
- Support drag & drop bidirectionnel
- Visualisation EOF (0xFFFF)
- Détection de clusters cassés (⚠)
- Menu contextuel (clic droit)

#### `fat_simulator_gui.py`
- Application principale PyQt6
- Interface à onglets (Hex Viewer / Éditeur FAT)
- Carte de partition interactive
- Gestion des événements utilisateur

---

## 🎨 Interface Utilisateur

### Fenêtre Principale

```
┌───────────────────────────────────────────────────────────────┐
│ Fichier                                                        │
├───────────────────────────────────────────────────────────────┤
│ [📂 Ouvrir Image .raw]  ✓ Image chargée: disk.raw            │
├───────────────────┬───────────────────────────────────────────┤
│ Informations      │ Carte de la Partition                     │
│ de la Partition   │ [Visualisation graphique colorée]         │
│                   │ 🟡🔴🟢🟢🟠🔵🔵🔵🔵🔵...                     │
│ - Octets/secteur  │                                            │
│ - Secteurs/cluster│ Légende: Boot Reserved FAT1 FAT2 ...      │
│ - ...             │                                            │
├───────────────────┴───────────────────────────────────────────┤
│ ┌─ 📄 Hex Viewer ─── 📊 Table FAT ─── 🔗 Éditeur Chaîne ──┐│
│ │ Type: [Cluster ▾] Numéro: [2] [Afficher]                 ││
│ │                                                            ││
│ │ Offset    00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D ...   ││
│ │ 00042000  4D 79 46 69 6C 65 20 20 54 58 54 20 00 ...       ││
│ │ 00042010  ...                                              ││
│ └────────────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────┘
```

### Table FAT Complète

```
┌────────────────────────────────────────────────────────────┐
│ Table FAT - Tous les Clusters  [Aller au cluster: ___ ↓]  │
├────────────────────────────────────────────────────────────┤
│ 💡 Cliquez pour voir, double-cliquez pour ajouter         │
│                                                             │
│ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐   │
│ │[0]│ │[1]│ │[2]│ │[3]│ │[4]│ │[5]│ │[6]│ │[7]│ │[8]│   │
│ │RES│ │EOF│ │→3 │ │→4 │ │EOF│ │→6 │ │EOF│ │⚠ │ │   │   │
│ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘   │
│                                                             │
│ 🔲 Libre  🟢 Utilisé  🔴 EOF  🟠 Défectueux  🟡 Réservé   │
└────────────────────────────────────────────────────────────┘
```

### Éditeur de Chaîne FAT (Drag & Drop Positionnel)

```
┌────────────────────────────────────────────────────────────┐
│ Éditeur de Chaîne FAT  [➕ Ajouter] [🔚 EOF] [🗑️ Effacer] │
├────────────────────────────────────────────────────────────┤
│ 💡 Glissez des clusters depuis la table FAT               │
│ Cluster de départ: [2 ▾] [📥 Charger Chaîne]              │
│                                                             │
│ ┌─┐ ┌─────────┐ ┌─┐ ┌─────────┐ ┌─┐ ┌─────────┐ ┌─┐ ┌───┐│
│ │+│ │Cluster  │ │+│ │Cluster  │ │+│ │Cluster  │ │+│ │EOF││
│ │ │ │   2     │ │ │ │   3     │ │ │ │   5     │ │ │ │...││
│ └─┘ └─────────┘ └─┘ └─────────┘ └─┘ └─────────┘ └─┘ └───┘│
│      ⤷ flèche →      ⤷ flèche →      ⤷ flèche →           │
│                                                             │
│ Chaîne: 4 cluster(s) | Clusters: 2, 3, 5, 65535           │
└────────────────────────────────────────────────────────────┘

Zones + : Déposez un cluster ici pour l'insérer à cette position
```

---

## 🔬 Cas d'Usage

### 1. Forensique Numérique
- Analyser des images disque suspectes
- Identifier des fichiers supprimés
- Reconstituer des chaînes FAT corrompues
- Extraire des données fragmentées

### 2. Récupération de Données
- Réparer des chaînages FAT cassés
- Reconstruire manuellement des fichiers
- Localiser des clusters orphelins

### 3. Éducation
- Apprendre la structure FAT16
- Comprendre le chaînage de clusters
- Visualiser l'organisation physique du disque
- Expérimenter avec des images test

### 4. Recherche
- Analyser le comportement du système de fichiers
- Tester des scénarios de corruption
- Développer des algorithmes de récupération

---

## 🧪 Créer une Image Test

Pour tester l'application, vous pouvez créer une petite image FAT16 :

```bash
# Créer une image de 10 MB
dd if=/dev/zero of=test.raw bs=1M count=10

# Formater en FAT16
mkfs.vfat -F 16 test.raw

# Monter l'image
sudo mkdir -p /mnt/test
sudo mount -o loop test.raw /mnt/test

# Créer des fichiers de test
echo "Test file 1" | sudo tee /mnt/test/file1.txt
echo "Test file 2" | sudo tee /mnt/test/file2.txt

# Démonter
sudo umount /mnt/test
```

Ensuite, ouvrez `test.raw` dans l'application !

---

## 🛠️ Développement

### Ajouter de Nouvelles Fonctionnalités

1. **Support FAT32** : Modifier `fat16_parser.py` pour gérer les différences FAT32
2. **Sauvegarde** : Implémenter l'écriture dans le fichier .raw
3. **Undo/Redo** : Ajouter un système de commandes réversibles
4. **Export** : Permettre d'exporter les clusters reconstruits

### Architecture MVC

L'application suit une architecture Modèle-Vue-Contrôleur :
- **Modèle** : `fat16_parser.py` (logique métier)
- **Vue** : Widgets PyQt6 (`hex_viewer.py`, `fat_chain_editor.py`)
- **Contrôleur** : `fat_simulator_gui.py` (gestion des événements)

---

## ⚠️ Limitations Actuelles

- ✋ **Lecture seule** : Les modifications ne sont pas encore sauvegardées
- ✋ **FAT16 uniquement** : FAT12 et FAT32 non supportés
- ✋ **Images < 5 GB** : Performance optimale pour petites images
- ✋ **Pas de validation** : Pas de vérification de cohérence FAT

---

## 🗺️ Roadmap

### Version 1.1 (Futur Proche)
- [ ] Sauvegarde des modifications dans le fichier .raw
- [ ] Édition directe des valeurs FAT en hexadécimal
- [ ] Drop à position spécifique dans la chaîne
- [ ] Export de chaînes FAT en JSON

### Version 1.2 (Futur)
- [ ] Support FAT32
- [ ] Détection automatique de corruption
- [ ] Reconstruction automatique de fichiers
- [ ] Comparaison FAT1 vs FAT2

### Version 2.0 (Futur Lointain)
- [ ] Support FAT12
- [ ] Mode diff pour comparer deux images
- [ ] Génération de rapports forensiques
- [ ] Plugin system

---

## 📝 Notes Techniques

### Format FAT16

**Structure de base :**
```
[Boot Sector] [Reserved] [FAT1] [FAT2] [Root Dir] [Data Zone]
     1           1-3      246     246      32      Reste
```

**Entrées FAT16 (2 octets)** :
- `0x0000` : Cluster libre
- `0x0002-0xFFEF` : Cluster suivant dans la chaîne
- `0xFFF0-0xFFF6` : Réservé
- `0xFFF7` : Cluster défectueux
- `0xFFF8-0xFFFF` : Fin de chaîne (EOF)

### PyQt6

Technologies utilisées :
- **PyQt6** : Framework GUI cross-platform
- **Signals/Slots** : Système d'événements Qt
- **Drag & Drop** : API Qt native
- **QPainter** : Rendu graphique personnalisé

---

## 📄 Licence

Ce projet est à usage **éducatif et de recherche forensique**.

⚠️ **Avertissement** : Utilisez cet outil uniquement sur vos propres images ou avec autorisation explicite. L'utilisation à des fins malveillantes est strictement interdite.

---

## 🙏 Crédits

Développé avec :
- Python 3
- PyQt6 (GUI framework)
- Inspiré par des outils forensiques comme Autopsy, FTK Imager

---

**Version** : 1.0.0
**Dernière mise à jour** : 2025
**Support** : FAT16 uniquement (pour l'instant)
