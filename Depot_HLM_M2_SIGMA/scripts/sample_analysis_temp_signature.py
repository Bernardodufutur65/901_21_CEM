# Import des librairies
import geopandas as gpd
import rasterio
import numpy as np
from rasterstats import zonal_stats

# Chemin vers les données en entrée
ECHANTILLONS = "/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp"
NDVI = "/home/onyxia/work/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif"

# Chargement des données vecteur
gdf_echantillons = gpd.read_file(ECHANTILLONS)
# Chargement du NDVI
ndvi_loaded = rasterio.open(NDVI)

# Sélection des codes correspondant aux classes en gras dans la colonne classif pixel de la figure 2
classes_en_gras = ['12', '13', '14', '23', '24', '25']
# Filtrage des classes dans le champ 'Code'
gdf_classif_pixel_gras = gdf_echantillons[gdf_echantillons["Code"].isin(classes_en_gras)]
# print(gdf_classif_pixel_gras)

# Calculer les statistiques zonales
stats = zonal_stats(
    gdf_classif_pixel_gras,
    ndvi_loaded,
    stats=["mean", "std"],
    geojson_out=True,
    nodata=src.nodata  # Exclure les valeurs nodata
)

# Organisation des résultats en GeoDataFrame pour les exploiter plus facilement
results = []
for feature in stats:
    class_code = feature["properties"]["Code"]
    mean_ndvi = feature["properties"]["mean"]
    std_ndvi = feature["properties"]["std"]
    date = feature["properties"]["date"]
    results.append({"Class": class_code, "Date": date, "Mean_NDVI": mean_ndvi, "Std_NDVI": std_ndvi})

# convertir en GeoDataFrame
gdf_ndvi_stats = gpd.DataFrame(results)

# Calculer les moyennes et écarts-types par classe et par date
grouped_stats = df_ndvi_stats.groupby(["Class", "Date"]).agg(
    Mean_NDVI=("Mean_NDVI", "mean"),
    Std_NDVI=("Std_NDVI", "mean")  # Moyenne des écarts-types pour simplifier
).reset_index()

print(grouped_stats)

