import os

def main():
    octets_per_sector = int(input("Nombre d'octets par secteur : "))
    sectors_in_cluster_count = int(input("Nombre de secteurs par cluster : "))
    reserved_sectors_count = int(input("Nombre de secteurs réservés (reserved sectors) : "))
    fat_zones_count = int(input("Nombre de zones FAT : "))
    sectors_per_fat_count = int(input("Nombre de secteurs par zone FAT : "))
    root_directory_entries_count = int(input("Nombre d'entrées dans le root directory : "))

    # Division entière pour obtenir le nombre de secteurs du root directory
    root_directory_sectors = (root_directory_entries_count * 32) // octets_per_sector
    # Calcul du nombre de secteurs alloués à la FAT
    fat_allocated_sectors = fat_zones_count * sectors_per_fat_count

    # Calcul de la position du "Cluster 2" (1er cluster où on trouve des Data), en secteurs
    first_data_sector = reserved_sectors_count + fat_allocated_sectors + root_directory_sectors

    # On peut ensuite calculer l'offset du premier cluster de la zone Data, soit le cluster 2
    data_zone_offset = int(first_data_sector * octets_per_sector)

    print(42*'-')
    print(f"1er secteur de Data : {first_data_sector}")
    print(f"Offset de la zone Data : {data_zone_offset}")

    cluster_to_reach = int(input("N° de cluster dont vous voulez trouver l'offset : "))

    def offset(n):
        """ Calcule l'offset (in octets) pour le cluster n """
        return (first_data_sector + (n - 2) * sectors_in_cluster_count) * octets_per_sector

    cluster_offset = offset(cluster_to_reach)

    print(42*'-')
    print(f"Offset du cluster {cluster_to_reach} (décimal) : {cluster_offset}")
    print(f"Offset du cluster {cluster_to_reach} (hex) : {hex(cluster_offset)}")


if __name__ == "__main__":
    main()