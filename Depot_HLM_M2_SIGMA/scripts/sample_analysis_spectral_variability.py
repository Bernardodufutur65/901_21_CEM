import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio
from shapely.geometry import Point
import os

# Sélection des classes rouges et bleues
classes_rouges = ['11', '12', '13', '14', '23', '24', '25']  # Classes de peuplements purs
classes_bleues = ['15', '26', '28', '29']  # Classes de peuplements en mélange

def calculate_centroid(coords):
    """
    Calculer le centroïde d'une liste de coordonnées.
    """
    coords = np.array(coords)
    return coords.mean(axis=0)

def calculate_average_distance(coords, centroid):
    """
    Calculer la distance moyenne des points à un centroïde.
    """
    distances = np.sqrt(((coords - centroid) ** 2).sum(axis=1))
    return distances.mean()

def is_point_in_polygon(x, y, polygon):
    """
    Vérifie si un point donné est à l'intérieur d'un polygone.
    """
    point = Point(x, y)
    return polygon.contains(point)

def process_image(image_path, polygons_path):
    """
    Traitement principal pour l'image et les polygones.
    Cette fonction analyse les distances au centroïde pour les classes en bleu et rouge.
    """
    # Charger le raster (NDVI)
    with rasterio.open(image_path) as src:
        ndvi_data = src.read(1)  # Lire la première bande
        transform = src.transform  # Transformation géographique

    # Charger les polygones (échantillons)
    polygons = gpd.read_file(polygons_path)

    # À l'échelle de l'image, identifier les classes uniques dans le NDVI
    unique_classes = np.unique(ndvi_data[~np.isnan(ndvi_data)])  # Identifier les classes uniques
    class_distances = {}

    # Initialiser des listes pour les distances des classes rouges et bleues
    distances_rouges = []
    distances_bleues = []

    for cls in unique_classes:
        # Trouver les indices des pixels correspondant à la classe
        cls_indices = np.column_stack(np.where(ndvi_data == cls))
        
        # Convertir les indices en coordonnées géographiques
        cls_coords = [
            rasterio.transform.xy(transform, row, col)
            for row, col in cls_indices
        ]

        centroid = calculate_centroid(cls_coords)  # Calculer le centroïde
        avg_distance = calculate_average_distance(cls_coords, centroid)  # Calculer la distance moyenne

        class_distances[cls] = avg_distance

        # Séparer les classes rouges et bleues
        if str(cls) in classes_rouges:
            distances_rouges.append(avg_distance)
        elif str(cls) in classes_bleues:
            distances_bleues.append(avg_distance)

    # Comparaison des distances moyennes des classes rouges et bleues
    print(f"Distance moyenne des classes rouges : {np.mean(distances_rouges)}")
    print(f"Distance moyenne des classes bleues : {np.mean(distances_bleues)}")
    
    # Calcul de la variabilité (écart-type)
    std_rouges = np.std(distances_rouges)
    std_bleues = np.std(distances_bleues)
    
    print(f"Variabilité (écart-type) des classes rouges : {std_rouges}")
    print(f"Variabilité (écart-type) des classes bleues : {std_bleues}")

    # Visualisation avec Matplotlib - Boxplot

    # Boxplot pour comparer les deux groupes de classes
    plt.figure(figsize=(6, 4))
    plt.boxplot([distances_rouges, distances_bleues], labels=["Rouges", "Bleues"], patch_artist=True)
    plt.title("Comparaison de la variabilité des distances moyennes\nentre classes rouges et bleues")
    plt.xlabel("Classe")
    plt.ylabel("Distance moyenne au centroïde")
    plt.savefig("results/figure/boxplot_variabilite_classes.png")
    plt.close()

    # Autre graphique : Distribution des distances
    plt.figure(figsize=(6, 4))
    plt.hist(distances_rouges, bins=15, alpha=0.7, label="Classes rouges", color='red')
    plt.hist(distances_bleues, bins=15, alpha=0.7, label="Classes bleues", color='blue')
    plt.legend()
    plt.title("Distribution des distances moyennes au centroïde")
    plt.xlabel("Distance moyenne au centroïde")
    plt.ylabel("Fréquence")
    plt.savefig("results/figure/distribution_distances_classes.png")
    plt.close()

# Exemple d'utilisation
process_image(
    "/home/onyxia/work/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif", 
    "/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp"
)
