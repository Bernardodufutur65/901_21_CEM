import os
import geopandas as gpd
import matplotlib.pyplot as plt

# Chemin du fichier shapefile
shapefile_path = "/home/onyxia/work/results/data/foret.shp"

# Charger le fichier shapefile
gdf = gpd.read_file(shapefile_path)

# Vérifier la colonne "classif pixel"
if "CODE_TFV" not in gdf.columns:
    raise ValueError("La colonne 'CODE_TFV' n'existe pas dans le fichier shapefile.")

# Diagramme 1 : Nombre de polygones par classe
polygons_by_class = gdf["CODE_TFV"].value_counts()

# Produire un diagramme en bâton
plt.figure(figsize=(10, 6))
polygons_by_class.plot(kind="bar", color="skyblue")
plt.title("Nombre de polygones par classe")
plt.xlabel("Classe")
plt.ylabel("Nombre de polygones")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

plt.savefig("diag_baton_nb_poly_by_class.png")
plt.close()

print("Diagramme du nombre de polygones par classe enregistré : diag_baton_nb_poly_by_class.png")

# Diagramme 2 : Nombre de pixels par classe
# Supposons que chaque polygone a un champ "pixel_count" indiquant son nombre de pixels
if "pixel_count" not in gdf.columns:
    raise ValueError("La colonne 'pixel_count' est nécessaire pour calculer le nombre de pixels par classe.")

pixels_by_class = gdf.groupby("classif pixel")["pixel_count"].sum()

# Produire un diagramme en bâton
plt.figure(figsize=(10, 6))
pixels_by_class.plot(kind="bar", color="lightcoral")
plt.title("Nombre de pixels par classe")
plt.xlabel("Classe")
plt.ylabel("Nombre de pixels")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("diag_baton_nb_pix_by_class.png")
plt.close()

print("Diagramme du nombre de pixels par classe enregistré : diag_baton_nb_pix_by_class.png")




import os
import geopandas as gpd
from osgeo import gdal, ogr
import numpy as np
import matplotlib.pyplot as plt

# Chemins des fichiers
shapefile_path = "/home/onyxia/work/results/data/foret.shp"
raster_path = "/home/onyxia/work/results/data/img_pretraitees/masque_foret.tif"
output_raster_path = "/home/onyxia/work/results/data/nb_pixel.tif"  # Temporaire pour calculer les pixels

# Charger le shapefile
gdf = gpd.read_file(shapefile_path)

# Vérifier la colonne "classif pixel"
if "CODE_TFV" not in gdf.columns:
    raise ValueError("La colonne 'CODE_TFV' n'existe pas dans le fichier shapefile.")

# Charger le raster pour récupérer les métadonnées
raster_ds = gdal.Open(raster_path)
geo_transform = raster_ds.GetGeoTransform()
projection = raster_ds.GetProjection()
x_res = raster_ds.RasterXSize
y_res = raster_ds.RasterYSize

# Créer un raster temporaire pour rasteriser les polygones
driver = gdal.GetDriverByName("GTiff")
rasterized_ds = driver.Create(output_raster_path, x_res, y_res, 1, gdal.GDT_UInt32)
rasterized_ds.SetGeoTransform(geo_transform)
rasterized_ds.SetProjection(projection)

# Charger le shapefile comme couche OGR
shapefile_ds = ogr.Open(shapefile_path)
layer = shapefile_ds.GetLayer()

# Ajouter un identifiant unique à chaque polygone
for i, feature in enumerate(layer):
    feature.SetField("id", i + 1)
    layer.SetFeature(feature)

# Rasteriser la couche
gdal.RasterizeLayer(
    rasterized_ds, [1], layer, options=["ATTRIBUTE=id"]
)
rasterized_ds.FlushCache()

# Lire le rasterisé comme un tableau numpy
rasterized_band = rasterized_ds.GetRasterBand(1)
rasterized_array = rasterized_band.ReadAsArray()

# Calculer le nombre de pixels pour chaque polygone
pixel_counts = {}
unique_ids = np.unique(rasterized_array)
unique_ids = unique_ids[unique_ids > 0]  # Ignorer les pixels de fond (valeur 0)

for poly_id in unique_ids:
    pixel_counts[poly_id] = np.sum(rasterized_array == poly_id)

# Ajouter les nombres de pixels au GeoDataFrame
gdf["pixel_count"] = gdf.index.map(pixel_counts)

# Supprimer le fichier raster temporaire
rasterized_ds = None
os.remove(output_raster_path)

# Diagramme : Nombre de pixels par classe
pixels_by_class = gdf.groupby("CODE_TFV")["pixel_count"].sum()

plt.figure(figsize=(10, 6))
pixels_by_class.plot(kind="bar", color="lightcoral")
plt.title("Nombre de pixels par classe")
plt.xlabel("Classe")
plt.ylabel("Nombre de pixels")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

print("Diagramme du nombre de pixels par classe affiché.")
