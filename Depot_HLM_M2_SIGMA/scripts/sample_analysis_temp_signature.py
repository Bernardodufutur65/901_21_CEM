# Import des librairies
import geopandas as gpd
import rasterio
import os
from rasterstats import zonal_stats
import pandas as pd
import matplotlib.pyplot as plt
import time


# Définition des paramètres
# en entrée
sample_file = '/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp'  # échantillons
ndvi_file = '/home/onyxia/work/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif'  # ndvi
# en sortie
output_folder = '/home/onyxia/work/results/figure'
output_file = os.path.join(output_folder, 'temp_mean_ndvi.png')

# Chargement des données
gdf_echantillons = gpd.read_file(sample_file)  # Données vecteur
ndvi_loaded = rasterio.open(ndvi_file)  # Données NDVI raster

# Sélection des codes correspondant aux classes en gras dans la colonne classif pixel de la figure 2
classes_en_gras = ['12', '13', '14', '23', '24', '25']
# Filtrage des classes dans le champ 'Code'
gdf_classif_pixel_gras = gdf_echantillons[gdf_echantillons["Code"].isin(classes_en_gras)]
print(gdf_classif_pixel_gras)

# Intersection des polygones avec le NDVI
# Extraction des statistiques zonales pour chaque bande NDVI
ndvi_stats = []
for i in range(1, ndvi_loaded.count + 1):  # Pour chaque bande temporelle
    stats = zonal_stats(
        gdf_classif_pixel_gras,  # Polygones des échantillons
        ndvi_loaded.read(i),     # Bande NDVI
        stats=['mean', 'std'],   # Moyenne et écart-type
        affine=ndvi_loaded.transform,
        nodata=ndvi_loaded.nodata
    )
    ndvi_stats.append(stats)  # Liste des statistiques par bande

# Conversion des statistiques en DataFrame
all_stats = []
for band_index, stats in enumerate(ndvi_stats):
    for poly_index, stat in enumerate(stats):
        all_stats.append({
            'class': gdf_classif_pixel_gras.iloc[poly_index]['Code'],
            'time': band_index + 1,  # Indice temporel correspondant à la bande
            'mean': stat['mean'],
            'std': stat['std']
        })

df_ndvi = pd.DataFrame(all_stats)
print(df_ndvi.head())

# Agrégation par classe et temps
df_grouped = df_ndvi.groupby(['class', 'time']).agg(
    mean_ndvi=('mean', 'mean'),
    std_ndvi=('std', 'mean')  # Moyenne des écarts-types pour simplifier
).reset_index()

# Tracer les courbes de signature temporelle
plt.figure(figsize=(12, 8))

for class_label in df_grouped['class'].unique():
    class_data = df_grouped[df_grouped['class'] == class_label]
    plt.plot(class_data['time'], class_data['mean_ndvi'], label=f'Classe {class_label}')
    plt.fill_between(
        class_data['time'],
        class_data['mean_ndvi'] - class_data['std_ndvi'],
        class_data['mean_ndvi'] + class_data['std_ndvi'],
        alpha=0.2
    )

plt.title("Signature temporelle NDVI par classe")
plt.xlabel("Temps (bandes temporelles)")
plt.ylabel("NDVI moyen")
plt.legend()
plt.grid()
plt.savefig(output_file)
plt.show()