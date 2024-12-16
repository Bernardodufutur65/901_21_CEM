import geopandas as gpd

ECHANTILLONS = "/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp"

# Chargement des données vecteur
gdf_echantillons = gpd.read_file(ECHANTILLONS)

# Sélection des codes correspondant aux classes en rouge dans la colonne classif objet de la figure 2
classes_rouges = ['11', '12', '13', '14', '23', '24', '25']
# Filtrage des classes dans le champ 'Code'
gdf_classes_rouges = gdf_echantillons[gdf_echantillons["Code"].isin(classes_rouges)]

# Sélection des codes correspondant aux classes en bleu dans la colonne classif objet de la figure 2
classes_bleues = ['15', '26', '28', '29']
# Filtrage des classes dans le champ 'Code'
gdf_classes_bleues = gdf_echantillons[gdf_echantillons["Code"].isin(classes_bleues)]

#print(gdf_classes_bleues)
#print(gdf_classes_rouges)

