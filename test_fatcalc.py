import unittest
from FATPartition import FATPartition


class TestFATPartition(unittest.TestCase):
    """
    Tests unitaires pour la classe FATPartition.
    Utilise des valeurs de référence pour s'assurer que les calculs restent corrects.
    """

    def setUp(self):
        """
        Initialise une partition de test avec les valeurs de référence :
        - 512 octets/secteur
        - 4 secteurs/cluster
        - 4 secteurs réservés
        - 2 zones FAT
        - 246 secteurs/FAT
        - 512 entrées root directory
        """
        self.partition = FATPartition(
            octets_per_sector=512,
            sectors_per_cluster=4,
            reserved_sectors=4,
            fat_count=2,
            sectors_per_fat=246,
            root_entries=512,
            fat_type="FAT16"
        )

    def test_parameters(self):
        """Vérifie que les paramètres d'initialisation sont correctement stockés."""
        self.assertEqual(self.partition.octets_per_sector, 512)
        self.assertEqual(self.partition.sectors_per_cluster, 4)
        self.assertEqual(self.partition.reserved_sectors, 4)
        self.assertEqual(self.partition.fat_count, 2)
        self.assertEqual(self.partition.sectors_per_fat, 246)
        self.assertEqual(self.partition.root_entries, 512)

    def test_cluster_size_bytes(self):
        """Vérifie que la taille d'un cluster est correctement calculée."""
        self.assertEqual(self.partition.cluster_size_bytes, 2048)

    def test_root_directory_sectors(self):
        """Vérifie le calcul du nombre de secteurs du répertoire racine."""
        # 512 entrées * 32 octets / 512 octets par secteur = 32 secteurs
        self.assertEqual(self.partition.root_directory_sectors, 32)

    def test_fat_allocated_sectors(self):
        """Vérifie le calcul du nombre total de secteurs alloués aux FAT."""
        # 2 zones FAT * 246 secteurs = 492 secteurs
        self.assertEqual(self.partition.fat_allocated_sectors, 492)

    def test_first_data_sector(self):
        """Vérifie le calcul du premier secteur de données."""
        # 4 (réservés) + 492 (FAT) + 32 (root dir) = 528
        self.assertEqual(self.partition.first_data_sector, 528)

    def test_data_zone_offset(self):
        """Vérifie le calcul de l'offset de la zone de données."""
        # 528 secteurs * 512 octets = 270336 octets (0x42000)
        self.assertEqual(self.partition.data_zone_offset, 270336)
        self.assertEqual(self.partition.data_zone_offset, 0x42000)

    def test_cluster_2_offset(self):
        """Vérifie que le cluster 2 (premier cluster de données) a le bon offset."""
        # Le cluster 2 doit être au début de la zone de données
        offset = self.partition.get_cluster_offset(2)
        self.assertEqual(offset, 270336)
        self.assertEqual(offset, 0x42000)

    def test_cluster_3_offset(self):
        """Vérifie le calcul de l'offset du cluster 3."""
        # Cluster 3 = cluster 2 + 1 cluster (2048 octets)
        # 270336 + 2048 = 272384 (0x42800)
        offset = self.partition.get_cluster_offset(3)
        self.assertEqual(offset, 272384)
        self.assertEqual(offset, 0x42800)

    def test_cluster_10_offset(self):
        """Vérifie le calcul de l'offset du cluster 10."""
        # Cluster 10 = cluster 2 + 8 clusters (8 * 2048 = 16384)
        # 270336 + 16384 = 286720 (0x46000)
        offset = self.partition.get_cluster_offset(10)
        self.assertEqual(offset, 286720)
        self.assertEqual(offset, 0x46000)

    def test_cluster_invalid(self):
        """Vérifie que les clusters < 2 lèvent une exception."""
        with self.assertRaises(ValueError) as context:
            self.partition.get_cluster_offset(0)
        self.assertIn("commencent au numéro 2", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.partition.get_cluster_offset(1)
        self.assertIn("commencent au numéro 2", str(context.exception))

    def test_sector_offset(self):
        """Vérifie le calcul de l'offset d'un secteur."""
        # Secteur 0 = offset 0
        self.assertEqual(self.partition.get_sector_offset(0), 0)
        # Secteur 1 = 512 octets
        self.assertEqual(self.partition.get_sector_offset(1), 512)
        # Secteur 528 (premier data sector) = 270336 octets
        self.assertEqual(self.partition.get_sector_offset(528), 270336)

    def test_fat_entry_offset_fat1(self):
        """Vérifie le calcul de l'offset d'une entrée dans FAT1."""
        # FAT1 commence à : 4 secteurs réservés * 512 = 2048 octets
        # Cluster 0 dans FAT1 : 2048 + (0 * 2) = 2048
        self.assertEqual(self.partition.get_fat_entry_offset(0, 1), 2048)
        # Cluster 2 dans FAT1 : 2048 + (2 * 2) = 2052
        self.assertEqual(self.partition.get_fat_entry_offset(2, 1), 2052)
        # Cluster 10 dans FAT1 : 2048 + (10 * 2) = 2068
        self.assertEqual(self.partition.get_fat_entry_offset(10, 1), 2068)

    def test_fat_entry_offset_fat2(self):
        """Vérifie le calcul de l'offset d'une entrée dans FAT2."""
        # FAT2 commence à : (4 + 246) secteurs * 512 = 128000 octets
        # Cluster 0 dans FAT2 : 128000 + (0 * 2) = 128000
        self.assertEqual(self.partition.get_fat_entry_offset(0, 2), 128000)
        # Cluster 2 dans FAT2 : 128000 + (2 * 2) = 128004
        self.assertEqual(self.partition.get_fat_entry_offset(2, 2), 128004)
        # Cluster 10 dans FAT2 : 128000 + (10 * 2) = 128020
        self.assertEqual(self.partition.get_fat_entry_offset(10, 2), 128020)

    def test_fat_entry_offset_invalid_cluster(self):
        """Vérifie que les numéros de cluster invalides lèvent une exception."""
        # Cluster négatif
        with self.assertRaises(ValueError):
            self.partition.get_fat_entry_offset(-1, 1)
        # Cluster trop grand
        with self.assertRaises(ValueError):
            self.partition.get_fat_entry_offset(self.partition.total_fat_entries, 1)

    def test_fat_entry_offset_invalid_fat_number(self):
        """Vérifie que les numéros de FAT invalides lèvent une exception."""
        with self.assertRaises(ValueError):
            self.partition.get_fat_entry_offset(2, 0)
        with self.assertRaises(ValueError):
            self.partition.get_fat_entry_offset(2, 3)

    def test_get_info_dictionary(self):
        """Vérifie que get_info() retourne un dictionnaire complet."""
        info = self.partition.get_info()

        self.assertIsInstance(info, dict)
        self.assertEqual(info['octets_per_sector'], 512)
        self.assertEqual(info['sectors_per_cluster'], 4)
        self.assertEqual(info['cluster_size_bytes'], 2048)
        self.assertEqual(info['reserved_sectors'], 4)
        self.assertEqual(info['fat_count'], 2)
        self.assertEqual(info['sectors_per_fat'], 246)
        self.assertEqual(info['root_entries'], 512)
        self.assertEqual(info['root_directory_sectors'], 32)
        self.assertEqual(info['fat_allocated_sectors'], 492)
        self.assertEqual(info['first_data_sector'], 528)
        self.assertEqual(info['data_zone_offset'], 270336)


class TestFATPartitionDifferentConfigurations(unittest.TestCase):
    """Tests avec différentes configurations FAT pour vérifier la robustesse."""

    def test_typical_fat16_floppy(self):
        """Test avec une configuration typique de disquette FAT16 1.44MB."""
        partition = FATPartition(
            octets_per_sector=512,
            sectors_per_cluster=1,
            reserved_sectors=1,
            fat_count=2,
            sectors_per_fat=9,
            root_entries=224,
            fat_type="FAT16"
        )

        # 224 * 32 / 512 = 14 secteurs
        self.assertEqual(partition.root_directory_sectors, 14)
        # 2 * 9 = 18 secteurs FAT
        self.assertEqual(partition.fat_allocated_sectors, 18)
        # 1 + 18 + 14 = 33
        self.assertEqual(partition.first_data_sector, 33)
        # 33 * 512 = 16896
        self.assertEqual(partition.data_zone_offset, 16896)

    def test_typical_fat32(self):
        """Test avec une configuration typique FAT32 (root_entries = 0 pour FAT32)."""
        partition = FATPartition(
            octets_per_sector=512,
            sectors_per_cluster=8,
            reserved_sectors=32,
            fat_count=2,
            sectors_per_fat=1952,
            root_entries=0,  # FAT32 n'a pas de root directory fixe
            fat_type="FAT32"
        )

        self.assertEqual(partition.root_directory_sectors, 0)
        self.assertEqual(partition.fat_allocated_sectors, 3904)
        self.assertEqual(partition.first_data_sector, 3936)
        self.assertEqual(partition.data_zone_offset, 2015232)

    def test_large_sector_size(self):
        """Test avec une taille de secteur non standard (4096 octets)."""
        partition = FATPartition(
            octets_per_sector=4096,
            sectors_per_cluster=1,
            reserved_sectors=1,
            fat_count=2,
            sectors_per_fat=5,
            root_entries=128,
            fat_type="FAT16"
        )

        # 128 * 32 / 4096 = 1 secteur
        self.assertEqual(partition.root_directory_sectors, 1)
        self.assertEqual(partition.cluster_size_bytes, 4096)

    def test_fat12_entry_offset(self):
        """Test de l'offset FAT avec FAT12 (1.5 octets par entrée)."""
        partition = FATPartition(
            octets_per_sector=512,
            sectors_per_cluster=1,
            reserved_sectors=1,
            fat_count=2,
            sectors_per_fat=9,
            root_entries=224,
            fat_type="FAT12"
        )

        # FAT1 commence à : 1 secteur * 512 = 512 octets
        # Cluster 0 dans FAT1 : 512 + int(0 * 1.5) = 512
        self.assertEqual(partition.get_fat_entry_offset(0, 1), 512)
        # Cluster 2 dans FAT1 : 512 + int(2 * 1.5) = 512 + 3 = 515
        self.assertEqual(partition.get_fat_entry_offset(2, 1), 515)
        # Cluster 4 dans FAT1 : 512 + int(4 * 1.5) = 512 + 6 = 518
        self.assertEqual(partition.get_fat_entry_offset(4, 1), 518)

    def test_fat32_entry_offset(self):
        """Test de l'offset FAT avec FAT32 (4 octets par entrée)."""
        partition = FATPartition(
            octets_per_sector=512,
            sectors_per_cluster=8,
            reserved_sectors=32,
            fat_count=2,
            sectors_per_fat=1952,
            root_entries=0,
            fat_type="FAT32"
        )

        # FAT1 commence à : 32 secteurs * 512 = 16384 octets
        # Cluster 0 dans FAT1 : 16384 + (0 * 4) = 16384
        self.assertEqual(partition.get_fat_entry_offset(0, 1), 16384)
        # Cluster 2 dans FAT1 : 16384 + (2 * 4) = 16392
        self.assertEqual(partition.get_fat_entry_offset(2, 1), 16392)
        # Cluster 10 dans FAT1 : 16384 + (10 * 4) = 16424
        self.assertEqual(partition.get_fat_entry_offset(10, 1), 16424)


if __name__ == '__main__':
    unittest.main(verbosity=2)
