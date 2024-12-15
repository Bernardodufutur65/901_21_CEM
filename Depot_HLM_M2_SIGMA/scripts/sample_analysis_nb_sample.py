import os
import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import rasterio
import seaborn as sns

from rasterio.mask import mask


# chemin du dossier de sortie à créer
folder_path = '/home/onyxia/work/results/figure'
# Vérifier si le dossier existe, sinon le créer
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
    print(f"Dossier créé : {folder_path}")
else:
    print(f"Le dossier existe déjà : {folder_path}")

# Chemin du fichier shapefile
shapefile_path = "/home/onyxia/work/results/data/sample/Sample_BD_foret_T31TCJ.shp"

# Charger le fichier shapefile
gdf = gpd.read_file(shapefile_path)

# Vérifier la colonne "classif pixel"
if "Code" not in gdf.columns:
    raise ValueError("La colonne 'Code' n'existe pas dans le fichier shapefile.")

# Diagramme 1 : Codebre de polygones par classe
polygons_by_class = gdf["Code"].value_counts()

# Produire un diagramme en bâton
plt.figure(figsize=(10, 6))
polygons_by_class.plot(kind="bar", color="skyblue")
plt.title("Histogramme du nombre de polygones par classe ")
plt.xlabel("Classe")
plt.ylabel("Nbs de polygones")
plt.xticks(rotation=45)
plt.tight_layout(pad=2)
plt.savefig("/home/onyxia/work/results/figure/diag_baton_nb_poly_by_class.png")
plt.show()
plt.close()


print("Diagramme du Codebre de polygones par classe enregistré : diag_baton_nb_poly_by_class.png")



# Diagramme 2 : Nombre de pixels par classe
# Chemins des fichiers
raster_path = "/home/onyxia/work/results/data/img_pretraitees/masque_foret.tif"
output_raster_path = "/home/onyxia/work/results/data/nb_pixel.tif"  # Temporaire pour calculer les pixels

# Charger le shapefile avec Geopandas
gdf = gpd.read_file(shapefile_path)

# Vérifier le CRS du shapefile
print("CRS du shapefile :", gdf.crs)

# Vérifier le CRS du raster
with rasterio.open(raster_path) as src:
    print("CRS du raster :", src.crs)

# Si les CRS sont différents, reprojetez le shapefile au CRS du raster
if gdf.crs != src.crs:
    gdf = gdf.to_crs(src.crs)

# Charger le raster avec Rasterio
with rasterio.open(raster_path) as src:
    raster_data = src.read(1)  # Lecture de la première bande
    affine = src.transform

    # Préparer une liste pour les résultats
    results = []

    # Parcourir chaque polygone du shapefile
    for _, row in gdf.iterrows():
        # Extraire le polygone
        geom = [row['geometry'].__geo_interface__]
        code = row['Code']  # Remplacez 'CODE' par le champ correspondant dans votre shapefile

        # Masquer le raster avec le polygone
        out_image, out_transform = mask(src, geom, crop=True)
        out_image = out_image[0]  # Extraire la première bande

        # Trouver les pixels ayant la valeur 1
        pixel_count = np.sum(out_image == 1)

        # Sauvegarder le résultat
        results.append({"code": code, "pixel_count": pixel_count})

# Afficher les résultats
for result in results:
    print(f"Code: {result['code']}, Pixels avec valeur 1: {result['pixel_count']}")


# Créer un DataFrame à partir des résultats
results_df = pd.DataFrame(results)

# Grouper les pixels par classe (code) et calculer la somme des pixels
pixels_by_class = results_df.groupby("code")["pixel_count"].sum()

# Trier par ordre croissant du nombre de pixels
pixels_by_class = pixels_by_class.sort_values(ascending=False)

# Tracer un histogramme
plt.figure(figsize=(10, 6))
pixels_by_class.plot(kind="bar", color="lightcoral")
plt.title("Histogramme du nombre de pixels par classe")
plt.xlabel("Classe")
plt.ylabel("Nombre de pixels x10^6")
plt.xticks(rotation=45)
plt.tight_layout()
# Sauvegarder le graphique avant de fermer
plt.savefig("/home/onyxia/work/results/figure/diag_baton_nb_pix_by_class.png")
plt.show()

# Fermer la figure pour éviter des conflits
plt.close()

print("Diagramme du nombre de polygones par classe enregistré : diag_baton_nb_pix_by_class.png")



# Créer un DataFrame à partir des résultats
results_df = pd.DataFrame(results)

# Grouper les pixels par classe pour avoir le total par classe
class_totals = results_df.groupby("code")["pixel_count"].sum().reset_index()

# Violin Plot basé sur les totaux par classe
plt.figure(figsize=(12, 8))
sns.violinplot(x="code", y="pixel_count", data=class_totals, scale="width", inner="quartile", palette="pastel")

# Ajuster les titres et les étiquettes
plt.title("Distribution des pixels totaux par classe", fontsize=14)
plt.xlabel("Classe", fontsize=12)
plt.ylabel("Nombre total de pixels", fontsize=12)
plt.xticks(rotation=45)


# Sauvegarder l'image
plt.tight_layout()
plt.savefig("/home/onyxia/work/results/figure/violin_plot_nb_pix_by_poly_by_class.png")
plt.show()

# logarithm
results_df["log_pixel_count"] = np.log1p(results_df["pixel_count"])
plt.figure(figsize=(12, 8))
sns.violinplot(x="code", y="log_pixel_count", data=results_df, scale="width", inner="quartile", palette="pastel")

plt.title("Distribution logarithmique du nombre de pixels par polygone et par classe", fontsize=14)
plt.xlabel("Classe", fontsize=12)
plt.ylabel("Log(Nombre de pixels)", fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("/home/onyxia/work/results/figure/violin_plot_but_with_logarithm.png")
plt.show()


# print(results_df.groupby("code")["pixel_count"].describe())
