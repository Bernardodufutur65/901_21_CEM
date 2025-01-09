import sys
sys.path.append('/home/onyxia/work/libsigma')
import os
import geopandas as gpd
from sklearn.model_selection import train_test_split
# personal librairies
import classification as cla

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

# Défintion des classes rouges et bleues
classe_rouge = ['11', '12', '13', '14', '23', '24', '25']
classe_bleue = ['15', '26', '28', '29']

# Sélection des polygones correspondant aux classes rouges et bleues dans deux variables distinctes
sample_rouge = sample_data[sample_data['Code'].isin(classe_rouge)]
sample_bleu = sample_data[sample_data['Code'].isin(classe_bleue)]

