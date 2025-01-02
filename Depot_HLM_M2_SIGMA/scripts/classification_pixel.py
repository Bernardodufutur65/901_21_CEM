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


# 1 --- define parameters d'entrée
# inputs / fichiers en entrée
sample_filename = ('/home/onyxia/work/data/project/emprise_etude.shp')
image_filename = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif')

# Sample parameters / paramètres échantillonnage
test_size = 0.8

# outputs / chemin de sortie
output_file = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/')


# vector to raster. 1 = ROI, 0 = out-side
roi_image = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/roi_raster.tif')
cla.hugo(sample_filename, image_filename, roi_image, dtype='int16')




### Nouvelle partie qui vien de Seance4.ipynb (cette partie de doit faire en sorte d'avoir les polygons avec leur attribut)
### Il faudrais faire les même étapes que la Seance4.ipynb avant de faire la partie # 3 --- Train / Entraînement du modèle
# 2 --- extract samples
# 2.1 get_xy_from_file
# 2.2 xy_to_rowcol
# 2.3 get_row_col_from_file
is_point = True
# if is_point is True
field_name = 'num'
if not is_point :
    X, Y, t = cla.get_samples_from_roi(image_filename, sample_filename)
else :
    # get X
    list_row, list_col = rw.get_row_col_from_file(sample_filename, image_filename)
    image = rw.load_img_as_array(image_filename)
    X = image[(list_row, list_col)]

    # get Y
    gdf = gpd.read_file(sample_filename)
    Y = gdf.loc[:, field_name].values
    Y = np.atleast_2d(Y).T

list_cm = []
list_accuracy = []
list_report = []

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
