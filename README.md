# FAT Filesystem Explorer

A visual, interactive tool for exploring and understanding FAT12/16/32 filesystems. Built as an educational project to learn about file allocation tables, disk structures, and forensic analysis.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-Educational-blue)

## 🎯 Project Goals

This project is designed to help understand:
- How FAT (File Allocation Table) filesystems work
- Disk sector organization and allocation
- Cluster chains and file fragmentation
- Hexadecimal data representation
- Forensic analysis techniques for deleted file recovery

## ✨ Features

### Partition Analysis
- **Multi-FAT Support**: Automatically detects and parses FAT12, FAT16, and FAT32 filesystems
- **Visual Partition Map**: Color-coded visualization of disk sectors
  - Boot sector, reserved area, FAT tables, root directory, and data area
  - Empty vs. full sectors differentiation (light blue vs. dark blue)
- **Boot Sector Information**: Complete parsing and display of BIOS Parameter Block (BPB)

### Data Exploration
- **Cluster Chain Viewer**: Visual representation of FAT chains
  - Navigate through linked clusters
  - Identify file fragments
  - Detect broken chains
- **Hexadecimal Editor**:
  - View raw sector/cluster data
  - Edit mode with validation (hexadecimal characters only)
  - Sector boundaries visualization with separators
  - Save modifications directly to disk image
  - Real-time modification tracking (orange highlighting)

### Search Capabilities
- **Cluster Search**: Find specific clusters by number (decimal, hex, little/big endian)
  - Displays cluster content and FAT chain
  - Highlights position in partition map
- **Text Search**: Search for strings in data area and root directory
  - Case-sensitive/insensitive options
  - Highlights matches in hex viewer
  - Navigate results with keyboard (arrow keys)
  - Search in root directory for filenames

### Forensic Features
- **Root Directory Parsing**: View and search file entries
- **Deleted File Detection**: Identify empty sectors (all zeros displayed in light blue)
- **FAT Entry Analysis**: Inspect individual FAT entries
- **Offset Calculation**: Compute precise byte positions for any cluster
- **Performance Optimized**: Scans 10,000 sectors in ~10-100ms

## 🚀 Getting Started

### Prerequisites
```bash
Python 3.8+
PyQt6
```

### Installation
```bash
# Clone or navigate to the repository
cd fat-calc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install PyQt6

# Run the application
./run_simulator.sh
# Or directly:
python fat_simulator_gui.py
```

### Usage

1. **Open a disk image**: Click "📂 Ouvrir Image .raw" or use Ctrl+O
   - Supports raw disk images (.raw, .img, .dd)
   - Automatically detects partition type and FAT variant

2. **Explore the partition**:
   - View partition information in the left panel
   - Browse the visual sector map on the right
   - Search for clusters or text content

3. **Analyze data**:
   - Click on search results to view hex data
   - Navigate through cluster chains
   - Edit hex values in edit mode (use with caution!)

4. **Search for data**:
   - **Cluster search**: Enter cluster number to view its content and chain
   - **Text search**: Find strings in data area or filenames in root directory
   - Navigate results with arrow keys or mouse clicks

## 📁 Project Structure

```
fat-calc/
├── fat_simulator_gui.py    # Main application window and UI
├── fat16_parser.py          # FAT12/16/32 parser and disk I/O
├── hex_viewer.py            # Hexadecimal viewer/editor widget
├── fat_chain_editor.py      # Visual FAT chain editor widget
├── run_simulator.sh         # Launch script
└── README.md                # This file
```

## 🎓 Learning Resources

### Understanding FAT Filesystems

**Boot Sector**: Contains BIOS Parameter Block (BPB) with filesystem parameters such as:
- Bytes per sector (usually 512)
- Sectors per cluster (power of 2)
- Number of FAT tables (usually 2 for redundancy)
- Root directory entries count
- Total sectors on partition

**FAT Tables**: File Allocation Table - maps cluster chains
- Each entry points to the next cluster in a file's chain
- Special values: FREE (0x0000), EOF (0xFFF8+), BAD (0xFFF7)

**Root Directory**: Fixed-size directory for FAT12/16 (variable for FAT32)
- Contains 32-byte directory entries
- Stores filenames in 8.3 format (8 char name + 3 char extension)

**Data Area**: Actual file content storage in clusters
- Clusters numbered starting from 2
- Minimum allocation unit

### Key Concepts

- **Cluster**: Smallest allocation unit (multiple sectors)
- **Sector**: Fixed 512-byte disk unit (sometimes 4096 on modern drives)
- **FAT Entry**: Pointer to next cluster in chain (or EOF/bad cluster marker)
- **LBA (Logical Block Addressing)**: Sector numbering scheme
- **Cluster Chain**: Linked list of clusters forming a file

### FAT Type Detection

Based on the number of clusters:
- **FAT12**: < 4,085 clusters (floppy disks, small partitions)
  - 12-bit entries, 1.5 bytes per entry
- **FAT16**: 4,085 - 65,524 clusters (small hard drives, USB sticks)
  - 16-bit entries, 2 bytes per entry
- **FAT32**: ≥ 65,525 clusters (modern USB drives, SD cards)
  - 32-bit entries (28 bits used), 4 bytes per entry

## ⚠️ Important Notes

### Safety
- **Read-only by default**: The application opens images in read-only mode
- **Edit mode warning**: Modifications in edit mode are written directly to the disk image
- **Backup recommendation**: Always work on copies of important disk images
- **Irreversible operations**: File modifications cannot be undone after saving

### Performance
- Automatically limits visualization to 10,000 sectors for performance
- Empty sector scanning takes ~10-100ms on typical images
- Hex viewer supports files of any size with efficient rendering
- Sector-by-sector scanning optimized for sequential reads

## 🔧 Advanced Features

### Hex Editor
- **Overwrite mode only**: Cannot insert or delete, only replace existing bytes
- **Validation**: Only accepts hexadecimal characters (0-9, A-F)
- **Real-time tracking**: Modified bytes highlighted in orange
- **Direct write**: Save button writes changes to disk image
- **Event filtering**: Blocks paste, cut, and invalid characters
- **Nibble editing**: Each hex digit modifies high or low nibble independently

### FAT Chain Visualization
- Add/remove clusters from chains
- Mark clusters as EOF (end of file)
- Visualize broken or corrupted chains
- Navigate to cluster content with single click
- Context menu for cluster operations

### Visual Partition Map
- **Color coding**:
  - Yellow: Boot sector
  - Red: Reserved sectors
  - Light green: FAT1
  - Dark green: FAT2
  - Orange: Root directory
  - Dark blue: Data sectors (with content)
  - Light blue: Empty data sectors (all zeros)
- **Interactive**: Click to navigate, tooltip info
- **Highlighting**: Shows current cluster and FAT entry positions

## 📝 Technical Details

### Supported Formats
- Raw disk images (sector-by-sector copies)
- MBR-partitioned images
- Direct partition images (no MBR)
- FAT12, FAT16, and FAT32 variants

### Not Supported
- GPT partitions
- Long File Names (LFN) - only 8.3 filenames shown
- NTFS, ext4, or other modern filesystems
- Compressed or encrypted volumes

### Architecture

The application follows a Model-View-Controller pattern:
- **Model**: `fat16_parser.py` (business logic, I/O)
- **View**: PyQt6 widgets (`hex_viewer.py`, `fat_chain_editor.py`)
- **Controller**: `fat_simulator_gui.py` (event handling)

### Technologies Used
- **PyQt6**: Cross-platform GUI framework
- **Python struct**: Binary data parsing
- **Qt Signals/Slots**: Event-driven architecture
- **Qt Painter**: Custom graphics rendering

## 🤝 Contributing

This is an educational project. Feel free to:
- Report bugs or suggest features
- Add new visualization modes
- Improve forensic capabilities
- Enhance performance optimizations

## 📜 License

This project is provided as-is for educational purposes.

## 🙏 Acknowledgments

Built to understand low-level filesystem structures and forensic analysis techniques. Inspired by professional forensic tools like Autopsy and FTK Imager, but designed specifically for learning and exploration.

---

**Note**: This tool is for educational purposes. Always respect data privacy and legal requirements when analyzing disk images. Only use on your own data or with explicit authorization.

**Version**: 2.0.0
**Last Updated**: 2025
**Support**: FAT12, FAT16, FAT32
