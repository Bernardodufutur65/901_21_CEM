# Import des bibliothèques personnelles Python
import sys
sys.path.append('/home/onyxia/work/libsigma')

# Import des librairies
import geopandas as gpd

# Chemin vers les données en entrée
FORMATION_VEGETALE = "/home/onyxia/work/data/project/FORMATION_VEGETALE.shp"
EMPRISE_ETUDE = "/home/onyxia/work/data/project/emprise_etude.shp"
MASQUE = "chemin/vers/le/masque"

# Chargement des données
gdf_formation_vegetale = gpd.read_file(FORMATION_VEGETALE)
gdf_emprise_etude = gpd.read_file(EMPRISE_ETUDE)
gdf_masque = gpd.read_file(MASQUE)

# Sélection des entités qui intersectent à la fois l'emprise d'étude et le masque
# Sélection des FV qui intersectent l'emprise d'étude, unary_union permet de combiner les geometries de l'emprise.
gdf_emprise_FV = gdf_formation_vegetale[gdf_formation_vegetale.geometry.intersects(gdf_emprise_etude.unary_union)]
# Inclure les entités qui intersectent aussi le masque
gdf_filtre = gdf_emprise_FV[gdf_emprise_FV.geometry.intersects(gdf_masque.unary_union)]

# Conserver uniquement les colonnes "CODE_TFV" et "TFV" et les renommer
gdf_result = gdf_filtre[["CODE_TFV", "TFV"]].rename(columns={"CODE_TFV": "Code", "TFV": "Nom"})

# Sauvegarder le résultat dans un nouveau fichier shape "Sample_BD_foret_T31TCJ.shp"
output_path = "results/data/sample/Sample_BD_foret_T31TCJ.shp"