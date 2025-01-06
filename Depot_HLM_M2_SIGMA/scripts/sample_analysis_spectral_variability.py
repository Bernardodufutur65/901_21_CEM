import geopandas as gpd
import rasterio

sample_file = '/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp'  # échantillons
ndvi_file = '/home/onyxia/work/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif'  # ndvi

# Chargement des données
gdf_echantillons = gpd.read_file(sample_file)  # Données vecteur
ndvi_loaded = rasterio.open(ndvi_file)  # Données NDVI raster


########## 1. À l'échelle de l'image entière, tous polygones confondus ##########


########## 2. À l'échelle de chaque polygone ##########
# Sélection des codes correspondant aux classes en rouge dans la colonne classif objet de la figure 2
classes_rouges = ['11', '12', '13', '14', '23', '24', '25']
# Filtrage des classes dans le champ 'Code'
gdf_classes_rouges = gdf_echantillons[gdf_echantillons["Code"].isin(classes_rouges)]

# Sélection des codes correspondant aux classes en bleu dans la colonne classif objet de la figure 2
classes_bleues = ['15', '26', '28', '29']
# Filtrage des classes dans le champ 'Code'
gdf_classes_bleues = gdf_echantillons[gdf_echantillons["Code"].isin(classes_bleues)]

#print(gdf_classes_bleues)
print(gdf_classes_rouges)

