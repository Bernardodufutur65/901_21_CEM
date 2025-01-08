import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import Point

# Classes de peuplement purs (rouges) et en mélange (bleues)
classes_rouges = ['11', '12', '13', '14', '23', '24', '25']
classes_bleues = ['15', '26', '28', '29']

# Chemins des fichiers
ndvi_file = "/home/onyxia/work/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif"
sample_file = "/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp"

# Charger le raster NDVI
with rasterio.open(ndvi_file) as src:
    ndvi_data = src.read(1)  # Lire la première bande
    transform = src.transform  # Transformation géographique

# Charger les polygones
sample = gpd.read_file(sample_file)

# Fonction permettant de calculer le centroïde d'une liste de coordonnées données
def calculate_centroid(coords):
    coords = np.array(coords)
    cx = np.sum(coords[:, 0]) / len(coords)
    cy = np.sum(coords[:, 1]) / len(coords)
    return np.array([cx, cy])

# Fonction permettant de calculer la distance moyenne au centroïde
def calculate_average_distance(coords, centroid):
    distances = []
    for coord in coords:
        dx = coord[0] - centroid[0]
        dy = coord[1] - centroid[1]
        distance = np.sqrt(dx**2 + dy**2)
        distances.append(distance)
    return np.mean(distances)

# Liste des distances par classe
distances_par_classe = {}

########## --- Analyse à l'échelle de l'image entière --- ##########
# Parcourir les classes uniques dans le raster NDVI
unique_classes = np.unique(ndvi_data[~np.isnan(ndvi_data)])  # Identifier les classes uniques

for cls in unique_classes:
    cls = str(int(cls))  # Convertir en chaîne pour correspondre aux classes rouges/bleues
    cls_indices = np.column_stack(np.where(ndvi_data == int(cls)))

    # Convertir les indices des pixels en coordonnées géographiques
    cls_coords = [rasterio.transform.xy(transform, row, col) for row, col in cls_indices]

    # Calculer le centroïde et la distance moyenne au centroïde
    centroid = calculate_centroid(cls_coords)
    avg_distance = calculate_average_distance(cls_coords, centroid)
    distances_par_classe[cls] = avg_distance

# Générer un diagramme en bâton
plt.figure(figsize=(10, 6))
plt.bar(distances_par_classe.keys(), distances_par_classe.values(), color='skyblue')
plt.title("Distance moyenne au centroïde par classe")
plt.xlabel("Classes")
plt.ylabel("Distance moyenne")
plt.savefig("/home/onyxia/work/results/figure/diag_baton_dist_centroide_classe.png")
plt.close()

########## --- Analyse à l'échelle de chaque polygone --- ##########
distances_polygones_rouges = []
distances_polygones_bleues = []

for _, row in sample.iterrows():
    polygon = row['geometry']
    class_label = str(row['Code'])  # Vérifiez le nom exact de la colonne dans le shapefile

    # Extraire les pixels du raster à l'intérieur du polygone
    mask = geometry_mask([polygon], transform=transform, invert=True, out_shape=ndvi_data.shape)
    masked_ndvi = ndvi_data[mask]

    if len(masked_ndvi) > 0:
        # Coordonner les pixels à l'intérieur du polygone
        poly_indices = np.column_stack(np.where(mask))
        poly_coords = [rasterio.transform.xy(transform, row, col) for row, col in poly_indices]

        # Calculer le centroïde et la distance moyenne
        centroid = calculate_centroid(poly_coords)
        avg_distance = calculate_average_distance(poly_coords, centroid)

        if class_label in classes_rouges:
            distances_polygones_rouges.append(avg_distance)
        elif class_label in classes_bleues:
            distances_polygones_bleues.append(avg_distance)

# Générer un "violin plot" pour les distances par classe
data = [distances_polygones_rouges, distances_polygones_bleues]

fig, ax = plt.subplots(figsize=(8, 6))
ax.violinplot(data, showmeans=True, showmedians=True)

# Ajout des étiquettes
ax.set_xticks([1, 2])
ax.set_xticklabels(["Rouges", "Bleues"])
ax.set_title("Distribution des distances moyennes par polygone et par classe")
ax.set_ylabel("Distance moyenne au centroïde")

# Sauvegarde et affichage
plt.savefig("results/figure/violin_plot_dist_centroide_by_poly_by_class.png")
plt.close()
