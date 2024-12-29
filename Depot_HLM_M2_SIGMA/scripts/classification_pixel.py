from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import sys
import classification as cla # provient d'un code que j'ai créée
sys.path.append('/home/onyxia/work/901_21_CEM/libsigma') # changement du path pour utiliser le fichier classification

# 1 --- define parameters d'entrée
# inputs / fichiers en entrée
sample_filename = ('/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp')
image_filename = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif')

# Sample parameters / paramètres échantillonnage
test_size = 0.8

# outputs / chemin de sortie
output_file = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/')

# 2 --- Extract samples
# vector to raster
roi_image = ('/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/roi_raster.tif')
cla.hugo(sample_filename, image_filename, roi_image, field_name=None, dtype=None)


try:
    # Extraction des données et labels
    X, Y, t = cla.get_samples_from_roi(image_filename, sample_filename)
    print(f"Samples extraits avec succès : {len(X)} échantillons.")
except Exception as e:
    print(f"Erreur lors de l'extraction des échantillons : {e}")
    raise
# Séparation en données d'entraînement et de test
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=test_size, random_state=42)
print(f"Données divisées : {len(X_train)} pour l'entraînement et {len(X_test)} pour le test.")


# 3 --- Train / Entraînement du modèle
try:
    # Initialisation du modèle Random Forest
    RF = RandomForestClassifier(
        max_depth=50,
        n_estimators=100,  # Nombre d'arbres
        oob_score=True,  # Out-of-Bag score
        class_weight="balanced",  # Poids équilibrés pour les classes
        random_state=42
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



from osgeo import gdal

def open_image_test(filename):
    raster = gdal.Open(filename)
    if raster is None:
        raise ValueError(f"Impossible d'ouvrir l'image : {filename}")
    print(f"Image ouverte avec succès : {filename}")
    print(f"Dimensions : {raster.RasterXSize} x {raster.RasterYSize}")
    return raster

# Testez votre raster_name et roi_name
open_image_test(image_filename)
open_image_test(sample_filename)