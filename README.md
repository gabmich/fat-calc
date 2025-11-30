# Calculateur FAT - Offsets et Secteurs

Un ensemble d'outils complets pour calculer les offsets et positions dans une partition FAT (FAT12, FAT16, FAT32) avec une interface graphique moderne et une cartographie visuelle interactive.

![License](https://img.shields.io/badge/license-Educational-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

## 🎯 Fonctionnalités

### Calculs Automatiques
- ✅ Calcul du premier secteur de données
- ✅ Calcul de l'offset de la zone de données
- ✅ Calcul de l'offset d'un cluster spécifique
- ✅ **Calcul automatique de la taille totale de la partition** (basé sur le type FAT)
- ✅ Support FAT12, FAT16 et FAT32

### Interface Graphique (GUI)
- 🎨 Interface moderne avec TTK Bootstrap
- 🗺️ **Cartographie visuelle interactive** de la partition
  - 1 carré = 1 secteur (détail maximal)
  - Couleurs distinctes par zone (Boot, FAT1, FAT2, Root, Data)
  - Scrollbar verticale pour explorer toute la partition
  - Support molette de souris
- 🔍 **Recherche de cluster avec mise en évidence**
  - Bordure rouge autour du cluster trouvé
  - Scroll automatique vers le cluster
  - Label "CLUSTER X" visible
- 💡 Tooltips informatifs au survol (type de zone, plage de secteurs)
- ⌨️ Support touche Entrée pour lancer la recherche
- 📊 Affichage en décimal et hexadécimal

### Outils en Ligne de Commande
- 🖥️ Interface CLI interactive
- 📦 Module Python réutilisable dans vos propres scripts

### Tests et Qualité
- ✅ Suite de tests unitaires complète (15 tests)
- ✅ Tests de régression pour éviter les régressions
- ✅ Support configurations FAT12, FAT16, FAT32

## 📥 Installation

### 1. Prérequis système (pour l'interface graphique)

**Sur Ubuntu/Debian :**
```bash
sudo apt-get install python3-tk
```

**Sur Fedora/RHEL :**
```bash
sudo dnf install python3-tkinter
```

**Sur Arch Linux :**
```bash
sudo pacman -S tk
```

### 2. Configuration de l'environnement

```bash
# Cloner ou télécharger le projet
cd fat-calc

# Créer l'environnement virtuel
python3 -m venv env

# Activer l'environnement
source env/bin/activate  # Linux/Mac
# ou
env\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## 🚀 Utilisation

### Interface Graphique (GUI) - Recommandé

**Lancement rapide :**
```bash
./run_gui.sh
```

**Ou manuellement :**
```bash
source env/bin/activate
python fatcalc_gui.py
```

#### Fonctionnalités de la GUI

1. **Sélection du type de FAT**
   - Dropdown : FAT12 / FAT16 / FAT32
   - Calcul automatique basé sur le type sélectionné

2. **Paramètres de partition** (valeurs par défaut pré-remplies)
   - Octets par secteur : `512`
   - Secteurs par cluster : `4`
   - Secteurs réservés : `4`
   - Nombre de zones FAT : `2`
   - Secteurs par zone FAT : `246`
   - Entrées du répertoire racine : `512`

3. **Calcul et affichage**
   - Cliquez sur **"Calculer les Informations"**
   - Vue textuelle détaillée à gauche
   - Cartographie visuelle interactive à droite

4. **Cartographie interactive**
   - **Légende des couleurs :**
     - 🟡 Jaune : Boot Sector
     - 🔴 Rouge : Reserved Sectors
     - 🟢 Vert clair : FAT 1
     - 🟢 Vert foncé : FAT 2
     - 🟠 Orange : Root Directory
     - 🔵 Bleu : Data Zone
   - **Navigation :**
     - Scrollbar verticale ou molette de souris
     - 1 carré = 1 secteur (détail complet)
     - Passez la souris sur un carré pour voir les détails

5. **Recherche de cluster**
   - Entrez le numéro de cluster (ex: `562`)
   - Cliquez "Rechercher" ou appuyez sur **Entrée**
   - Le cluster est automatiquement mis en évidence en rouge
   - La vue scrolle vers le cluster
   - L'offset est affiché (décimal et hexadécimal)

### Interface en Ligne de Commande (CLI)

```bash
source env/bin/activate
python fatcalc.py
```

Exemple d'interaction :
```
CALCULATEUR D'OFFSETS POUR PARTITION FAT
============================================================

Type de FAT (FAT12, FAT16, ou FAT32) [défaut: FAT16] : FAT16
Nombre d'octets par secteur : 512
Nombre de secteurs par cluster : 4
...
```

### Utilisation comme Module Python

```python
from FATPartition import FATPartition

# Créer une partition FAT16
partition = FATPartition(
    octets_per_sector=512,
    sectors_per_cluster=4,
    reserved_sectors=4,
    fat_count=2,
    sectors_per_fat=246,
    root_entries=512,
    fat_type="FAT16"  # Nouveau paramètre
)

# Afficher toutes les informations
partition.print_info()

# Obtenir l'offset d'un cluster
offset = partition.get_cluster_offset(10)
print(f"Cluster 10 : {offset} octets (0x{offset:X})")

# Accéder aux propriétés calculées automatiquement
print(f"Total secteurs : {partition.total_sectors}")
print(f"Total clusters : {partition.total_data_clusters}")
print(f"Taille partition : {partition.total_sectors * partition.octets_per_sector} octets")

# Obtenir toutes les infos en dictionnaire
info = partition.get_info()
print(info)
```

#### Propriétés disponibles

**Propriétés de base :**
- `octets_per_sector`
- `sectors_per_cluster`
- `reserved_sectors`
- `fat_count`
- `sectors_per_fat`
- `root_entries`
- `fat_type`

**Propriétés calculées :**
- `root_directory_sectors` : Secteurs occupés par le root directory
- `fat_allocated_sectors` : Secteurs totaux des FAT
- `first_data_sector` : Numéro du premier secteur de données
- `data_zone_offset` : Offset en octets de la zone data
- `cluster_size_bytes` : Taille d'un cluster en octets
- `bytes_per_fat_entry` : Octets par entrée FAT (1.5, 2 ou 4)
- `total_fat_entries` : Nombre total d'entrées FAT
- `total_data_clusters` : Nombre de clusters disponibles
- `total_data_sectors` : Nombre de secteurs de données
- `total_sectors` : **Taille totale de la partition en secteurs** ⭐

**Méthodes :**
- `get_cluster_offset(cluster_number)` : Retourne l'offset d'un cluster
- `get_sector_offset(sector_number)` : Retourne l'offset d'un secteur
- `get_info()` : Retourne toutes les infos en dictionnaire
- `print_info()` : Affiche toutes les informations

## 🧪 Tests

Exécuter les tests unitaires :

```bash
source env/bin/activate
python test_fatcalc.py
```

Avec affichage détaillé :
```bash
python test_fatcalc.py -v
```

**Suite de tests (15 tests) :**
- Paramètres d'initialisation
- Calculs de secteurs et clusters
- Calculs d'offsets
- Validation des erreurs
- Configurations FAT12/16/32

## 📂 Structure du Projet

```
fat-calc/
├── FATPartition.py      # Classe principale avec calculs intelligents
├── fatcalc.py           # Interface CLI interactive
├── fatcalc_gui.py       # Interface graphique moderne (GUI)
├── test_fatcalc.py      # Suite de tests unitaires (15 tests)
├── requirements.txt     # Dépendances Python (ttkbootstrap)
├── run_gui.sh           # Script de lancement rapide de la GUI
├── .gitignore           # Fichiers à ignorer par Git
├── env/                 # Environnement virtuel Python (à créer)
└── README.md            # Documentation complète
```

## 📊 Calculs Effectués

### Structure d'une Partition FAT

```
┌─────────────────┬───────┬───────┬──────────────┬────────────────────┐
│ Boot + Reserved │ FAT 1 │ FAT 2 │ Root Dir     │ Data Zone          │
│ (jaune + rouge) │(vert) │(vert) │ (orange)     │ (bleu)             │
└─────────────────┴───────┴───────┴──────────────┴────────────────────┘
```

### Formules Utilisées

#### Formules de base
- **Secteurs du répertoire racine** : `(nombre_entrées × 32) ÷ octets_par_secteur`
- **Secteurs FAT totaux** : `nombre_zones_FAT × secteurs_par_zone_FAT`
- **Premier secteur de données** : `secteurs_réservés + secteurs_FAT + secteurs_root_dir`
- **Offset zone de données** : `premier_secteur_données × octets_par_secteur`
- **Offset cluster N** : `(premier_secteur_données + (N - 2) × secteurs_par_cluster) × octets_par_secteur`

#### Calculs automatiques intelligents (⭐ Nouveau)
- **Octets par entrée FAT** :
  - FAT12 : 1.5 octets
  - FAT16 : 2 octets
  - FAT32 : 4 octets
- **Entrées FAT totales** : `(secteurs_par_FAT × octets_par_secteur) ÷ octets_par_entrée`
- **Clusters de données** : `entrées_FAT_totales - 2` (clusters 0 et 1 réservés)
- **Secteurs de données** : `clusters_de_données × secteurs_par_cluster`
- **Total secteurs partition** : `premier_secteur_données + secteurs_de_données`

### Exemple de Calcul (FAT16)

**Entrées :**
```
Type FAT : FAT16
Octets/secteur : 512
Secteurs/cluster : 4
Secteurs réservés : 4
Zones FAT : 2
Secteurs/FAT : 246
Entrées root : 512
```

**Calculs intermédiaires :**
```
Root directory : (512 × 32) ÷ 512 = 32 secteurs
FAT totaux : 2 × 246 = 492 secteurs
1er secteur data : 4 + 492 + 32 = 528
```

**Calculs automatiques :**
```
Entrées FAT : (246 × 512) ÷ 2 = 62,976 entrées
Clusters data : 62,976 - 2 = 62,974 clusters
Secteurs data : 62,974 × 4 = 251,896 secteurs
TOTAL : 528 + 251,896 = 252,424 secteurs (~123 MB)
```

**Cluster 562 :**
```
Secteur : 528 + (562 - 2) × 4 = 2,768
Offset : 2,768 × 512 = 1,417,216 octets (0x15A000)
```

## 📖 Exemples de Configurations

### Disquette 1.44 MB (FAT12)
```
Type FAT : FAT12
Octets/secteur : 512
Secteurs/cluster : 1
Secteurs réservés : 1
Zones FAT : 2
Secteurs/FAT : 9
Entrées root : 224
→ Total : 2,880 secteurs (1.44 MB)
```

### Partition FAT16 Typique (128 MB)
```
Type FAT : FAT16
Octets/secteur : 512
Secteurs/cluster : 4
Secteurs réservés : 4
Zones FAT : 2
Secteurs/FAT : 246
Entrées root : 512
→ Total : ~252,424 secteurs (~123 MB)
```

### Partition FAT32 (1 GB)
```
Type FAT : FAT32
Octets/secteur : 512
Secteurs/cluster : 8
Secteurs réservés : 32
Zones FAT : 2
Secteurs/FAT : 1,952
Entrées root : 0 (FAT32 n'a pas de root directory fixe)
→ Total : ~2,000,000+ secteurs (~1 GB)
```

## 🎯 Cas d'Usage

### Forensique Numérique
- Localiser précisément des données sur un disque
- Analyser la structure d'une partition récupérée
- Identifier l'emplacement exact de fichiers

### Récupération de Données
- Calculer les offsets pour accéder directement aux données
- Trouver des fichiers supprimés via leurs clusters
- Reconstruire la structure de la partition

### Analyse de Systèmes de Fichiers
- Comprendre la structure FAT en détail
- Visualiser l'organisation d'une partition
- Étudier l'impact de différentes configurations

### Éducation
- Apprendre le fonctionnement des systèmes de fichiers FAT
- Visualiser graphiquement la structure d'une partition
- Expérimenter avec différentes configurations

## 🔧 Développement

### Ajouter de nouveaux tests

Ajoutez vos tests dans `test_fatcalc.py` :

```python
def test_my_new_feature(self):
    """Description du test."""
    partition = FATPartition(...)
    self.assertEqual(partition.my_value, expected_value)
```

### Contribuer

1. Fork le projet
2. Créez une branche pour votre fonctionnalité
3. Ajoutez des tests
4. Assurez-vous que tous les tests passent
5. Soumettez une pull request

## ⚠️ Notes Importantes

- **Clusters 0 et 1** : Réservés dans la FAT, les clusters de données commencent à 2
- **FAT32 Root Directory** : N'a pas de taille fixe (contrairement à FAT12/16)
- **1 carré = 1 secteur** : Dans la cartographie GUI pour un maximum de détails
- **Calcul automatique** : Le nombre total de secteurs est calculé automatiquement selon le type FAT

## 📝 Licence

Ce projet est à usage **éducatif et de recherche**.

## 🙏 Crédits

Développé avec :
- Python 3
- TTK Bootstrap (interface graphique moderne)
- Tkinter (widgets graphiques)

---

**Version** : 2.0
**Dernière mise à jour** : 2025
**Support** : FAT12, FAT16, FAT32
