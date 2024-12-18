#ERREUR DE Découpage a l'emprise et bande manquante mais image plus grosse
'''
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

# Dimensions cibles fixes
fixed_width = 10990
fixed_height = 10990

# Vérifier les fichiers d'entrée
image_files = sorted([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(".tif")])
if not image_files:
    raise RuntimeError("Aucun fichier .tif trouvé dans le dossier d'entrée.")

# Charger le masque de forêt et le reprojeter si nécessaire
gdal_mask = gdal.Open(mask_file)
if not gdal_mask:
    raise RuntimeError(f"Impossible de charger le masque de forêt : {mask_file}")

# Reprojeter le masque dans la projection cible
print("Reprojection du masque de forêt...")
temp_mask_file = os.path.join(output_folder, "masque_foret_reprojete.tif")
gdal.Warp(
    temp_mask_file,
    gdal_mask,
    format="GTiff",
    dstSRS=projection_target,
    width=fixed_width,
    height=fixed_height,
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

# Déterminer la taille de la sortie basée sur des dimensions fixes
xmin, xmax, ymin, ymax = emprise_extent
geo_transform = (xmin, resolution, 0, ymax, 0, -resolution)

# Créer le fichier de sortie (GeoTIFF)
driver = gdal.GetDriverByName("GTiff")
output_dataset = driver.Create(
    output_file, fixed_width, fixed_height, len(image_files), gdal.GDT_UInt16,
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
for image_index, image_file in enumerate(image_files):
    print(f"Traitement de l'image {image_index + 1}/{len(image_files)} : {image_file}")

    gdal_image = gdal.Open(image_file)
    if not gdal_image:
        raise RuntimeError(f"Impossible de charger l'image : {image_file}")

    # Découper et reprojeter l'image selon des dimensions fixes
    print(f"Reprojection et redimensionnement de l'image {image_file}...")
    temp_image_file = os.path.join(output_folder, f"temp_{os.path.basename(image_file)}")
    gdal.Warp(
        temp_image_file,
        gdal_image,
        format="GTiff",
        outputBounds=(xmin, ymin, xmax, ymax),  # Découpage selon l'emprise
        width=fixed_width,
        height=fixed_height,
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
        output_band_index = image_index + 1  # Index de la bande dans le fichier de sortie
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
'''

import os
import rasterio
from rasterio.mask import mask
from rasterio.enums import Resampling
from rasterio.warp import reproject, calculate_default_transform
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









'''

import numpy as np
import rasterio as rio
from rasterio.transform import from_bounds
from rasterio.crs import CRS

def calculate_ndvi(releves, emprise, forest_mask, output_path):
    suffixe = '.tif'
    minx, miny, maxx, maxy = get_img_extend(emprise)
    src_epsg = 32631  # EPSG 32631 (UTM zone 31N)
    dst_epsg = 2154   # EPSG 2154 (RGF93 / Lambert-93)

    for r in releves:
        # Reproject B8 and B4 bands
        band_b8_name = f'data/images/SENTINEL2{r}8'
        band_b4_name = f'data/images/SENTINEL2{r}4'
        band_b8_file = f'{band_b8_name}{suffixe}'
        band_b4_file = f'{band_b4_name}{suffixe}'
        
        # Output filenames for reprojected bands
        b8_reproj_file = f"{band_b8_name}_10_2154{suffixe}"
        b4_reproj_file = f"{band_b4_name}_10_2154{suffixe}"
        
        reproject_raster(minx, miny, maxx, maxy, band_b8_file, b8_reproj_file, src_epsg, dst_epsg)
        reproject_raster(minx, miny, maxx, maxy, band_b4_file, b4_reproj_file, src_epsg, dst_epsg)

        # Load reprojected bands as arrays
        band_b8 = rw.load_img_as_array(b8_reproj_file)
        band_b4 = rw.load_img_as_array(b4_reproj_file)
        
        # Load forest mask and apply it
        masque_foret = rw.load_img_as_array(forest_mask).astype('bool')
        band_b8[~masque_foret] = 0
        band_b4[~masque_foret] = 0

        # Calculate NDVI
        ndvi = np.zeros_like(band_b8, dtype=np.float32)
        numerator = band_b8 - band_b4
        denominator = band_b8 + band_b4
        with np.errstate(divide='ignore', invalid='ignore'):
            ndvi = np.where(denominator == 0, 0, numerator / denominator)

        # Save NDVI as a new raster
        with rio.open(b8_reproj_file) as src:
            transform = src.transform
            profile = src.profile.copy()
            profile.update(dtype=rio.float32, count=1, compress='lzw', crs=CRS.from_epsg(dst_epsg))

        ndvi_output_file = f"{output_path}/NDVI_{r}{suffixe}"
        with rio.open(ndvi_output_file, 'w', **profile) as dst:
            dst.write(ndvi, 1)

# Inputs
emprise = 'data/project/emprise.tif'
releves = [
    'B_20220326-105856-076_L2A_T31TCJ_C_V3-0_FRE_B',
    'B_20220405-105855-542_L2A_T31TCJ_C_V3-0_FRE_B',
    'B_20220803-105903-336_L2A_T31TCJ_C_V3-0_FRE_B',
    'B_20221111-105858-090_L2A_T31TCJ_C_V3-1_FRE_B',
    'A_20221116-105900-865_L2A_T31TCJ_C_V3-1_FRE_B',
    'B_20230209-105857-157_L2A_T31TCJ_C_V3-1_FRE_B'
]
forest = 'masque_foret.tif'
output_path = 'results/ndvi'

# Calculate NDVI
calculate_ndvi(releves, emprise, forest, output_path)
'''