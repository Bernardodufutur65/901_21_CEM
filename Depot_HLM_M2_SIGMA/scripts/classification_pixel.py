from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import sys
sys.path.append('/home/onyxia/work/901_21_CEM/libsigma') # changement du path pour utiliser le fichier classification
import classification as cla # provient d'un code que j'ai créée

# 1 --- define parameters d'entrée
# inputs / fichiers en entrée
sample_filename = ('/home/onyxia/work/data/project/emprise_etude.shp')
image_filename = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif')

# Sample parameters / paramètres échantillonnage
test_size = 0.8

# outputs / chemin de sortie
output_file = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/')

# 2 --- Extract samples
# vector to raster. 1 = ROI, 0 = out-side
roi_image = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/roi_raster.tif')
cla.hugo(sample_filename, image_filename, roi_image, dtype='int16')


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
try:
    # Initialisation du modèle Random Forest
    RF = RandomForestClassifier(
        max_depth=50,
        n_estimators=100,  # Nombre de pixel
        oob_score=True,  # Out-of-Bag score
        class_weight="balanced",  # Poids équilibrés pour les classes
        max_samples=0.75,
        random_state=1
    )

    # Entraîner le modèle
    RF.fit(X_train, Y_train)
    print("Modèle entraîné avec succès.")

    # Évaluer la performance
    oob_score = RF.oob_score_
    print(f"Out-of-Bag Score : {oob_score:.2f}")
except Exception as e:
    print(f"Erreur lors de l'entraînement du modèle : {e}")
    raise


from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score

# Configuration de la validation croisée stratifiée
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)

# Initialisation du modèle Random Forest
RF = RandomForestClassifier(
    max_depth=50,
    n_estimators=100,  # Nombre de pixel
    oob_score=True,  # Out-of-Bag score
    class_weight="balanced",  # Poids équilibrés pour les classes
    max_samples=0.75,
    random_state=1
)

# Validation croisée avec scoring
scores = cross_val_score(RF, X_train, Y_train, cv=skf, scoring='accuracy')

# Résultats
print("Scores pour chaque fold :", scores)
print(f"Précision moyenne (cross-val) : {scores.mean():.2f}")
print(f"Écart type des scores : {scores.std():.2f}")


