import sys
import os
import geopandas as gpd
import rasterio
from sklearn.model_selection import train_test_split
# personal librairies
import classification as cla

sys.path.append('/home/onyxia/work/libsigma')

# 1 --- define parameters
# inputs
sample_filename = '/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp'  # échantillons
image_filename = '/home/onyxia/work/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif'  # ndvi
# outputs
output_folder = '/home/onyxia/work/results/figure'
output_file_diag = os.path.join(output_folder, 'diag_baton_dist_centroide_classe.png ')
output_file_violin = os.path.join(output_folder, 'violin_plot_dist_centroide_by_poly_by_class.png ')

# Chargement des couches
sample_data = gpd.read_file(sample_filename)
ndvi_open = rasterio.open(image_filename)

# Défintion des classes rouges et bleues
classe_rouge = ['11', '12', '13', '14', '23', '24', '25']
classe_bleue = ['15', '26', '28', '29']

# Sélection des polygones correspondant aux classes rouges et bleues dans deux variables
sample_rouge = sample_data[sample_data['Code'].isin(classe_rouge)]
sample_bleu = sample_data[sample_data['Code'].isin(classe_bleue)]

########## --- À l'échelle de l'image entière, tous polygones confondus --- ##########
# Regrouper les pixels appartenant à chaque classe
###A REPRENDRE###
import numpy as np
import rasterio
from rasterio.mask import mask

# Fonction pour extraire les pixels NDVI pour un groupe de polygones
def extract_ndvi_values(sample_group, raster, affine):
    # Convertir les polygones en géométrie GeoJSON
    geometries = [geom for geom in sample_group.geometry]
    
    # Extraire les pixels NDVI à l'intérieur des polygones
    out_image, out_transform = mask(raster, geometries, crop=True)
    
    # Remettre en tableau 2D pour faciliter l'analyse
    ndvi_values = out_image[0].flatten()
    
    # Filtrer les valeurs valides (par exemple, en excluant les nodata)
    ndvi_values = ndvi_values[ndvi_values != raster.nodata]
    
    return ndvi_values

# Extraction des valeurs NDVI pour les classes rouges
ndvi_rouge = extract_ndvi_values(sample_rouge, ndvi_open, ndvi_open.transform)

# Extraction des valeurs NDVI pour les classes bleues
ndvi_bleu = extract_ndvi_values(sample_bleu, ndvi_open, ndvi_open.transform)

# Affichage des résultats
print("NDVI pour les classes rouges :", ndvi_rouge)
print("NDVI pour les classes bleues :", ndvi_bleu)