"""
Parser for FAT16 disk images (.raw)
Reads and analyzes the structure of a FAT16 partition
"""

import struct
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class BootSector:
    """Represents the FAT16 Boot Sector"""
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
        """Returns the total number of sectors"""
        return self.total_sectors_32 if self.total_sectors_32 > 0 else self.total_sectors_16

    @property
    def root_dir_sectors(self) -> int:
        """Calculates the number of root directory sectors"""
        return ((self.root_entries * 32) + (self.bytes_per_sector - 1)) // self.bytes_per_sector

    @property
    def first_data_sector(self) -> int:
        """Calculates the first sector of the data area"""
        return self.reserved_sectors + (self.num_fats * self.sectors_per_fat) + self.root_dir_sectors

    @property
    def data_sectors(self) -> int:
        """Calculates the number of data sectors"""
        return self.total_sectors - self.first_data_sector

    @property
    def total_clusters(self) -> int:
        """Calculates the total number of clusters"""
        return self.data_sectors // self.sectors_per_cluster


@dataclass
class MBRPartition:
    """Represents a partition entry in the MBR"""
    status: int
    start_chs: Tuple[int, int, int]
    partition_type: int
    end_chs: Tuple[int, int, int]
    start_lba: int
    total_sectors: int

    def is_fat16(self) -> bool:
        """Checks if this is a FAT16 partition"""
        # FAT16 types: 0x04, 0x06, 0x0E
        return self.partition_type in [0x04, 0x06, 0x0E]

    def is_fat32(self) -> bool:
        """Checks if this is a FAT32 partition"""
        # FAT32 types: 0x0B, 0x0C
        return self.partition_type in [0x0B, 0x0C]

    def is_fat12(self) -> bool:
        """Checks if this is a FAT12 partition"""
        # FAT12 type: 0x01
        return self.partition_type == 0x01


class FAT16Parser:
    """Parser for FAT12/16/32 disk images"""

    def __init__(self, image_path: str):
        self.image_path = image_path
        self.file_handle: Optional[object] = None
        self.boot_sector: Optional[BootSector] = None
        self.partitions: List[MBRPartition] = []
        self.current_partition_offset: int = 0
        self.fat_type: Optional[str] = None  # 'FAT12', 'FAT16', or 'FAT32'

    def open(self):
        """Opens the image file"""
        self.file_handle = open(self.image_path, 'rb')

    def close(self):
        """Closes the image file"""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read_mbr(self) -> List[MBRPartition]:
        """Reads the MBR and returns the list of partitions"""
        if not self.file_handle:
            raise RuntimeError("Image file not opened")

        self.file_handle.seek(0)
        mbr_data = self.file_handle.read(512)

        # Check MBR signature (0x55AA at offset 510)
        signature = struct.unpack('<H', mbr_data[510:512])[0]
        if signature != 0xAA55:
            raise ValueError("Invalid MBR signature")

        # Read the 4 partition entries (offset 446, 16 bytes each)
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

            # Ignore empty partitions
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
        """Reads the boot sector of a FAT16 partition"""
        if not self.file_handle:
            raise RuntimeError("Image file not opened")

        self.current_partition_offset = partition_offset
        self.file_handle.seek(partition_offset)
        boot_data = self.file_handle.read(512)

        # Check jump boot (0xEB or 0xE9 in first byte)
        if boot_data[0] not in [0xEB, 0xE9]:
            raise ValueError("Invalid jump boot - this may not be a FAT boot sector")

        # Parse the BPB (BIOS Parameter Block)
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

        # EBPB (Extended BIOS Parameter Block) for FAT16
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

        # Automatically detect FAT type
        self._detect_fat_type()

        return self.boot_sector

    def _detect_fat_type(self):
        """Detects the FAT type (FAT12, FAT16, or FAT32) based on cluster count"""
        if not self.boot_sector:
            return

        total_clusters = self.boot_sector.total_clusters

        # According to Microsoft specification:
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
        """Reads a specific sector"""
        if not self.file_handle or not self.boot_sector:
            raise RuntimeError("Image file or boot sector not initialized")

        offset = self.current_partition_offset + (sector_number * self.boot_sector.bytes_per_sector)
        self.file_handle.seek(offset)
        return self.file_handle.read(self.boot_sector.bytes_per_sector)

    def read_cluster(self, cluster_number: int) -> bytes:
        """Reads a specific cluster (cluster 2 = first data cluster)"""
        if not self.boot_sector:
            raise RuntimeError("Boot sector not initialized")

        if cluster_number < 2:
            raise ValueError("Data clusters start at 2")

        # Calculate the corresponding sector
        first_sector = self.boot_sector.first_data_sector + ((cluster_number - 2) * self.boot_sector.sectors_per_cluster)

        # Read all sectors in the cluster
        data = b''
        for i in range(self.boot_sector.sectors_per_cluster):
            data += self.read_sector(first_sector + i)

        return data

    def read_fat(self, fat_number: int = 1) -> bytes:
        """Reads a complete FAT table (1 or 2)"""
        if not self.boot_sector:
            raise RuntimeError("Boot sector not initialized")

        if fat_number not in [1, 2]:
            raise ValueError("fat_number must be 1 or 2")

        # Calculate the starting sector of the FAT
        if fat_number == 1:
            first_sector = self.boot_sector.reserved_sectors
        else:
            first_sector = self.boot_sector.reserved_sectors + self.boot_sector.sectors_per_fat

        # Read all sectors of the FAT
        fat_data = b''
        for i in range(self.boot_sector.sectors_per_fat):
            fat_data += self.read_sector(first_sector + i)

        return fat_data

    def read_root_directory(self) -> bytes:
        """Reads the complete root directory"""
        if not self.boot_sector:
            raise RuntimeError("Boot sector not initialized")

        # The root directory starts after the FATs
        first_sector = self.boot_sector.reserved_sectors + (self.boot_sector.num_fats * self.boot_sector.sectors_per_fat)

        # Read all sectors of the root directory
        root_data = b''
        for i in range(self.boot_sector.root_dir_sectors):
            root_data += self.read_sector(first_sector + i)

        return root_data

    def _get_fat12_entry(self, fat_data: bytes, cluster: int) -> int:
        """Returns the value of a FAT12 entry for a given cluster"""
        # FAT12: 1.5 bytes per entry (12 bits)
        # Entries are packed: offset = (cluster * 3) / 2
        offset = (cluster * 3) // 2

        if offset + 2 > len(fat_data):
            return 0

        # Read 2 bytes
        two_bytes = struct.unpack('<H', fat_data[offset:offset + 2])[0]

        # Extract the correct 12 bits depending on whether cluster is even or odd
        if cluster % 2 == 0:
            # Even cluster: bits 0-11
            return two_bytes & 0x0FFF
        else:
            # Odd cluster: bits 4-15
            return (two_bytes >> 4) & 0x0FFF

    def _get_fat16_entry(self, fat_data: bytes, cluster: int) -> int:
        """Returns the value of a FAT16 entry for a given cluster"""
        # FAT16: 2 bytes per entry (16 bits)
        offset = cluster * 2
        if offset + 2 > len(fat_data):
            return 0
        return struct.unpack('<H', fat_data[offset:offset + 2])[0]

    def _get_fat32_entry(self, fat_data: bytes, cluster: int) -> int:
        """Returns the value of a FAT32 entry for a given cluster"""
        # FAT32: 4 bytes per entry (32 bits, but only the lower 28 bits are used)
        offset = cluster * 4
        if offset + 4 > len(fat_data):
            return 0
        value = struct.unpack('<I', fat_data[offset:offset + 4])[0]
        # Mask the upper 4 bits (reserved)
        return value & 0x0FFFFFFF

    def get_fat_entry(self, fat_data: bytes, cluster: int) -> int:
        """Returns the value of a FAT entry for a given cluster (automatically detects type)"""
        if self.fat_type == 'FAT12':
            return self._get_fat12_entry(fat_data, cluster)
        elif self.fat_type == 'FAT16':
            return self._get_fat16_entry(fat_data, cluster)
        elif self.fat_type == 'FAT32':
            return self._get_fat32_entry(fat_data, cluster)
        else:
            # By default, use FAT16
            return self._get_fat16_entry(fat_data, cluster)

    def _is_eof(self, value: int) -> bool:
        """Checks if a FAT value represents EOF (End Of File)"""
        if self.fat_type == 'FAT12':
            return value >= 0xFF8
        elif self.fat_type == 'FAT16':
            return value >= 0xFFF8
        elif self.fat_type == 'FAT32':
            return value >= 0x0FFFFFF8
        return False

    def _is_bad_cluster(self, value: int) -> bool:
        """Checks if a FAT value represents a bad cluster"""
        if self.fat_type == 'FAT12':
            return value == 0xFF7
        elif self.fat_type == 'FAT16':
            return value == 0xFFF7
        elif self.fat_type == 'FAT32':
            return value == 0x0FFFFFF7
        return False

    def find_chain_start(self, fat_data: bytes, cluster: int) -> int:
        """
        Finds the start of a FAT chain by working backwards from a given cluster.

        Args:
            fat_data: The FAT data
            cluster: A cluster in the chain

        Returns:
            The first cluster of the chain
        """
        if cluster < 2:
            return cluster

        # Build a reverse map: cluster -> clusters that point to it
        total_clusters = self.boot_sector.total_clusters
        visited = set()
        current = cluster

        # Work backwards until we find a cluster that no one points to
        max_iterations = 10000  # Protection against infinite loops
        iterations = 0

        while iterations < max_iterations:
            visited.add(current)
            found_predecessor = False

            # Search through all clusters to find one that points to current
            for check_cluster in range(2, total_clusters + 2):
                if check_cluster in visited:
                    continue  # Skip clusters we've already checked

                next_cluster = self.get_fat_entry(fat_data, check_cluster)

                if next_cluster == current:
                    # Found a cluster that points to current
                    current = check_cluster
                    found_predecessor = True
                    break

            if not found_predecessor:
                # No cluster points to current, so current is the start
                return current

            iterations += 1

        # If we hit max iterations, return the current cluster
        # (might be in a loop, but at least return something)
        return current

    def parse_fat_chain(self, fat_data: bytes, start_cluster: int) -> List[int]:
        """Parses a FAT chain from a starting cluster (supports FAT12/16/32)"""
        chain = [start_cluster]
        current = start_cluster

        while True:
            next_cluster = self.get_fat_entry(fat_data, current)

            # Special values
            if self._is_eof(next_cluster):  # End of chain (EOF)
                break
            elif next_cluster == 0x0000:  # Free cluster
                break
            elif self._is_bad_cluster(next_cluster):  # Bad cluster
                break
            elif next_cluster < 2:  # Reserved
                break

            chain.append(next_cluster)
            current = next_cluster

            # Protection against infinite loops
            if len(chain) > 10000:
                raise ValueError("FAT chain too long or corrupted")

        return chain

    def get_info_dict(self) -> Dict:
        """Returns a dictionary with all partition information"""
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
            'detected_fat_type': self.fat_type or 'Unknown',  # Automatically detected type
        }

    def write_bytes_at_offset(self, offset: int, data: bytes):
        """
        Writes bytes at an absolute offset in the image file

        Args:
            offset: Absolute offset in the file (in bytes)
            data: Data to write

        Raises:
            RuntimeError: If the file is not opened
            ValueError: If the offset is invalid
        """
        if not self.file_handle:
            raise RuntimeError("Image file not opened")

        # Check that the file is opened in read/write mode
        if self.file_handle.mode == 'rb':
            raise RuntimeError("File must be opened in read/write mode (r+b)")

        if offset < 0:
            raise ValueError("Offset cannot be negative")

        # Position to the offset
        print(f"[FAT16Parser] Seeking to offset 0x{offset:X}")
        self.file_handle.seek(offset)

        current_pos = self.file_handle.tell()
        print(f"[FAT16Parser] Current position: 0x{current_pos:X}")

        # Write the data
        print(f"[FAT16Parser] Writing {len(data)} bytes: {data.hex()}")
        bytes_written = self.file_handle.write(data)
        print(f"[FAT16Parser] Bytes written: {bytes_written}")

        # Force write to disk
        self.file_handle.flush()
        print(f"[FAT16Parser] Flush complete")

        return bytes_written

    def reopen_writable(self):
        """
        Closes and reopens the file in read/write mode
        WARNING: This operation allows modifying the image file
        """
        if not self.file_handle:
            raise RuntimeError("No file is opened")

        # Save the path
        path = self.image_path
        print(f"[FAT16Parser] Reopening file: {path}")

        # Close the current file
        self.close()
        print(f"[FAT16Parser] File closed")

        # Reopen in read/write mode
        self.file_handle = open(path, 'r+b')
        print(f"[FAT16Parser] File reopened in mode: {self.file_handle.mode}")

        return True
