
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import sys
sys.path.append('/home/onyxia/work/libsigma') # changement du path pour utiliser le fichier classification
import my_function as MF # provient d'un code que j'ai créée
import read_and_write as rw
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score

from rasterio.features import dataset_features
from rasterio.transform import from_origin
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import Point
import numpy as np

# 1 --- define parameters d'entrée
# inputs / fichiers en entrée
sample_filename = ('/home/onyxia/work/data/project/emprise_etude.shp')
image_filename = ('/home/onyxia/work/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif')
vector_filename = ('/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp')


# outputs / chemin de sortie
output_file = ('/home/onyxia/work/results/data')
output_centroid_file = ('/home/onyxia/work/results/data/centro.shp')

# vector to raster. 1 = ROI, 0 = out-side
roi_image = ('/home/onyxia/work/results/data/roi_raster.tif')
MF.hugo(sample_filename, image_filename, roi_image, dtype='int16')

# ouvrir vector_filename et enlever les polygon qui sont en dehors du roi_image valeur =1
# Charger le shapefile (vecteur) et l'image raster (ROI)
vector_data = gpd.read_file(vector_filename)
roi_raster = rasterio.open(roi_image)
ndvi_raster = rasterio.open(image_filename)

# créer un vecteur centroid qui représente le centroid de tous les pixel de mon image ndvi (utilise les info du raster taille pixel / total...)
# Découper les centroid par rapport au vextor_data. 
# Les centroide doivent avoir un nouveau champs 'NDVI' qui correspond a la valeur du pixel du ndvi_raster
# les centroides qui intersect un polygon doivent récupérer le 'Code' dans un nouveau champs



# === Obtenir les centroïdes du raster en vectorisant ===
def generate_centroids(raster):
    transform = raster.transform
    rows, cols = raster.height, raster.width

    # Calculer les coordonnées pour tous les pixels en une étape vectorisée
    x_coords = np.linspace(
        transform[2] + transform[0] / 2,
        transform[2] + transform[0] * (cols - 0.5),
        cols
    )
    y_coords = np.linspace(
        transform[5] + transform[4] / 2,
        transform[5] + transform[4] * (rows - 0.5),
        rows
    )

    # Créer une grille complète des points
    xx, yy = np.meshgrid(x_coords, y_coords)
    points = np.column_stack((xx.ravel(), yy.ravel()))

    return points

centroid_points = generate_centroids(ndvi_raster)



# === Filtrer par le ROI (optionnel pour accélérer) ===
def filter_by_roi(points, roi_bounds):
    xmin, ymin, xmax, ymax = roi_bounds
    return points[
        (points[:, 0] >= xmin) & (points[:, 0] <= xmax) &
        (points[:, 1] >= ymin) & (points[:, 1] <= ymax)
    ]

roi_bounds = roi_raster.bounds
centroid_points_filtered = filter_by_roi(centroid_points, roi_bounds)

# === Créer une GeoDataFrame pour les centroïdes filtrés ===
centroid_gdf = gpd.GeoDataFrame(
    geometry=gpd.points_from_xy(centroid_points_filtered[:, 0], centroid_points_filtered[:, 1]),
    crs=ndvi_raster.crs
)

# === Découper la couche centroid_gdf par rapport à vector_data ===
centroid_gdf = gpd.overlay(centroid_gdf, vector_data, how="intersection")

# === Ajouter le champ "NDVI" avec les valeurs du raster ===
def assign_ndvi(centroid_gdf, raster):
    # Vectorisation pour améliorer les performances
    with rasterio.open(raster) as src:
        affine = src.transform
        array = src.read(1)  # Lire la première bande

        # Obtenir les indices matriciels pour tous les points
        rows_cols = [src.index(point.x, point.y) for point in centroid_gdf.geometry]

        # Extraire les valeurs NDVI via une compréhension de liste
        values = [array[row, col] if 0 <= row < array.shape[0] and 0 <= col < array.shape[1] else np.nan
                  for row, col in rows_cols]

    centroid_gdf["NDVI"] = values
    return centroid_gdf

centroid_gdf = assign_ndvi(centroid_gdf, image_filename)

# === Associer le champ "Code" des polygones intersectés avec jointure spatiale ===
def assign_code(centroid_gdf, vector_gdf):
    vector_gdf = vector_gdf.to_crs(centroid_gdf.crs)
    centroid_gdf = gpd.sjoin(centroid_gdf, vector_gdf, how="left", predicate="intersects")
    if "Code" not in centroid_gdf.columns:
        centroid_gdf["Code"] = None
    return centroid_gdf

centroid_gdf = assign_code(centroid_gdf, vector_data)

# === Sauvegarder le fichier de sortie ===
centroid_gdf.to_file(output_centroid_file, driver='ESRI Shapefile')

print(f"Les centroïdes ont été enregistrés dans {output_centroid_file}.")


centroid_gdf.head()

# === Préparation des données pour le Machine Learning ===
X = centroid_gdf[["NDVI"]].values  # Features : NDVI
Y = centroid_gdf["Code_right"].values    # Target : Code

# Séparation en données d'entraînement et de test
test_size = 0.2
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=test_size, random_state=1)
print(f"Données divisées : {len(X_train)} pour l'entraînement et {len(X_test)} pour le test.")

# === Entraînement du modèle Random Forest ===
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)
RF = RandomForestClassifier(
    max_depth=50,
    n_estimators=100,
    oob_score=True,
    class_weight="balanced",
    max_samples=0.75,
    random_state=1
)

fold_scores = []
for fold, (train_idx, test_idx) in enumerate(skf.split(X_train, Y_train), 1):
    X_fold_train, X_fold_test = X_train[train_idx], X_train[test_idx]
    Y_fold_train, Y_fold_test = Y_train[train_idx], Y_train[test_idx]

    RF.fit(X_fold_train, Y_fold_train)
    Y_pred = RF.predict(X_fold_test)

    accuracy = accuracy_score(Y_fold_test, Y_pred)
    fold_scores.append(accuracy)
    print(f"Pli {fold}: Précision = {accuracy:.2f}")

print("Scores pour chaque pli :", fold_scores)
print(f"Précision moyenne : {np.mean(fold_scores):.2f}")
print(f"Écart type des scores : {np.std(fold_scores):.2f}")



