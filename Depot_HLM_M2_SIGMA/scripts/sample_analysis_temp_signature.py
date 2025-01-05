# Import des librairies
import geopandas as gpd
import rasterio
import matplotlib.pyplot as plt
import numpy as np
from rasterio.sample import sample_gen

# Définition des paramètres en entrée
# échantillons
my_folder_sample = '/home/onyxia/work/results/data/sample'
sample_file_name = os.path.join(my_folder_sample, 'Sample_BD_foret_T31TCJ.shp')
# NDVI
my_folder_ndvi = '/home/onyxia/work/results/data/img_pretraitees'
ndvi_file_name = os.path.join(my_folder_ndvi, 'Serie_temp_S2_ndvi.tif')

# Chargement des données
gdf_echantillons = gpd.read_file(sample_file_name)  # Données vecteur
ndvi_loaded = rasterio.open(ndvi_file_name)  # Données NDVI raster

# Sélection des codes correspondant aux classes en gras dans la colonne classif pixel de la figure 2
classes_en_gras = ['12', '13', '14', '23', '24', '25']
# Filtrage des classes dans le champ 'Code'
gdf_classif_pixel_gras = gdf_echantillons[gdf_echantillons["Code"].isin(classes_en_gras)]
# print(gdf_classif_pixel_gras)


# Extraction des valeurs NDVI pour chaque point dans les classes filtrées
points_classes = [(x, y) for x, y in zip(gdf_classif_pixel_gras.geometry.x, gdf_classif_pixel_gras.geometry.y)]
ndvi_values = list(ndvi_loaded.sample(points_classes))

# Organisation des données par classe
classes = gdf_classif_pixel_gras['Code'].unique()
dict_X = {class_code: [] for class_code in classes}

for value, class_code in zip(ndvi_values, gdf_classif_pixel_gras['Code']):
    dict_X[class_code].append(value)

# Conversion en tableaux NumPy pour simplifier les calculs
dict_X = {key: np.array(values) for key, values in dict_X.items()}

# Création du graphique
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(7, 5))
colors = ['tan', 'palegreen', 'limegreen', 'darkgreen', 'cornflowerblue', 'seagreen']  # Ajustez les couleurs si nécessaire
labels = [f"Classe {cls}" for cls in classes]

# Tracé des courbes moyennes et des écarts-types
for X, color, label in zip(dict_X.values(), colors, labels):
    means = X.mean(axis=0)
    stds = X.std(axis=0)
    ax.plot(means, color=color, label=label)
    ax.fill_between(range(means.shape[0]), means + stds, means - stds, facecolor=color, alpha=0.3)

# Personnalisation du graphique
ax.set_xticks(range(means.shape[0]))
bands_name = ['NDVI-' + str(i + 1) for i in range(means.shape[0])]  # Exemple : NDVI-1, NDVI-2, etc.
ax.set_xticklabels(bands_name, rotation=45)
ax.set_xlabel("Bande NDVI")
ax.set_ylabel("Valeurs NDVI")
ax.legend()
ax.set_title("Signatures spectrales moyennes des classes avec écart-types")
plt.tight_layout()

# Affichage du graphique
plt.show()