#!/bin/bash

# Script de lancement du FAT Simulator

echo "==================================="
echo "FAT16 Simulator - Forensic Tool"
echo "==================================="
echo ""

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "⚠️  Environnement virtuel non trouvé. Création..."
    python3 -m venv venv

    echo "📦 Installation des dépendances..."
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✓ Installation terminée"
    echo ""
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Lancer l'application
echo "🚀 Lancement du FAT Simulator..."
echo ""
python fat_simulator_gui.py

# Désactiver l'environnement
deactivate
