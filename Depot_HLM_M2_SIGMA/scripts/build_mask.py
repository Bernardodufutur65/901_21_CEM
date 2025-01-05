import os
import geopandas as gpd

from osgeo import gdal, ogr

# Chemin du dossier à créer
folder_path = '/home/onyxia/work/results/data/img_pretraitees'

# Vérifier si le dossier existe, sinon le créer
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
    print(f"Dossier créé : {folder_path}")
else:
    print(f"Le dossier existe déjà : {folder_path}")

# Chemin des fichiers
my_folder = '/home/onyxia/work/data/project/'
sample_filename = os.path.join(my_folder, 'FORMATION_VEGETALE.shp')
image_filename = '/home/onyxia/work/data/images/SENTINEL2B_20220326-105856-076_L2A_T31TCJ_C_V3-0_FRE_B2.tif'
output_filename = "/home/onyxia/work/results/data/foret.shp"
output_raster_path = "/home/onyxia/work/results/data/img_pretraitees/masque_foret.tif"

# Liste des éléments à exclure
exclude_list = ["LA4", "LA6", "FO", "FF0"]

# Champ à filtrer
field_to_filter = 'CODE_TFV'

try:
    # Charger le shapefile
    if not os.path.exists(sample_filename):
        raise FileNotFoundError(f"Le fichier {sample_filename} est introuvable.")
    
    gdf = gpd.read_file(sample_filename)
    print(f"Fichier chargé : {sample_filename}")
    
    # Filtrer le GeoDataFrame
    gdf_filtered = gdf[~gdf[field_to_filter].str.startswith(tuple(exclude_list), na=False)].copy()
    print(f"Nombre d'éléments après filtrage : {len(gdf_filtered)}")
    
    # Ajouter un champ "forest_zon" avec une valeur de 1
    gdf_filtered['forest_zon'] = 1
    
    # Sauvegarder le GeoDataFrame filtré dans un fichier Shapefile
    gdf_filtered.to_file(output_filename, layer='filtered_data', driver='ESRI Shapefile')
    print(f"Données filtrées sauvegardées dans : {output_filename}")

except FileNotFoundError as e:
    print(f"Erreur : {e}")
except Exception as e:
    print(f"Une erreur s'est produite : {e}")

from osgeo import gdal, ogr
# Charger l'image de référence pour récupérer la résolution et l'emprise
reference_ds = gdal.Open(image_filename)
geotransform = reference_ds.GetGeoTransform()
projection = reference_ds.GetProjection()
x_res = reference_ds.RasterXSize
y_res = reference_ds.RasterYSize
extent = [
    geotransform[0],
    geotransform[3] + y_res * geotransform[5],
    geotransform[0] + x_res * geotransform[1],
    geotransform[3],
]

# Créer un raster vide avec les mêmes dimensions et emprise que l'image de référence
driver = gdal.GetDriverByName('GTiff')
output_raster = driver.Create(
    output_raster_path, x_res, y_res, 1, gdal.GDT_Byte
)
output_raster.SetGeoTransform(geotransform)
output_raster.SetProjection(projection)

# Charger le fichier shapefile en tant que source de données OGR
shapefile_ds = ogr.Open(output_filename)
layer = shapefile_ds.GetLayer()

# Rasteriser la couche
gdal.RasterizeLayer(
    output_raster, [1], layer,
    options=["ATTRIBUTE=forest_zon"]
)

# Assigner une valeur de nodata pour les pixels non couverts
band = output_raster.GetRasterBand(1)
band.SetNoDataValue(0)

# Nettoyer les objets
band.FlushCache()
output_raster.FlushCache()
output_raster = None
shapefile_ds = None
reference_ds = None

print(f"Raster généré avec succès : {output_raster_path}")


'''
from osgeo import gdal, ogr

# Charger l'image de référence pour récupérer la résolution et l'emprise
try:
    reference_ds = gdal.Open(image_filename)
    if reference_ds is None:
        raise FileNotFoundError(f"Impossible d'ouvrir le fichier d'image : {image_filename}")

    geotransform = reference_ds.GetGeoTransform()
    projection = reference_ds.GetProjection()
    x_res = reference_ds.RasterXSize
    y_res = reference_ds.RasterYSize
    extent = [
        geotransform[0],
        geotransform[3] + y_res * geotransform[5],
        geotransform[0] + x_res * geotransform[1],
        geotransform[3],
    ]
    print("Image de référence chargée avec succès.")

    # Créer un raster vide avec les mêmes dimensions et emprise que l'image de référence
    driver = gdal.GetDriverByName('GTiff')
    output_raster = driver.Create(
        output_raster_path, x_res, y_res, 1, gdal.GDT_Byte
    )
    output_raster.SetGeoTransform(geotransform)
    output_raster.SetProjection(projection)
    print("Raster vide créé avec succès.")
    
    # Charger le fichier shapefile en tant que source de données OGR
    shapefile_ds = ogr.Open(output_filename)
    if shapefile_ds is None:
        raise FileNotFoundError(f"Impossible d'ouvrir le shapefile : {output_filename}")

    layer = shapefile_ds.GetLayer()
    print("Shapefile chargé avec succès.")

    # Rasteriser la couche
    gdal.RasterizeLayer(
        output_raster, [1], layer,
        options=["ATTRIBUTE=forest_zon"]
    )
    print("Rasterisation complétée avec succès.")

    # Assigner une valeur de nodata pour les pixels non couverts
    band = output_raster.GetRasterBand(1)
    band.SetNoDataValue(0)
    print("Valeur NoData assignée.")

except FileNotFoundError as e:
    print(f"Erreur : {e}")
except Exception as e:
    print(f"Une erreur s'est produite : {e}")
finally:
    # Nettoyer les objets pour libérer la mémoire
    if 'band' in locals():
        band.FlushCache()
    if 'output_raster' in locals():
        output_raster.FlushCache()
        output_raster = None
    if 'shapefile_ds' in locals():
        shapefile_ds = None
    if 'reference_ds' in locals():
        reference_ds = None

print(f"Raster généré avec succès : {output_raster_path}")
'''