from FATPartition import FATPartition


def main():
    """
    Script standalone qui permet de calculer l'offset du first_data_sector (cluster FAT 2)
    et l'offset d'un cluster en particulier.
    """
    print("CALCULATEUR D'OFFSETS POUR PARTITION FAT")
    print("=" * 60)

    # Collecte des paramètres de la partition
    octets_per_sector = int(input("Nombre d'octets par secteur : "))
    sectors_per_cluster = int(input("Nombre de secteurs par cluster : "))
    reserved_sectors = int(input("Nombre de secteurs réservés (reserved sectors) : "))
    fat_count = int(input("Nombre de zones FAT : "))
    sectors_per_fat = int(input("Nombre de secteurs par zone FAT : "))
    root_entries = int(input("Nombre d'entrées dans le root directory : "))

    # Création de l'objet partition
    partition = FATPartition(
        octets_per_sector=octets_per_sector,
        sectors_per_cluster=sectors_per_cluster,
        reserved_sectors=reserved_sectors,
        fat_count=fat_count,
        sectors_per_fat=sectors_per_fat,
        root_entries=root_entries
    )

    # Affichage des informations
    print()
    partition.print_info()

    # Calcul d'offset pour un cluster spécifique
    print()
    cluster_number = int(input("N° de cluster dont vous voulez trouver l'offset : "))

    try:
        cluster_offset = partition.get_cluster_offset(cluster_number)
        print("-" * 60)
        print(f"Offset du cluster {cluster_number} (décimal) : {cluster_offset}")
        print(f"Offset du cluster {cluster_number} (hex)     : {hex(cluster_offset)}")
        print("=" * 60)
    except ValueError as e:
        print(f"Erreur : {e}")


if __name__ == "__main__":
    main()
