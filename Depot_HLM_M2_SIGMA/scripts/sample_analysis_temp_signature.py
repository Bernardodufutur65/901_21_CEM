# Import des librairies
import geopandas as gpd

# Chemin vers les données en entrée
ECHANTILLONS = "/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp"

# Chargement des données vecteur
gdf_echantillons = gpd.read_file(ECHANTILLONS)

# Sélection des codes correspondant aux classes en gras dans la colonne classif pixel de la figure 2
classes_en_gras = ['12', '13', '14', '23', '24', '25']
# Filtrage des classes dans le champ 'Code'
gdf_classif_pixel_gras = gdf_echantillons[gdf_echantillons["Code"].isin(classes_en_gras)]

# Affichage pour vérifier
# print(gdf_classif_pixel_gras)




# results/figure existe déjà je n'ai plus qu'à écrire les fichiers dedans