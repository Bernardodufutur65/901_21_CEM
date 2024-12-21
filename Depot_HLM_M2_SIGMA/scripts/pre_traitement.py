
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