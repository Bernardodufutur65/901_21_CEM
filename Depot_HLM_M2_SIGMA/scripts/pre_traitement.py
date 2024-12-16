

import os
from osgeo import gdal, ogr, osr


# Dossiers d'entrée et de sortie
input_folder = "/home/onyxia/work/data/images/"
output_folder = "/home/onyxia/work/901_21_CEM/Depot_HLM_M2_SIGMA/results/data/img_pretraitees"
os.makedirs(output_folder, exist_ok=True)
output_file = os.path.join(output_folder, "Serie_temp_S2_allbands.tif")

# Paramètres spécifiques
selected_bands = [2, 3, 4, 5, 6, 7, 8, 9, 11, 12]  # Bandes à sélectionner
resolution = 10  # Résolution spatiale cible (en mètres)
projection_target = "EPSG:2154"  # Projection cible Lambert 93
mask_file = "/home/onyxia/work/results/data/img_pretraitees/masque_foret.tif"  # Masque de forêt
shapefile_emprise = "/home/onyxia/work/data/project/emprise_etude.shp"  # Emprise
nodata_value = 0  # Valeur de NoData

# Vérifier les fichiers d'entrée
image_files = sorted([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(".tif")])
if not image_files:
    raise RuntimeError("Aucun fichier .tif trouvé dans le dossier d'entrée.")

# Charger le masque de forêt et le reprojeter si nécessaire
gdal_mask = gdal.Open(mask_file)
if not gdal_mask:
    raise RuntimeError(f"Impossible de charger le masque de forêt : {mask_file}")

# Reprojeter le masque en 10m si nécessaire
mask_geo_transform = gdal_mask.GetGeoTransform()
mask_projection = gdal_mask.GetProjection()
mask_width = gdal_mask.RasterXSize
mask_height = gdal_mask.RasterYSize

if abs(mask_geo_transform[1] - resolution) > 1e-6 or abs(mask_geo_transform[5] + resolution) > 1e-6:
    print("Reprojection et rééchantillonnage du masque de forêt...")
    temp_mask_file = os.path.join(output_folder, "masque_foret_10m.tif")
    gdal.Warp(
        temp_mask_file,
        gdal_mask,
        format="GTiff",
        xRes=resolution,
        yRes=resolution,
        dstSRS=projection_target,
        resampleAlg="near"
    )
    gdal_mask = gdal.Open(temp_mask_file)

mask_array = gdal_mask.GetRasterBand(1).ReadAsArray()
gdal_mask = None  # Fermer le fichier masque

# Charger l'emprise du shapefile
shp = ogr.Open(shapefile_emprise)
if not shp:
    raise RuntimeError(f"Impossible de charger le fichier shapefile : {shapefile_emprise}")
layer = shp.GetLayer()
emprise_extent = layer.GetExtent()  # Obtenir l'étendue [xmin, xmax, ymin, ymax]

# Déterminer la taille de la sortie basée sur l'emprise et la résolution
xmin, xmax, ymin, ymax = emprise_extent
width = int((xmax - xmin) / resolution)
height = int((ymax - ymin) / resolution)
geo_transform = (xmin, resolution, 0, ymax, 0, -resolution)

# Créer le fichier de sortie (GeoTIFF)
driver = gdal.GetDriverByName("GTiff")
output_dataset = driver.Create(
    output_file, width, height, len(image_files), gdal.UInt16,
    options=["COMPRESS=LZW"]
)
if not output_dataset:
    raise RuntimeError(f"Impossible de créer le fichier de sortie : {output_file}")

# Appliquer les métadonnées (géoréférencement et projection)
output_dataset.SetGeoTransform(geo_transform)
srs = osr.SpatialReference()
srs.ImportFromEPSG(2154)
output_dataset.SetProjection(srs.ExportToWkt())

# Traitement par image
for date_index, image_file in enumerate(image_files):
    print(f"Traitement de l'image {date_index + 1}/{len(image_files)} : {image_file}")

    gdal_image = gdal.Open(image_file)
    if not gdal_image:
        raise RuntimeError(f"Impossible de charger l'image : {image_file}")

    # Vérifier la résolution et reprojeter si nécessaire
    image_geo_transform = gdal_image.GetGeoTransform()
    if abs(image_geo_transform[1] - resolution) > 1e-6 or abs(image_geo_transform[5] + resolution) > 1e-6:
        print(f"Reprojection et rééchantillonnage de l'image {image_file}...")
        temp_image_file = os.path.join(output_folder, f"temp_{os.path.basename(image_file)}")
        gdal.Warp(
            temp_image_file,
            gdal_image,
            format="GTiff",
            xRes=resolution,
            yRes=resolution,
            dstSRS=projection_target,
            resampleAlg="bilinear"
        )
        gdal_image = gdal.Open(temp_image_file)

    try:
        # Lire la seule bande de l'image
        band = gdal_image.GetRasterBand(1)  # Une seule bande présente
        band_array = band.ReadAsArray()

        # Appliquer le masque (zones non-forêt)
        band_array[mask_array == 0] = nodata_value

        # Écrire dans le fichier de sortie
        output_band_index = date_index + 1  # Index de la bande dans le fichier de sortie
        output_band = output_dataset.GetRasterBand(output_band_index)
        output_band.WriteArray(band_array)
        output_band.SetNoDataValue(nodata_value)
    except Exception as e:
        print(f"Erreur avec l'image {image_file}: {e}")

    gdal_image = None  # Fermer l'image

# Sauvegarder les modifications et fermer le fichier de sortie
if output_dataset:
    output_dataset.FlushCache()
    output_dataset = None

print(f"Image empilée créée avec succès : {output_file}")