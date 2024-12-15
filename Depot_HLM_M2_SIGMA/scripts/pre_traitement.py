# Ce que chatGPT a fait dans un autre groupe :
'''
import os
from osgeo import gdal

# Dossiers d'entrée et de sortie
input_folder = "data/images"
output_folder = "results/data/img_pretaitees"
os.makedirs(output_folder, exist_ok=True)
output_file = os.path.join(output_folder, "Serie_temp_S2_allbands.tif")

# Récupérer les fichiers d'entrée
image_files = sorted([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(".tif")])

if not image_files:
    raise RuntimeError("Aucun fichier .tif trouvé dans le dossier d'entrée.")

# Charger les dimensions de la première image
first_dataset = gdal.Open(image_files[0])
if not first_dataset:
    raise RuntimeError(f"Impossible d'ouvrir l'image : {image_files[0]}")

height, width = first_dataset.RasterYSize, first_dataset.RasterXSize
geo_transform = first_dataset.GetGeoTransform()
projection = first_dataset.GetProjection()

# Créer le fichier de sortie (format GeoTIFF) sans compression pour l'instant
driver = gdal.GetDriverByName("GTiff")
output_dataset = driver.Create(output_file, width, height, len(image_files), gdal.GDT_Float32, options=["COMPRESS=LZW"])

# Vérifier si la création du fichier a réussi
if not output_dataset:
    raise RuntimeError(f"Impossible de créer le fichier de sortie : {output_file}")

# Appliquer les métadonnées (géoréférencement et projection)
output_dataset.SetGeoTransform(geo_transform)
output_dataset.SetProjection(projection)

# Traiter par lots (10 bandes à la fois)
batch_size = 10
for batch_start in range(0, len(image_files), batch_size):
    batch_end = min(batch_start + batch_size, len(image_files))
    print(f"Traitement du lot {batch_start // batch_size + 1} ({batch_start + 1} à {batch_end})")

    # Empiler les bandes du lot actuel
    for i, image_file in enumerate(image_files[batch_start:batch_end]):
        try:
            print(f"Traitement de la bande {batch_start + i + 1} : {image_file}")
            band_dataset = gdal.Open(image_file)
            
            if not band_dataset:
                raise RuntimeError(f"Impossible d'ouvrir l'image {image_file}")

            # Lire la bande et l'écrire dans le fichier de sortie
            band_array = band_dataset.GetRasterBand(1).ReadAsArray()
            output_dataset.GetRasterBand(batch_start + i + 1).WriteArray(band_array)
            print(f"Bande {batch_start + i + 1} ajoutée depuis {image_file}")
        except Exception as e:
            print(f"Erreur lors du traitement de la bande {batch_start + i + 1} ({image_file}): {e}")
            continue  # Continue avec les bandes suivantes même si une bande échoue

    # Sauvegarder les modifications après chaque lot
    output_dataset.FlushCache()

# Sauvegarder les modifications et fermer le fichier de sortie
output_dataset = None

print(f"Image empilée créée avec succès : {output_file}")


'''