'''
A lire pour les trous de balle qui ne savent pas quoi faire de leur vacances. 
Je bosse le 2 MOIIIIII, envoyez moi un discord si vous n'arrivez pas sur cette partie, vu que c'est moi qui ai commencé
'''


from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import sys
sys.path.append('/home/onyxia/work/901_21_CEM/libsigma') # changement du path pour utiliser le fichier classification
import classification as cla # provient d'un code que j'ai créée
import read_and_write as rw

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score
import numpy as np
import geopandas as gpd



import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import Point
import numpy as np

# 1 --- define parameters d'entrée
# inputs / fichiers en entrée
sample_filename = ('/home/onyxia/work/data/project/emprise_etude.shp')
image_filename = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif')
vector_filename = ('/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp')


# outputs / chemin de sortie
output_file = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/')


# vector to raster. 1 = ROI, 0 = out-side
roi_image = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/roi_raster.tif')
cla.hugo(sample_filename, image_filename, roi_image, dtype='int16')

# ouvrir vector_filename et enlever les polygon qui sont en dehors du roi_image valeur =1
# Charger le shapefile (vecteur) et l'image raster (ROI)
vector_data = gpd.read_file(vector_filename)
roi_raster = rasterio.open(roi_image)

# Créer une fonction pour filtrer les polygones en fonction de ROI
def filter_polygons_by_roi(vector_data, roi_raster):
    roi_array = roi_raster.read(1)  # Lire la première bande
    transform = roi_raster.transform
    
    # Filtrer les polygones qui intersectent les zones ROI=1
    def is_in_roi(geom):
        geom_bounds = geom.bounds
        rows, cols = rasterio.transform.rowcol(
            transform, [geom_bounds[0], geom_bounds[2]], [geom_bounds[1], geom_bounds[3]]
        )
        mask = geometry_mask([geom], transform=transform, invert=True, out_shape=roi_array.shape)
        return np.any(roi_array[mask] == 1)
    
    filtered_data = vector_data[vector_data.geometry.apply(is_in_roi)]
    return filtered_data

# Filtrer les polygones
filtered_vector_data = filter_polygons_by_roi(vector_data, roi_raster)

# créer une nouvelle couche de centroide par rapport aux pixel qui sont inclu dans ma géométrie.


# Créer une couche contenant les centroïdes de tous les pixels dans chaque polygone
def create_pixel_centroid_layer_optimized(filtered_data, roi_raster):
    roi_array = roi_raster.read(1)
    transform = roi_raster.transform
    centroids = []

    # Pré-calculer la matrice de transformation inverse
    transform_inv = ~transform

    for idx, row in filtered_data.iterrows():
        # Créer un masque binaire pour le polygone
        mask = geometry_mask(
            [row.geometry],
            transform=transform,
            invert=True,
            out_shape=roi_array.shape
        )
        
        # Identifier les pixels dans le polygone avec ROI=1
        rows, cols = np.where(mask & (roi_array == 1))
        
        # Calculer les coordonnées centrales des pixels en batch
        coords = rasterio.transform.xy(transform, rows, cols, offset='center')
        x_coords, y_coords = coords

        # Ajouter les centroïdes sous forme de batch
        centroids.extend([
            {
                'geometry': Point(x, y),
                'Code': row['Code'],  # Champ existant dans le fichier vecteur
                'Pixel_Value': roi_array[r, c]
            }
            for x, y, r, c in zip(x_coords, y_coords, rows, cols)
        ])
    
    # Créer une GeoDataFrame à partir des centroïdes
    centroid_gdf = gpd.GeoDataFrame(centroids, crs=filtered_data.crs)
    return centroid_gdf

# Générer la couche de centroïdes
centroid_layer = create_pixel_centroid_layer_optimized(vector_data, roi_raster)

# ajouter la valeur du pixel et ne numéro du polygon champs "Code"
# enregistrer cette couche dans un fichier avec cette sortie "/home/onyxia/work/results/data/centro.shp"
output_centroid_file = '/home/onyxia/work/results/data/centro.shp'
centroid_layer.to_file(output_centroid_file)



# Sample parameters / paramètres échantillonnage
test_size = 0.2

#### Ancienne partie qui fonctionne 
try:
    # Extraction des données et labels
    X, Y, t = cla.get_samples_from_roi(image_filename, roi_image)
    print(f"Samples extraits avec succès : {len(X)} échantillons.")
except Exception as e:
    print(f"Erreur lors de l'extraction des échantillons : {e}")
    raise
# Séparation en données d'entraînement et de test
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=test_size, random_state=1)
print(f"Données divisées : {len(X_train)} pour l'entraînement et {len(X_test)} pour le test.")







# 3 --- Train / Entraînement du modèle

# Configuration de la validation croisée stratifiée
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)

# Initialisation du modèle Random Forest
RF = RandomForestClassifier(
    max_depth=50,
    n_estimators=100,
    oob_score=True,
    class_weight="balanced",
    max_samples=0.75,
    random_state=1,
    #n_jobs=-1  # Utilisation de tous les cœurs disponibles
)

# Liste pour stocker les scores de chaque pli
fold_scores = []

# Validation croisée incrémentale
for fold, (train_idx, test_idx) in enumerate(skf.split(X_train, Y_train), 1):
    # Division des données pour le pli courant
    X_fold_train, X_fold_test = X_train[train_idx], X_train[test_idx]
    Y_fold_train, Y_fold_test = Y_train[train_idx], Y_train[test_idx]
    
    # Entraîner le modèle sur les données d'entraînement du pli
    RF.fit(X_fold_train, Y_fold_train)
    
    # Prédire sur les données de test du pli
    Y_pred = RF.predict(X_fold_test)
    
    # Calculer la précision pour le pli courant
    accuracy = accuracy_score(Y_fold_test, Y_pred)
    fold_scores.append(accuracy)
    
    # Afficher le score du pli
    print(f"Pli {fold}: Précision = {accuracy:.2f}")

# Résultats globaux
print("Scores pour chaque pli :", fold_scores)
print(f"Précision moyenne : {sum(fold_scores) / len(fold_scores):.2f}")
print(f"Écart type des scores : {np.std(fold_scores):.2f}")
