"""
Parser pour images disque FAT16 (.raw)
Lit et analyse la structure d'une partition FAT16
"""

import struct
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class BootSector:
    """Représente le Boot Sector FAT16"""
    bytes_per_sector: int
    sectors_per_cluster: int
    reserved_sectors: int
    num_fats: int
    root_entries: int
    total_sectors_16: int
    media_descriptor: int
    sectors_per_fat: int
    sectors_per_track: int
    num_heads: int
    hidden_sectors: int
    total_sectors_32: int
    drive_number: int
    volume_id: int
    volume_label: str
    fs_type: str

    @property
    def total_sectors(self) -> int:
        """Retourne le nombre total de secteurs"""
        return self.total_sectors_32 if self.total_sectors_32 > 0 else self.total_sectors_16

    @property
    def root_dir_sectors(self) -> int:
        """Calcule le nombre de secteurs du répertoire racine"""
        return ((self.root_entries * 32) + (self.bytes_per_sector - 1)) // self.bytes_per_sector

    @property
    def first_data_sector(self) -> int:
        """Calcule le premier secteur de la zone de données"""
        return self.reserved_sectors + (self.num_fats * self.sectors_per_fat) + self.root_dir_sectors

    @property
    def data_sectors(self) -> int:
        """Calcule le nombre de secteurs de données"""
        return self.total_sectors - self.first_data_sector

    @property
    def total_clusters(self) -> int:
        """Calcule le nombre total de clusters"""
        return self.data_sectors // self.sectors_per_cluster


@dataclass
class MBRPartition:
    """Représente une entrée de partition dans le MBR"""
    status: int
    start_chs: Tuple[int, int, int]
    partition_type: int
    end_chs: Tuple[int, int, int]
    start_lba: int
    total_sectors: int

    def is_fat16(self) -> bool:
        """Vérifie si c'est une partition FAT16"""
        # Types FAT16: 0x04, 0x06, 0x0E
        return self.partition_type in [0x04, 0x06, 0x0E]

    def is_fat32(self) -> bool:
        """Vérifie si c'est une partition FAT32"""
        # Types FAT32: 0x0B, 0x0C
        return self.partition_type in [0x0B, 0x0C]

    def is_fat12(self) -> bool:
        """Vérifie si c'est une partition FAT12"""
        # Type FAT12: 0x01
        return self.partition_type == 0x01


class FAT16Parser:
    """Parser pour images disque FAT12/16/32"""

    def __init__(self, image_path: str):
        self.image_path = image_path
        self.file_handle: Optional[object] = None
        self.boot_sector: Optional[BootSector] = None
        self.partitions: List[MBRPartition] = []
        self.current_partition_offset: int = 0
        self.fat_type: Optional[str] = None  # 'FAT12', 'FAT16', ou 'FAT32'

    def open(self):
        """Ouvre le fichier image"""
        self.file_handle = open(self.image_path, 'rb')

    def close(self):
        """Ferme le fichier image"""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read_mbr(self) -> List[MBRPartition]:
        """Lit le MBR et retourne la liste des partitions"""
        if not self.file_handle:
            raise RuntimeError("Fichier image non ouvert")

        self.file_handle.seek(0)
        mbr_data = self.file_handle.read(512)

        # Vérifier la signature MBR (0x55AA à l'offset 510)
        signature = struct.unpack('<H', mbr_data[510:512])[0]
        if signature != 0xAA55:
            raise ValueError("Signature MBR invalide")

        # Lire les 4 entrées de partition (offset 446, 16 octets chacune)
        partitions = []
        for i in range(4):
            offset = 446 + (i * 16)
            entry = mbr_data[offset:offset + 16]

            status = entry[0]
            start_chs = (entry[1], entry[2], entry[3])
            partition_type = entry[4]
            end_chs = (entry[5], entry[6], entry[7])
            start_lba = struct.unpack('<I', entry[8:12])[0]
            total_sectors = struct.unpack('<I', entry[12:16])[0]

            # Ignorer les partitions vides
            if partition_type != 0:
                partition = MBRPartition(
                    status=status,
                    start_chs=start_chs,
                    partition_type=partition_type,
                    end_chs=end_chs,
                    start_lba=start_lba,
                    total_sectors=total_sectors
                )
                partitions.append(partition)

        self.partitions = partitions
        return partitions

    def read_boot_sector(self, partition_offset: int = 0) -> BootSector:
        """Lit le boot sector d'une partition FAT16"""
        if not self.file_handle:
            raise RuntimeError("Fichier image non ouvert")

        self.current_partition_offset = partition_offset
        self.file_handle.seek(partition_offset)
        boot_data = self.file_handle.read(512)

        # Vérifier le jump boot (0xEB ou 0xE9 au premier octet)
        if boot_data[0] not in [0xEB, 0xE9]:
            raise ValueError("Jump boot invalide - ce n'est peut-être pas un boot sector FAT")

        # Parser le BPB (BIOS Parameter Block)
        bytes_per_sector = struct.unpack('<H', boot_data[11:13])[0]
        sectors_per_cluster = boot_data[13]
        reserved_sectors = struct.unpack('<H', boot_data[14:16])[0]
        num_fats = boot_data[16]
        root_entries = struct.unpack('<H', boot_data[17:19])[0]
        total_sectors_16 = struct.unpack('<H', boot_data[19:21])[0]
        media_descriptor = boot_data[21]
        sectors_per_fat = struct.unpack('<H', boot_data[22:24])[0]
        sectors_per_track = struct.unpack('<H', boot_data[24:26])[0]
        num_heads = struct.unpack('<H', boot_data[26:28])[0]
        hidden_sectors = struct.unpack('<I', boot_data[28:32])[0]
        total_sectors_32 = struct.unpack('<I', boot_data[32:36])[0]

        # EBPB (Extended BIOS Parameter Block) pour FAT16
        drive_number = boot_data[36]
        volume_id = struct.unpack('<I', boot_data[39:43])[0]
        volume_label = boot_data[43:54].decode('ascii', errors='ignore').strip()
        fs_type = boot_data[54:62].decode('ascii', errors='ignore').strip()

        self.boot_sector = BootSector(
            bytes_per_sector=bytes_per_sector,
            sectors_per_cluster=sectors_per_cluster,
            reserved_sectors=reserved_sectors,
            num_fats=num_fats,
            root_entries=root_entries,
            total_sectors_16=total_sectors_16,
            media_descriptor=media_descriptor,
            sectors_per_fat=sectors_per_fat,
            sectors_per_track=sectors_per_track,
            num_heads=num_heads,
            hidden_sectors=hidden_sectors,
            total_sectors_32=total_sectors_32,
            drive_number=drive_number,
            volume_id=volume_id,
            volume_label=volume_label,
            fs_type=fs_type
        )

        # Détecter automatiquement le type FAT
        self._detect_fat_type()

        return self.boot_sector

    def _detect_fat_type(self):
        """Détecte le type FAT (FAT12, FAT16 ou FAT32) basé sur le nombre de clusters"""
        if not self.boot_sector:
            return

        total_clusters = self.boot_sector.total_clusters

        # Selon la spécification Microsoft:
        # FAT12: < 4085 clusters
        # FAT16: 4085 - 65524 clusters
        # FAT32: >= 65525 clusters
        if total_clusters < 4085:
            self.fat_type = 'FAT12'
        elif total_clusters < 65525:
            self.fat_type = 'FAT16'
        else:
            self.fat_type = 'FAT32'

    def read_sector(self, sector_number: int) -> bytes:
        """Lit un secteur spécifique"""
        if not self.file_handle or not self.boot_sector:
            raise RuntimeError("Fichier image ou boot sector non initialisé")

        offset = self.current_partition_offset + (sector_number * self.boot_sector.bytes_per_sector)
        self.file_handle.seek(offset)
        return self.file_handle.read(self.boot_sector.bytes_per_sector)

    def read_cluster(self, cluster_number: int) -> bytes:
        """Lit un cluster spécifique (cluster 2 = premier cluster de données)"""
        if not self.boot_sector:
            raise RuntimeError("Boot sector non initialisé")

        if cluster_number < 2:
            raise ValueError("Les clusters de données commencent à 2")

        # Calculer le secteur correspondant
        first_sector = self.boot_sector.first_data_sector + ((cluster_number - 2) * self.boot_sector.sectors_per_cluster)

        # Lire tous les secteurs du cluster
        data = b''
        for i in range(self.boot_sector.sectors_per_cluster):
            data += self.read_sector(first_sector + i)

        return data

    def read_fat(self, fat_number: int = 1) -> bytes:
        """Lit une table FAT complète (1 ou 2)"""
        if not self.boot_sector:
            raise RuntimeError("Boot sector non initialisé")

        if fat_number not in [1, 2]:
            raise ValueError("fat_number doit être 1 ou 2")

        # Calculer le secteur de début de la FAT
        if fat_number == 1:
            first_sector = self.boot_sector.reserved_sectors
        else:
            first_sector = self.boot_sector.reserved_sectors + self.boot_sector.sectors_per_fat

        # Lire tous les secteurs de la FAT
        fat_data = b''
        for i in range(self.boot_sector.sectors_per_fat):
            fat_data += self.read_sector(first_sector + i)

        return fat_data

    def read_root_directory(self) -> bytes:
        """Lit le root directory complet"""
        if not self.boot_sector:
            raise RuntimeError("Boot sector non initialisé")

        # Le root directory commence après les FATs
        first_sector = self.boot_sector.reserved_sectors + (self.boot_sector.num_fats * self.boot_sector.sectors_per_fat)

        # Lire tous les secteurs du root directory
        root_data = b''
        for i in range(self.boot_sector.root_dir_sectors):
            root_data += self.read_sector(first_sector + i)

        return root_data

    def _get_fat12_entry(self, fat_data: bytes, cluster: int) -> int:
        """Retourne la valeur d'une entrée FAT12 pour un cluster donné"""
        # FAT12: 1.5 octets par entrée (12 bits)
        # Les entrées sont empaquetées: offset = (cluster * 3) / 2
        offset = (cluster * 3) // 2

        if offset + 2 > len(fat_data):
            return 0

        # Lire 2 octets
        two_bytes = struct.unpack('<H', fat_data[offset:offset + 2])[0]

        # Extraire les 12 bits corrects selon si le cluster est pair ou impair
        if cluster % 2 == 0:
            # Cluster pair: bits 0-11
            return two_bytes & 0x0FFF
        else:
            # Cluster impair: bits 4-15
            return (two_bytes >> 4) & 0x0FFF

    def _get_fat16_entry(self, fat_data: bytes, cluster: int) -> int:
        """Retourne la valeur d'une entrée FAT16 pour un cluster donné"""
        # FAT16: 2 octets par entrée (16 bits)
        offset = cluster * 2
        if offset + 2 > len(fat_data):
            return 0
        return struct.unpack('<H', fat_data[offset:offset + 2])[0]

    def _get_fat32_entry(self, fat_data: bytes, cluster: int) -> int:
        """Retourne la valeur d'une entrée FAT32 pour un cluster donné"""
        # FAT32: 4 octets par entrée (32 bits, mais seuls les 28 bits inférieurs sont utilisés)
        offset = cluster * 4
        if offset + 4 > len(fat_data):
            return 0
        value = struct.unpack('<I', fat_data[offset:offset + 4])[0]
        # Masquer les 4 bits de poids fort (réservés)
        return value & 0x0FFFFFFF

    def get_fat_entry(self, fat_data: bytes, cluster: int) -> int:
        """Retourne la valeur d'une entrée FAT pour un cluster donné (détecte automatiquement le type)"""
        if self.fat_type == 'FAT12':
            return self._get_fat12_entry(fat_data, cluster)
        elif self.fat_type == 'FAT16':
            return self._get_fat16_entry(fat_data, cluster)
        elif self.fat_type == 'FAT32':
            return self._get_fat32_entry(fat_data, cluster)
        else:
            # Par défaut, utiliser FAT16
            return self._get_fat16_entry(fat_data, cluster)

    def _is_eof(self, value: int) -> bool:
        """Vérifie si une valeur FAT représente EOF (End Of File)"""
        if self.fat_type == 'FAT12':
            return value >= 0xFF8
        elif self.fat_type == 'FAT16':
            return value >= 0xFFF8
        elif self.fat_type == 'FAT32':
            return value >= 0x0FFFFFF8
        return False

    def _is_bad_cluster(self, value: int) -> bool:
        """Vérifie si une valeur FAT représente un cluster défectueux"""
        if self.fat_type == 'FAT12':
            return value == 0xFF7
        elif self.fat_type == 'FAT16':
            return value == 0xFFF7
        elif self.fat_type == 'FAT32':
            return value == 0x0FFFFFF7
        return False

    def parse_fat_chain(self, fat_data: bytes, start_cluster: int) -> List[int]:
        """Parse une chaîne FAT à partir d'un cluster de départ (supporte FAT12/16/32)"""
        chain = [start_cluster]
        current = start_cluster

        while True:
            next_cluster = self.get_fat_entry(fat_data, current)

            # Valeurs spéciales
            if self._is_eof(next_cluster):  # Fin de chaîne (EOF)
                break
            elif next_cluster == 0x0000:  # Cluster libre
                break
            elif self._is_bad_cluster(next_cluster):  # Cluster défectueux
                break
            elif next_cluster < 2:  # Réservé
                break

            chain.append(next_cluster)
            current = next_cluster

            # Protection contre les boucles infinies
            if len(chain) > 10000:
                raise ValueError("Chaîne FAT trop longue ou corrompue")

        return chain

    def get_info_dict(self) -> Dict:
        """Retourne un dictionnaire avec toutes les informations de la partition"""
        if not self.boot_sector:
            return {}

        bs = self.boot_sector
        return {
            'bytes_per_sector': bs.bytes_per_sector,
            'sectors_per_cluster': bs.sectors_per_cluster,
            'reserved_sectors': bs.reserved_sectors,
            'num_fats': bs.num_fats,
            'root_entries': bs.root_entries,
            'total_sectors': bs.total_sectors,
            'sectors_per_fat': bs.sectors_per_fat,
            'root_dir_sectors': bs.root_dir_sectors,
            'first_data_sector': bs.first_data_sector,
            'data_sectors': bs.data_sectors,
            'total_clusters': bs.total_clusters,
            'volume_label': bs.volume_label,
            'fs_type': bs.fs_type,
            'volume_id': f"0x{bs.volume_id:08X}",
            'detected_fat_type': self.fat_type or 'Unknown',  # Type détecté automatiquement
        }

    def write_bytes_at_offset(self, offset: int, data: bytes):
        """
        Écrit des octets à un offset absolu dans le fichier image

        Args:
            offset: Offset absolu dans le fichier (en octets)
            data: Données à écrire

        Raises:
            RuntimeError: Si le fichier n'est pas ouvert
            ValueError: Si l'offset est invalide
        """
        if not self.file_handle:
            raise RuntimeError("Fichier image non ouvert")

        # Vérifier que le fichier est ouvert en mode lecture/écriture
        if self.file_handle.mode == 'rb':
            raise RuntimeError("Le fichier doit être ouvert en mode lecture/écriture (r+b)")

        if offset < 0:
            raise ValueError("L'offset ne peut pas être négatif")

        # Se positionner à l'offset
        print(f"[FAT16Parser] Seeking to offset 0x{offset:X}")
        self.file_handle.seek(offset)

        current_pos = self.file_handle.tell()
        print(f"[FAT16Parser] Current position: 0x{current_pos:X}")

        # Écrire les données
        print(f"[FAT16Parser] Writing {len(data)} bytes: {data.hex()}")
        bytes_written = self.file_handle.write(data)
        print(f"[FAT16Parser] Bytes written: {bytes_written}")

        # Forcer l'écriture sur le disque
        self.file_handle.flush()
        print(f"[FAT16Parser] Flush complete")

        return bytes_written

    def reopen_writable(self):
        """
        Ferme et rouvre le fichier en mode lecture/écriture
        ATTENTION: Cette opération permet de modifier le fichier image
        """
        if not self.file_handle:
            raise RuntimeError("Aucun fichier n'est ouvert")

        # Sauvegarder le chemin
        path = self.image_path
        print(f"[FAT16Parser] Reopening file: {path}")

        # Fermer le fichier actuel
        self.close()
        print(f"[FAT16Parser] File closed")

        # Rouvrir en mode lecture/écriture
        self.file_handle = open(path, 'r+b')
        print(f"[FAT16Parser] File reopened in mode: {self.file_handle.mode}")

        return True
