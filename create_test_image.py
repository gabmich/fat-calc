"""
Script pour créer une image disque FAT16 de test
Utile pour tester l'application sans avoir à créer manuellement une image
"""

import struct
import sys


def create_fat16_test_image(filename: str, size_mb: int = 10):
    """
    Crée une image disque FAT16 minimale pour les tests

    Args:
        filename: Nom du fichier à créer
        size_mb: Taille de l'image en MB (défaut: 10)
    """
    # Paramètres FAT16
    bytes_per_sector = 512
    sectors_per_cluster = 4
    reserved_sectors = 4
    num_fats = 2
    root_entries = 512
    media_descriptor = 0xF8
    sectors_per_track = 32
    num_heads = 64
    hidden_sectors = 0

    # Calculer le nombre de secteurs
    total_sectors = (size_mb * 1024 * 1024) // bytes_per_sector

    # Calculer le nombre de secteurs pour la FAT
    # Formule approximative : (total_clusters * 2) / bytes_per_sector
    # Pour simplifier, on utilise environ 1% de la taille totale
    sectors_per_fat = max(246, total_sectors // 100)

    print(f"Création d'une image FAT16 de {size_mb} MB...")
    print(f"  Secteurs totaux: {total_sectors}")
    print(f"  Octets par secteur: {bytes_per_sector}")
    print(f"  Secteurs par cluster: {sectors_per_cluster}")
    print(f"  Secteurs réservés: {reserved_sectors}")
    print(f"  Nombre de FATs: {num_fats}")
    print(f"  Secteurs par FAT: {sectors_per_fat}")
    print(f"  Entrées root: {root_entries}")

    # Créer le fichier
    with open(filename, 'wb') as f:
        # 1. Boot Sector (secteur 0)
        boot_sector = bytearray(512)

        # Jump boot (3 octets)
        boot_sector[0:3] = bytes([0xEB, 0x3C, 0x90])

        # OEM Name (8 octets)
        boot_sector[3:11] = b'TESTFAT '

        # BPB (BIOS Parameter Block)
        struct.pack_into('<H', boot_sector, 11, bytes_per_sector)      # Octets par secteur
        struct.pack_into('B', boot_sector, 13, sectors_per_cluster)     # Secteurs par cluster
        struct.pack_into('<H', boot_sector, 14, reserved_sectors)       # Secteurs réservés
        struct.pack_into('B', boot_sector, 16, num_fats)                # Nombre de FATs
        struct.pack_into('<H', boot_sector, 17, root_entries)           # Entrées root
        struct.pack_into('<H', boot_sector, 19, 0)                      # Total secteurs 16-bit (0 si > 65535)
        struct.pack_into('B', boot_sector, 21, media_descriptor)        # Media descriptor
        struct.pack_into('<H', boot_sector, 22, sectors_per_fat)        # Secteurs par FAT
        struct.pack_into('<H', boot_sector, 24, sectors_per_track)      # Secteurs par piste
        struct.pack_into('<H', boot_sector, 26, num_heads)              # Nombre de têtes
        struct.pack_into('<I', boot_sector, 28, hidden_sectors)         # Secteurs cachés
        struct.pack_into('<I', boot_sector, 32, total_sectors)          # Total secteurs 32-bit

        # EBPB (Extended BIOS Parameter Block)
        struct.pack_into('B', boot_sector, 36, 0x80)                    # Drive number
        struct.pack_into('B', boot_sector, 37, 0)                       # Reserved
        struct.pack_into('B', boot_sector, 38, 0x29)                    # Boot signature
        struct.pack_into('<I', boot_sector, 39, 0x12345678)             # Volume ID
        boot_sector[43:54] = b'TEST IMAGE '                             # Volume label
        boot_sector[54:62] = b'FAT16   '                                # File system type

        # Boot signature (2 derniers octets)
        struct.pack_into('<H', boot_sector, 510, 0xAA55)

        # Écrire le boot sector
        f.write(boot_sector)

        # 2. Secteurs réservés (secteurs 1-3)
        for i in range(1, reserved_sectors):
            f.write(bytes(bytes_per_sector))

        # 3. FAT 1
        fat = bytearray(sectors_per_fat * bytes_per_sector)
        # Les deux premières entrées sont réservées
        struct.pack_into('<H', fat, 0, 0xFFF8)  # Media descriptor
        struct.pack_into('<H', fat, 2, 0xFFFF)  # End of chain marker

        # Créer quelques chaînes de test
        # Chaîne 1: clusters 2 -> 3 -> 4 -> EOF
        struct.pack_into('<H', fat, 2 * 2, 3)      # Cluster 2 -> 3
        struct.pack_into('<H', fat, 3 * 2, 4)      # Cluster 3 -> 4
        struct.pack_into('<H', fat, 4 * 2, 0xFFFF) # Cluster 4 -> EOF

        # Chaîne 2: clusters 5 -> 6 -> EOF
        struct.pack_into('<H', fat, 5 * 2, 6)      # Cluster 5 -> 6
        struct.pack_into('<H', fat, 6 * 2, 0xFFFF) # Cluster 6 -> EOF

        # Chaîne cassée : cluster 7 -> 0x0000 (cassé)
        struct.pack_into('<H', fat, 7 * 2, 0x0000) # Cluster 7 cassé

        f.write(fat)

        # 4. FAT 2 (copie de FAT 1)
        f.write(fat)

        # 5. Root Directory
        root_dir_sectors = ((root_entries * 32) + (bytes_per_sector - 1)) // bytes_per_sector
        root_dir = bytearray(root_dir_sectors * bytes_per_sector)

        # Créer quelques entrées de test
        # Entrée 1: TEST.TXT
        entry_offset = 0
        root_dir[entry_offset:entry_offset + 11] = b'TEST    TXT'
        root_dir[entry_offset + 11] = 0x20  # Attribut: archive
        struct.pack_into('<H', root_dir, entry_offset + 26, 2)  # Premier cluster: 2
        struct.pack_into('<I', root_dir, entry_offset + 28, 1024)  # Taille: 1024 octets

        # Entrée 2: DATA.BIN
        entry_offset = 32
        root_dir[entry_offset:entry_offset + 11] = b'DATA    BIN'
        root_dir[entry_offset + 11] = 0x20  # Attribut: archive
        struct.pack_into('<H', root_dir, entry_offset + 26, 5)  # Premier cluster: 5
        struct.pack_into('<I', root_dir, entry_offset + 28, 2048)  # Taille: 2048 octets

        # Entrée 3: BROKEN.DAT (pointant vers cluster cassé)
        entry_offset = 64
        root_dir[entry_offset:entry_offset + 11] = b'BROKEN  DAT'
        root_dir[entry_offset + 11] = 0x20  # Attribut: archive
        struct.pack_into('<H', root_dir, entry_offset + 26, 7)  # Premier cluster: 7 (cassé)
        struct.pack_into('<I', root_dir, entry_offset + 28, 512)  # Taille: 512 octets

        f.write(root_dir)

        # 6. Zone de données
        # Calculer le nombre de secteurs de données
        first_data_sector = reserved_sectors + (num_fats * sectors_per_fat) + root_dir_sectors
        data_sectors = total_sectors - first_data_sector

        # Écrire des données de test dans les premiers clusters
        cluster_size = sectors_per_cluster * bytes_per_sector

        # Cluster 2 (TEST.TXT)
        cluster_2 = b"Ceci est le contenu du fichier TEST.TXT\n" * 20
        cluster_2 = cluster_2[:cluster_size].ljust(cluster_size, b'\x00')
        f.write(cluster_2)

        # Cluster 3 (suite de TEST.TXT)
        cluster_3 = b"Suite du fichier TEST.TXT (cluster 3)\n" * 20
        cluster_3 = cluster_3[:cluster_size].ljust(cluster_size, b'\x00')
        f.write(cluster_3)

        # Cluster 4 (fin de TEST.TXT)
        cluster_4 = b"Fin du fichier TEST.TXT (cluster 4)\n"
        cluster_4 = cluster_4.ljust(cluster_size, b'\x00')
        f.write(cluster_4)

        # Cluster 5 (DATA.BIN)
        cluster_5 = bytes(range(256)) * (cluster_size // 256)
        f.write(cluster_5)

        # Cluster 6 (suite de DATA.BIN)
        cluster_6 = bytes(range(255, -1, -1)) * (cluster_size // 256)
        f.write(cluster_6)

        # Cluster 7 (BROKEN.DAT - données corrompues)
        cluster_7 = b'\xDE\xAD\xBE\xEF' * (cluster_size // 4)
        f.write(cluster_7)

        # Remplir le reste avec des zéros
        remaining_clusters = (data_sectors - 7 * sectors_per_cluster) // sectors_per_cluster
        for i in range(remaining_clusters):
            f.write(bytes(cluster_size))

    print(f"✓ Image créée: {filename}")
    print(f"\nFichiers de test créés dans l'image:")
    print(f"  1. TEST.TXT    (clusters 2, 3, 4) - chaîne complète")
    print(f"  2. DATA.BIN    (clusters 5, 6)    - chaîne complète")
    print(f"  3. BROKEN.DAT  (cluster 7)        - chaîne cassée ⚠️")
    print(f"\nVous pouvez maintenant ouvrir '{filename}' dans l'application !")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "test_fat16.raw"

    if len(sys.argv) > 2:
        size_mb = int(sys.argv[2])
    else:
        size_mb = 10

    create_fat16_test_image(filename, size_mb)
