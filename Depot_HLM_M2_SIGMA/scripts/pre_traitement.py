
import os
import rasterio
# from rasterio.mask import mask
from rasterio.enums import Resampling
from rasterio.warp import reproject
import geopandas as gpd
import numpy as np


# Dossiers d'entrée et de sortie
input_folder = "/home/onyxia/work/data/images/"
output_folder = "/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/img_pretraitees"
os.makedirs(output_folder, exist_ok=True)
output_file = os.path.join(output_folder, "Serie_temp_S2_allbands.tif")

# Paramètres spécifiques
resolution = 10  # Résolution spatiale cible (en mètres)
projection_target = "EPSG:2154"  # Projection cible Lambert 93
mask_file = "/home/onyxia/work/results/data/img_pretraitees/masque_foret.tif"  # Masque de forêt
shapefile_emprise = "/home/onyxia/work/data/project/emprise_etude.shp"  # Emprise
nodata_value = 0  # Valeur de NoData

# Vérifier les fichiers d'entrée
image_files = sorted([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(".tif")])
if not image_files:
    raise RuntimeError("Aucun fichier .tif trouvé dans le dossier d'entrée.")

# Charger l'emprise du shapefile
gdf = gpd.read_file(shapefile_emprise)
gdf = gdf.to_crs(projection_target)
emprise_bounds = gdf.total_bounds  # [xmin, ymin, xmax, ymax]

# Déterminer les dimensions cibles
output_width = int((emprise_bounds[2] - emprise_bounds[0]) / resolution)
output_height = int((emprise_bounds[3] - emprise_bounds[1]) / resolution)

# Charger et reprojeter le masque de forêt
with rasterio.open(mask_file) as src_mask:
    mask_data = np.zeros((output_height, output_width), dtype=src_mask.read(1).dtype)
    reproject(
        source=src_mask.read(1),
        destination=mask_data,
        src_transform=src_mask.transform,
        src_crs=src_mask.crs,
        dst_transform=rasterio.transform.from_bounds(*emprise_bounds, output_width, output_height),
        dst_crs=projection_target,
        resampling=Resampling.nearest
    )

# Créer le fichier de sortie (GeoTIFF)
profile = {
    "driver": "GTiff",
    "height": output_height,
    "width": output_width,
    "count": len(image_files),  # Une bande par image, toutes empilées
    "dtype": "uint16",
    "crs": projection_target,
    "transform": rasterio.transform.from_bounds(*emprise_bounds, output_width, output_height),
    "nodata": nodata_value,
    "compress": "lzw"
}

with rasterio.open(output_file, "w", **profile) as dst:
    band_counter = 1
    for image_file in image_files:
        print(f"Traitement de l'image : {image_file}")

        with rasterio.open(image_file) as src:
            # Lire la seule bande de l'image
            band_data = src.read(1)

            # Reprojection et redimensionnement
            reprojected_band = np.zeros((output_height, output_width), dtype=band_data.dtype)
            reproject(
                source=band_data,
                destination=reprojected_band,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=profile["transform"],
                dst_crs=projection_target,
                resampling=Resampling.bilinear
            )

            # Appliquer le masque (zones non-forêt)
            reprojected_band[mask_data == 0] = nodata_value

            # Écrire la bande dans le fichier de sortie
            dst.write(reprojected_band, indexes=band_counter)
            dst.set_band_description(band_counter, f"Band {band_counter}")
            band_counter += 1

print(f"Image empilée créée avec succès : {output_file}")

#####################################################
#####################################################
#####################################################


# Étape 1 : Sélectionner toutes les bandes B4 et B8
input_folder = "/home/onyxia/work/data/images/"
output_folder = "/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/img_pretraitees"
os.makedirs(output_folder, exist_ok=True)
output_file_ndvi = os.path.join(output_folder, "Serie_temp_S2_ndvi.tif")
resolution = 10  # Résolution spatiale cible (en mètres)
projection_target = "EPSG:2154"  # Projection cible Lambert 93
nodata_value = -9999  # Valeur de NoData

# Filtrer les images pour inclure uniquement celles contenant "B4" et "B8", exclure "B8A"
images = [
    f for f in os.listdir(input_folder)
    if ("B4" in f or "B8" in f) and "B8A" not in f
]

# Grouper les images par date en utilisant les 15 premiers caractères du nom
grouped_images = {}
for img in images:
    date_key = img[:19]  # Utiliser les 15 premiers caractères comme clé
    if date_key not in grouped_images:
        grouped_images[date_key] = []
    grouped_images[date_key].append(img)

# Charger le masque de forêt et le reprojeter
with rasterio.open(mask_file) as src_mask:
    mask_data = src_mask.read(1).astype("float32")
    mask_transform = src_mask.transform
    mask_crs = src_mask.crs

# Initialisation des NDVI à empiler
dates_with_ndvi = sorted(grouped_images.keys())
output_height, output_width, profile = None, None, None

# Étape 2 : Calculer les NDVI pour les paires B4 et B8 correspondant à la même date
ndvi_bands = []
for date_key in dates_with_ndvi:
    # Trouver les bandes B4 et B8 pour cette date
    b4_file = next((f for f in grouped_images[date_key] if "B4" in f), None)
    b8_file = next((f for f in grouped_images[date_key] if "B8" in f), None)

    if b4_file and b8_file:
        print(f"Calcul du NDVI pour la date {date_key}: B4 -> {b4_file}, B8 -> {b8_file}")

        # Charger les bandes B4 et B8
        with rasterio.open(os.path.join(input_folder, b4_file)) as src_b4:
            b4_data = src_b4.read(1).astype("float32")
            if not profile:
                profile = src_b4.profile
                output_width, output_height = src_b4.width, src_b4.height

        with rasterio.open(os.path.join(input_folder, b8_file)) as src_b8:
            b8_data = src_b8.read(1).astype("float32")

        # Calculer le NDVI
        ndvi = (b8_data - b4_data) / (b8_data + b4_data)
        ndvi = np.where((b8_data + b4_data) == 0, nodata_value, ndvi)  # Éviter les divisions par zéro

        # Ajouter le NDVI calculé à la liste des bandes NDVI
        ndvi_bands.append(ndvi)

    else:
        print(f"Bandes B4 ou B8 manquantes pour la date {date_key}.")

# Étape 3 : Compiler toutes les bandes NDVI dans un seul fichier
if not profile:
    raise RuntimeError("Impossible de définir le profil des images. Vérifiez les fichiers d'entrée.")

# Mettre à jour le profil pour l'image de sortie
profile.update(
    driver="GTiff",
    height=output_height,
    width=output_width,
    count=len(ndvi_bands),  # Une bande par date
    dtype="float32",
    nodata=nodata_value,
    compress="lzw"
)

# Écrire les bandes NDVI dans le fichier de sortie
with rasterio.open(output_file_ndvi, "w", **profile) as dst:
    for band_index, ndvi_band in enumerate(ndvi_bands, start=1):
        dst.write(ndvi_band, indexes=band_index)
        dst.set_band_description(band_index, f"NDVI_{dates_with_ndvi[band_index - 1]}")

print(f"Fichier NDVI compilé créé avec succès : {output_file_ndvi}")















import os
import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np

# Étape 1 : Initialisation des paramètres et des dossiers
input_folder = "/home/onyxia/work/data/images/"
output_folder = "/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/img_pretraitees"
os.makedirs(output_folder, exist_ok=True)
output_file_ndvi = os.path.join(output_folder, "Serie_temp_S2_ndvi.tif")
mask_file = "/home/onyxia/work/results/data/img_pretraitees/masque_foret.tif"  # Masque de forêt
nodata_value = -9999  # Valeur de NoData

# Étape 2 : Filtrer et grouper les bandes B4 et B8
images = [
    f for f in os.listdir(input_folder)
    if ("B4" in f or "B8" in f) and "B8A" not in f
]

grouped_images = {}
for img in images:
    date_key = img[:19]  # Utiliser les 19 premiers caractères comme clé
    if date_key not in grouped_images:
        grouped_images[date_key] = []
    grouped_images[date_key].append(img)

# Charger le masque de forêt et ses métadonnées
with rasterio.open(mask_file) as src_mask:
    mask_data = src_mask.read(1).astype("float32")
    mask_transform = src_mask.transform
    mask_crs = src_mask.crs

# Initialisation des NDVI à empiler
dates_with_ndvi = sorted(grouped_images.keys())
output_height, output_width, profile = None, None, None

ndvi_bands = []

# Étape 3 : Calcul des NDVI avec application du masque avant le calcul
for date_key in dates_with_ndvi:
    # Trouver les bandes B4 et B8 pour cette date
    b4_file = next((f for f in grouped_images[date_key] if "B4" in f), None)
    b8_file = next((f for f in grouped_images[date_key] if "B8" in f), None)

    if b4_file and b8_file:
        print(f"Traitement de la date {date_key}: B4 -> {b4_file}, B8 -> {b8_file}")

        # Charger les bandes B4 et B8
        with rasterio.open(os.path.join(input_folder, b4_file)) as src_b4:
            b4_data = src_b4.read(1).astype("float32")
            b4_transform = src_b4.transform
            b4_crs = src_b4.crs
            if not profile:
                profile = src_b4.profile
                output_width, output_height = src_b4.width, src_b4.height

        with rasterio.open(os.path.join(input_folder, b8_file)) as src_b8:
            b8_data = src_b8.read(1).astype("float32")

        # Reprojeter le masque pour qu'il corresponde aux bandes B4 et B8
        reprojected_mask = np.zeros_like(b4_data, dtype="float32")
        reproject(
            source=mask_data,
            destination=reprojected_mask,
            src_transform=mask_transform,
            src_crs=mask_crs,
            dst_transform=b4_transform,
            dst_crs=b4_crs,
            resampling=Resampling.nearest
        )

        # Appliquer le masque aux bandes B4 et B8
        b4_data[reprojected_mask == 0] = nodata_value
        b8_data[reprojected_mask == 0] = nodata_value

        # Calculer le NDVI uniquement dans les zones non masquées
        ndvi = (b8_data - b4_data) / (b8_data + b4_data)
        ndvi = np.where((b8_data + b4_data) == 0, nodata_value, ndvi)

        # Ajouter la bande NDVI avec masque appliqué à la liste
        ndvi_bands.append(ndvi)

    else:
        print(f"Bandes B4 ou B8 manquantes pour la date {date_key}.")

# Étape 4 : Compilation des bandes NDVI dans un fichier unique
if not profile:
    raise RuntimeError("Impossible de définir le profil des images. Vérifiez vos données d'entrée.")

# Mettre à jour le profil pour l'image de sortie
profile.update(
    driver="GTiff",
    height=output_height,
    width=output_width,
    count=len(ndvi_bands),
    dtype="float32",
    nodata=nodata_value,
    compress="lzw"
)

# Sauvegarder les NDVI
with rasterio.open(output_file_ndvi, "w", **profile) as dst:
    for band_index, ndvi_band in enumerate(ndvi_bands, start=1):
        dst.write(ndvi_band, indexes=band_index)
        dst.set_band_description(band_index, f"NDVI_{dates_with_ndvi[band_index - 1]}")

print(f"Fichier NDVI compilé avec succès : {output_file_ndvi}")
