import sys
sys.path.append('/libsigma')

import os
import geopandas as gpd


from osgeo import gdal
import numpy as np
import subprocess



def rasterization(in_vector, ref_image, out_image, field_name, dtype=None):
    """
    See otbcli_rasterisation for details on parameters
    """
    if dtype is not None :
        field_name = field_name + ' ' + dtype
    # define commande
    cmd_pattern = (
        "otbcli_Rasterization -in {in_vector} -im {ref_image} -out {out_image}"
        " -mode attribute -mode.attribute.field {field_name}")
    cmd = cmd_pattern.format(in_vector=in_vector, ref_image=ref_image,
                             out_image=out_image, field_name=field_name)
    print(cmd)

    # pour python >= 3.7
    result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    print(result.decode())




# inputs
my_folder = '/home/onyxia/work/data/project/'
sample_filename = os.path.join(my_folder, 'FORMATION_VEGETALE.shp')
image_filename = ('/home/onyxia/work/data/images/SENTINEL2B_20220326-105856-076_L2A_T31TCJ_C_V3-0_FRE_B2.tif')
output_filename = "/test.shp"
output_raster_path = "/home/onyxia/work/data/project/test.tif"

# Liste des éléments à exclure
exclude_list = ["LA4", "LA6", "FO", "FF0"]

# Champ à filtrer (à ajuster selon le shapefile)
field_to_filter = 'CODE_TFV'  # Remplace 'CODE' par le nom réel du champ

# Charger le shapefile
gdf = gpd.read_file(sample_filename)

# Filtrer le GeoDataFrame en excluant les valeurs commençant par les préfixes de la liste
gdf_filtered = gdf[~gdf[field_to_filter].str.startswith(tuple(exclude_list), na=False)]

# Ajouter un champ "forest_zone" avec une valeur de 1 pour tous les éléments filtrés
gdf_filtered['forest_zone'] = 1

# Sauvegarder le GeoDataFrame filtré dans un fichier GeoPackage
gdf_filtered.to_file(my_folder + output_filename, layer='filtered_data', driver='ESRI Shapefile')



rasterization(
    in_vector="/home/onyxia/work/data/project/test.shp",
    ref_image="/home/onyxia/work/data/images/SENTINEL2B_20220326-105856-076_L2A_T31TCJ_C_V3-0_FRE_B2.tif",
    out_image="901_21_CEM/Depot_HLM_M2_SIGMA/results/data/img_pretraitees/masque_foret.tif",
    field_name="forest_zone",
    dtype="uint8"  # Assure l'encodage en 8 bits
)