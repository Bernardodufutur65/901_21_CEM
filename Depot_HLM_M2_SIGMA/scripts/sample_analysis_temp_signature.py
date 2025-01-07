# Import des librairies
import geopandas as gpd
import rasterio
import os
from rasterstats import zonal_stats
import pandas as pd
import matplotlib.pyplot as plt

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
# Filtrage des classes sélectionnées dans le champ 'Code'
gdf_classif_pixel_gras = gdf_echantillons[gdf_echantillons["Code"].isin(classes_en_gras)]
print(gdf_classif_pixel_gras)

# Intersection des polygones avec le NDVI
# Extraction des statistiques zonales pour chaque bande NDVI
ndvi_stats = []
for i in range(1, ndvi_loaded.count + 1):  # Pour chaque bande temporelle
    stats = zonal_stats(                   # statistiques zonales de chaque polygone
        gdf_classif_pixel_gras,            # Echantillons sur lesquels on fait les statistiques
        ndvi_loaded.read(i),               # Lecture des bandes du NDVI
        stats=['mean', 'std'],             # Calcul de la moyenne et écart-type des valeurs de NDVI
        affine=ndvi_loaded.transform,
        nodata=ndvi_loaded.nodata
    )
    ndvi_stats.append(stats)  # Liste des statistiques par bande

# Conversion des statistiques en DataFrame
# Création d'un dictionnaire qui contiendra la classe du polygone, le numéro de bande et les statistiques
all_stats = []
for band_index, stats in enumerate(ndvi_stats):
    for polygon_index, stat_poly in enumerate(stats):
        all_stats.append({
            'class': gdf_classif_pixel_gras.iloc[polygon_index]['Code'],
            'time': band_index + 1,  # Indice temporel correspondant à la bande
            'mean': stat_poly['mean'],
            'std': stat_poly['std']
        })

df_ndvi = pd.DataFrame(all_stats)
print(df_ndvi.head())

# Agrégation par classe et temps
df_grouped = df_ndvi.groupby(['class', 'time']).agg(
    mean_ndvi=('mean', 'mean'),
    std_ndvi=('std', 'mean')  # Moyenne des écarts-types pour simplifier
).reset_index()                # Facilite l'accès et l'utilisation des colonnes "normales" (et pas indexées)

#####Tracer les courbes de signature temporelle#####
# Dictionnaire pour associer les classes à des noms personnalisés
class_names = {
    12: 'Chêne',
    13: 'Robinier',
    14: 'Peupleraie',
    23: 'Douglas',
    24: 'Pin Lacirio ou Pin Noir',
    25: 'Pin Maritime'
}

# Création de la figure et de l'axe
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(7, 5))

# Définition des couleurs pour chaque classe
colors = ['tan', 'palegreen', 'limegreen', 'darkgreen', 'cornflowerblue', 'gold']
classes = df_grouped['class'].unique()  # Liste des classes uniques

# Parcours des classes et affichage
for class_label, color in zip(classes, colors):
    class_data = df_grouped[df_grouped['class'] == class_label]
    means = class_data['mean_ndvi']
    stds = class_data['std_ndvi']
    
    # Tracé de la courbe moyenne
    ax.plot(class_data['time'], means, color=color, label=class_names.get(int(class_label), f'Classe {class_label}'))
    
    # Zone d'incertitude (± écart-type)
    ax.fill_between(class_data['time'], means + stds, means - stds, facecolor=color, alpha=0.3)

ax.xaxis.set_ticklabels([    
    '000', '26/03/2022', '05/04/2022', '14/07/2022',
    '22/09/2022', '11/11/2022', '19/02/2023'])

# Configuration des axes et des légendes
ax.set_title("Signature temporelle de la moyenne et l'écart type du NDVI par classe")
ax.set_xlabel("Dates")
ax.set_ylabel("NDVI")
ax.legend()

# Exportation du graphique en PNG
plt.savefig(output_file)

# Affichage du graphique
plt.tight_layout()
plt.show()