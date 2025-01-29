import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import matplotlib.pyplot as plt

# Définir les fichiers d'entrée et de sortie
sample_filename = '/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp'  # échantillons
image_filename = '/home/onyxia/work/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif'  # NDVI
output_folder = '/home/onyxia/work/results/figure' # dossier de sortie
output_file_diag = os.path.join(output_folder, 'diag_baton_dist_centroide_classe.png') # fichier de sortie partie 1
output_file_violin = os.path.join(output_folder, 'violin_plot_dist_centroide_by_poly_by_class.png') # fichier de sortie partie 2

# Charger les échantillons et le raster NDVI
sample_data = gpd.read_file(sample_filename)
ndvi_open = rasterio.open(image_filename)

# Défintion des classes rouges et bleues
classe_rouge = ['11', '12', '13', '14', '23', '24', '25']
classe_bleue = ['15', '26', '28', '29']

########## --- À l'échelle de l'image entière, tous polygones confondus --- ##########
# Fonction pour extraire les valeurs NDVI d'un raster pour des polygones donnés
def extract_ndvi_values(ndvi_raster, polygons):
    values = []
    for _, poly in polygons.iterrows():
        out_image, _ = mask(ndvi_raster, [poly.geometry], crop=True)
        ndvi_values = out_image[out_image != ndvi_raster.nodata]
        values.extend(ndvi_values)
    return np.array(values)

# Calcul des centroïdes et des distances moyennes
resultats = []
for classe, codes in {'Rouge': classe_rouge, 'Bleue': classe_bleue}.items():
    # Filtrer les échantillons pour la classe actuelle
    classe_data = sample_data[sample_data['Code'].isin(codes)]
    
    # Extraire les valeurs NDVI
    ndvi_values = extract_ndvi_values(ndvi_open, classe_data)
    
    # Calculer le centroïde (moyenne des valeurs NDVI)
    centroide = np.mean(ndvi_values)
    
    # Calculer les distances des pixels au centroïde
    distances = np.abs(ndvi_values - centroide)
    
    # Calculer la distance moyenne
    distance_moyenne = np.mean(distances)
    
    # Sauvegarder les résultats
    resultats.append({'Classe': classe, 'Centroïde': centroide, 'Distance moyenne': distance_moyenne})

# Convertir les résultats en DataFrame pour la visualisation
resultats_df = pd.DataFrame(resultats)

# Générer le diagramme en bâton
plt.figure(figsize=(8, 6))
plt.bar(['Peuplements purs', 'Peuplements en mélange'], resultats_df['Distance moyenne'], color=['red', 'blue'])
plt.xlabel('Classe')
plt.ylabel('Distance moyenne au centroïde')
plt.title('Distance moyenne au centroïde des NDVI par classe')
plt.savefig(output_file_diag)
plt.close()

# Affichage du graphique
plt.tight_layout()
plt.show()

########## --- À l'échelle de chaque polygone --- ##########
# Fonction pour extraire les valeurs NDVI d'un raster pour un polygone donné
def extract_ndvi_values(ndvi_raster, polygon):
    out_image, _ = mask(ndvi_raster, [polygon.geometry], crop=True)
    return out_image[out_image != ndvi_raster.nodata]

# Liste pour stocker les distances moyennes par classe
distances_par_classe = {'Rouge': [], 'Bleue': []}

# Traitement par classe
for classe, codes in {'Rouge': classe_rouge, 'Bleue': classe_bleue}.items():
    # Filtrer les échantillons pour la classe actuelle
    classe_data = sample_data[sample_data['Code'].isin(codes)]
    
    # Calculer les distances moyennes pour chaque polygone
    for _, poly in classe_data.iterrows():
        # Extraire les valeurs NDVI du polygone
        ndvi_values = extract_ndvi_values(ndvi_open, poly)
        
        if len(ndvi_values) > 0:  # Vérifier que le polygone contient des pixels valides
            # Calculer le centroïde (moyenne des valeurs NDVI)
            centroide = np.mean(ndvi_values)
            
            # Calculer les distances des pixels au centroïde
            distances = np.abs(ndvi_values - centroide)
            
            # Calculer la distance moyenne
            distance_moyenne = np.mean(distances)
            
            # Ajouter la distance moyenne à la liste de la classe
            distances_par_classe[classe].append(distance_moyenne)

# Générer le violin plot avec matplotlib
plt.figure(figsize=(10, 6))

# Générer les distributions pour chaque classe
positions = [1, 2]
labels = ['Peuplements purs', 'Peuplements en mélange']
data = [distances_par_classe['Rouge'], distances_par_classe['Bleue']]

# Fonction pour tracer un violin plot avec matplotlib
for pos, d, label in zip(positions, data, labels):
    parts = plt.violinplot(d, [pos], showmeans=True, showextrema=True, showmedians=True)
    
    # Personnalisation des couleurs
    for pc in parts['bodies']:
        pc.set_facecolor('red' if label == 'Peuplements purs' else 'blue')
        pc.set_edgecolor('black')
        pc.set_alpha(0.6)
    parts['cmeans'].set_color('green')
    parts['cmedians'].set_color('orange')
    parts['cbars'].set_color('black')

# Ajouter des étiquettes et un titre
plt.xticks(positions, labels)
plt.xlabel('Classe')
plt.ylabel('Distance moyenne au centroïde')
plt.title('Distances moyennes au centroïde des NDVI pour les polygones d’une classe')

# Sauvegarder la figure
plt.savefig(output_file_violin)
plt.close()

# Affichage du graphique
plt.tight_layout()
plt.show()