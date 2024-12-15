# Import des librairies
import geopandas as gpd
import os

# Chemin vers les données en entrée
FORMATION_VEGETALE = "/home/onyxia/work/data/project/FORMATION_VEGETALE.shp"
EMPRISE_ETUDE = "/home/onyxia/work/data/project/emprise_etude.shp"
# Couche vecteur contenant les classes de la figure 2 (sont exclus les codes : LA4, LA6, FO et FF0)
MASQUE = "/home/onyxia/work/results/data/foret.shp"

# Chargement des données vecteur
gdf_formation_vegetale = gpd.read_file(FORMATION_VEGETALE)
gdf_emprise_etude = gpd.read_file(EMPRISE_ETUDE)
gdf_masque = gpd.read_file(MASQUE)

# Sélection des entités qui intersectent à la fois l'emprise d'étude et le masque
# Sélection des FV qui intersectent l'emprise d'étude ; unary_union permet de combiner les géometries de l'emprise.
gdf_FV_intersect_emprise = gdf_formation_vegetale[gdf_formation_vegetale.geometry.intersects(gdf_emprise_etude.unary_union)]
# Inclure les entités qui intersectent aussi le masque
gdf_intersect_emprise_masque_FV = gdf_FV_intersect_emprise[gdf_FV_intersect_emprise.geometry.intersects(gdf_masque.unary_union)]

# Création des champs "Nom" et "Code" grâce aux colonnes "Nom" et "Code" de la figure 2.
# Création d'un dictionnaire correspondant aux valeurs du champ "TFV" rapportées à deux nouveaux champs "Nom" et "Code"
classif_objet = {
    "Forêt fermée d’un autre feuillu pur": ("Autres feuillus", "11"),
    "Forêt fermée de châtaignier pur": ("Autres feuillus", "11"),
    "Forêt fermée de hêtre pur": ("Autres feuillus", "11"),
    "Forêt fermée de chênes décidus purs": ("Chêne", "12"),
    "Forêt fermée de robinier pur": ("Robinier", "13"),
    "Peupleraie": ("Peupleraie", "14"),
    "Forêt fermée à mélange de feuillus": ("Mélange de feuillus", "15"),
    "Forêt fermée de feuillus purs en îlots": ("Feuillus en îlots", "16"),
    "Forêt fermée d’un autre conifère pur autre que pin ": ("Autre conifère que pin", "21"),
    "Forêt fermée de mélèze pur": ("Autre conifère que pin", "21"),
    "Forêt fermée de sapin ou épicéa": ("Autre conifère que pin", "21"),
    "Forêt fermée à mélange d’autres conifères": ("Autre conifère que pin", "21"),
    "Forêt fermée d’un autre pin pur": ("Autre pin", "22"),
    "Forêt fermée de pin sylvestre pur": ("Autre pin", "22"),
    "Forêt fermée à mélange de pins purs": ("Autre pin", "22"),
    "Forêt fermée de douglas pur": ("Douglas", "23"),
    "Forêt fermée de pin laricio ou pin noir pur": ("Pin laricio ou pin noir", "24"),
    "Forêt fermée de pin maritime pur": ("Pin maritime", "25"),
    "Forêt fermée à mélange de conifères": ("Mélange conifères", "26"),
    "Forêt fermée de conifères purs en îlots": ("Conifères en ilots", "27"),
    "Forêt fermée à mélange de conifères prépondérants et feuillus": ("Mélange de conifères prépondérants et feuillus", "28"),
    "Forêt fermée à mélange de feuillus prépondérants et conifères": ("Mélange de feuillus prépondérants et conifères", "29")
}

# Création des champs "Nom" et "Code" si non existants
if "Nom" not in gdf_intersect_emprise_masque_FV.columns:
    gdf_intersect_emprise_masque_FV["Nom"] = None
if "Code" not in gdf_intersect_emprise_masque_FV.columns:
    gdf_intersect_emprise_masque_FV["Code"] = None

# Mise à jour des champs "Nom" et "Code"
def update_fields(row):
    tfv_value = row["TFV"]
    if tfv_value in classif_objet:
        row["Nom"], row["Code"] = classif_objet[tfv_value]
    return row

gdf_intersect_emprise_masque_FV = gdf_intersect_emprise_masque_FV.apply(update_fields, axis=1)

#print(gdf_intersect_emprise_masque_FV)

# Sauvegarder le résultat dans un nouveau fichier shape "Sample_BD_foret_T31TCJ.shp"
# chemin de sortie
output_path = "/home/onyxia/work//data/sampleZ/Sample_BD_foret_T31TCJ.shp"
# Création du répertoire parent
output_dir = os.path.dirname(output_path)
os.makedirs(output_dir, exist_ok=True)
# sauvegarde du gdf dans un shp
gdf_intersect_emprise_masque_FV.to_file(output_path)

print(f"Mise à jour terminée et fichier sauvegardé à : {output_path}")