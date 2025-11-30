class FATPartition:
    """
    Classe pour calculer les valeurs et offsets d'une partition FAT.
    """

    # Constante : taille d'une entrée de répertoire en octets - ne change jamais
    # en FAT12, FAT16, FAT32
    DIRECTORY_ENTRY_SIZE = 32

    def __init__(self, octets_per_sector, sectors_per_cluster, reserved_sectors,
                 fat_count, sectors_per_fat, root_entries, fat_type="FAT16"):
        """
        Initialise une partition FAT avec ses paramètres.

        Args:
            octets_per_sector: Nombre d'octets par secteur (généralement 512)
            sectors_per_cluster: Nombre de secteurs par cluster
            reserved_sectors: Nombre de secteurs réservés (boot sector, etc.)
            fat_count: Nombre de zones FAT (généralement 2)
            sectors_per_fat: Nombre de secteurs par zone FAT
            root_entries: Nombre d'entrées dans le répertoire racine
            fat_type: Type de FAT ("FAT12", "FAT16", ou "FAT32")
        """
        self.octets_per_sector = octets_per_sector
        self.sectors_per_cluster = sectors_per_cluster
        self.reserved_sectors = reserved_sectors
        self.fat_count = fat_count
        self.sectors_per_fat = sectors_per_fat
        self.root_entries = root_entries
        self.fat_type = fat_type

    @property
    def root_directory_sectors(self):
        """Calcule le nombre de secteurs occupés par le répertoire racine."""
        return (self.root_entries * self.DIRECTORY_ENTRY_SIZE) // self.octets_per_sector

    @property
    def fat_allocated_sectors(self):
        """Calcule le nombre total de secteurs alloués aux zones FAT."""
        return self.fat_count * self.sectors_per_fat

    @property
    def first_data_sector(self):
        """
        Calcule le numéro du premier secteur de la zone de données (cluster 2).
        Structure : [Réservés] [FAT1] [FAT2] [Root Dir] [Data Zone]
        """
        return self.reserved_sectors + self.fat_allocated_sectors + self.root_directory_sectors

    @property
    def data_zone_offset(self):
        """Calcule l'offset en octets du début de la zone de données."""
        return self.first_data_sector * self.octets_per_sector

    @property
    def cluster_size_bytes(self):
        """Calcule la taille d'un cluster en octets."""
        return self.sectors_per_cluster * self.octets_per_sector

    @property
    def bytes_per_fat_entry(self):
        """Retourne le nombre d'octets par entrée FAT selon le type."""
        if self.fat_type == "FAT12":
            return 1.5
        elif self.fat_type == "FAT16":
            return 2
        elif self.fat_type == "FAT32":
            return 4
        else:
            return 2  # Par défaut FAT16

    @property
    def total_fat_entries(self):
        """Calcule le nombre total d'entrées dans la FAT."""
        fat_size_bytes = self.sectors_per_fat * self.octets_per_sector
        return int(fat_size_bytes / self.bytes_per_fat_entry)

    @property
    def total_data_clusters(self):
        """Calcule le nombre total de clusters de données disponibles."""
        # Les 2 premières entrées (0 et 1) sont réservées
        return self.total_fat_entries - 2

    @property
    def total_data_sectors(self):
        """Calcule le nombre total de secteurs de données."""
        return self.total_data_clusters * self.sectors_per_cluster

    @property
    def total_sectors(self):
        """Calcule le nombre total de secteurs de la partition."""
        return self.first_data_sector + self.total_data_sectors

    def get_cluster_offset(self, cluster_number):
        """
        Calcule l'offset en octets pour un cluster donné.

        Args:
            cluster_number: Numéro du cluster (commence à 2 pour les données)

        Returns:
            L'offset en octets depuis le début de la partition
        """
        if cluster_number < 2:
            raise ValueError("Les clusters de données commencent au numéro 2")

        # (cluster_number - 2) car les clusters 0 et 1 sont réservés dans la FAT
        return (self.first_data_sector + (cluster_number - 2) * self.sectors_per_cluster) * self.octets_per_sector

    def get_sector_offset(self, sector_number):
        """
        Calcule l'offset en octets pour un secteur donné.

        Args:
            sector_number: Numéro du secteur absolu

        Returns:
            L'offset en octets depuis le début de la partition
        """
        return sector_number * self.octets_per_sector

    def get_fat_entry_offset(self, cluster_number, fat_number=1):
        """
        Calcule l'offset en octets de l'entrée d'un cluster dans la FAT.

        Args:
            cluster_number: Numéro du cluster (0 à total_fat_entries - 1)
            fat_number: Numéro de la FAT (1 ou 2, défaut: 1)

        Returns:
            L'offset en octets depuis le début de la partition
        """
        if cluster_number < 0 or cluster_number >= self.total_fat_entries:
            raise ValueError(f"Le numéro de cluster doit être entre 0 et {self.total_fat_entries - 1}")

        if fat_number not in [1, 2]:
            raise ValueError("Le numéro de FAT doit être 1 ou 2")

        # Offset de base de la FAT
        if fat_number == 1:
            fat_start_offset = self.reserved_sectors * self.octets_per_sector
        else:
            fat_start_offset = (self.reserved_sectors + self.sectors_per_fat) * self.octets_per_sector

        # Pour FAT12, le calcul est un peu spécial (1.5 octets par entrée)
        if self.fat_type == "FAT12":
            # Chaque cluster utilise 1.5 octets = 12 bits
            # 2 entrées utilisent 3 octets
            byte_offset = int(cluster_number * 1.5)
        else:
            # FAT16 et FAT32 : simple multiplication
            byte_offset = int(cluster_number * self.bytes_per_fat_entry)

        return fat_start_offset + byte_offset

    def get_info(self):
        """Retourne un dictionnaire avec toutes les informations de la partition."""
        return {
            'fat_type': self.fat_type,
            'octets_per_sector': self.octets_per_sector,
            'sectors_per_cluster': self.sectors_per_cluster,
            'cluster_size_bytes': self.cluster_size_bytes,
            'reserved_sectors': self.reserved_sectors,
            'fat_count': self.fat_count,
            'sectors_per_fat': self.sectors_per_fat,
            'root_entries': self.root_entries,
            'root_directory_sectors': self.root_directory_sectors,
            'fat_allocated_sectors': self.fat_allocated_sectors,
            'first_data_sector': self.first_data_sector,
            'data_zone_offset': self.data_zone_offset,
            'total_fat_entries': self.total_fat_entries,
            'total_data_clusters': self.total_data_clusters,
            'total_data_sectors': self.total_data_sectors,
            'total_sectors': self.total_sectors
        }

    def print_info(self):
        """Affiche toutes les informations de la partition."""
        print("=" * 60)
        print("INFORMATIONS DE LA PARTITION FAT")
        print("=" * 60)
        print(f"Type de FAT                : {self.fat_type}")
        print(f"Octets par secteur         : {self.octets_per_sector}")
        print(f"Secteurs par cluster       : {self.sectors_per_cluster}")
        print(f"Taille d'un cluster        : {self.cluster_size_bytes} octets")
        print(f"Secteurs réservés          : {self.reserved_sectors}")
        print(f"Nombre de zones FAT        : {self.fat_count}")
        print(f"Secteurs par zone FAT      : {self.sectors_per_fat}")
        print(f"Secteurs FAT totaux        : {self.fat_allocated_sectors}")
        print(f"Entrées répertoire racine  : {self.root_entries}")
        print(f"Secteurs répertoire racine : {self.root_directory_sectors}")
        print("-" * 60)
        print(f"1er secteur de données     : {self.first_data_sector}")
        print(f"Offset zone de données     : {self.data_zone_offset} octets (0x{self.data_zone_offset:X})")
        print(f"Nombre total d'entrées FAT : {self.total_fat_entries}")
        print(f"Nombre de clusters données : {self.total_data_clusters}")
        print(f"Secteurs de données totaux : {self.total_data_sectors}")
        print(f"Nombre total de secteurs   : {self.total_sectors}")
        print("=" * 60)
