
####
import rasterio
from rasterio.features import rasterize
import fiona

def hugo(in_vector, ref_image, out_image, dtype='uint8'):
    """
    Rasterise un fichier vecteur .shp en un fichier raster .tif.

    Parameters
    ----------
    in_vector : str
        Chemin vers le fichier vecteur d'entrée (.shp).
    ref_image : str
        Chemin vers l'image raster de référence pour les dimensions et la géoréférence.
    out_image : str
        Chemin vers le fichier raster de sortie (.tif).
    dtype : str, optional
        Type des données du raster de sortie (par exemple, 'uint8', 'int16').
    """
    # Ouvrir l'image raster de référence pour récupérer les métadonnées
    with rasterio.open(ref_image) as src:
        meta = src.meta.copy()
        transform = src.transform
        width = src.width
        height = src.height
        crs = src.crs
    
    # Configurer les métadonnées du raster de sortie
    meta.update({
        'driver': 'GTiff',
        'dtype': dtype,
        'count': 1,
        'crs': crs,
        'transform': transform,
        'width': width,
        'height': height
    })

    # Charger les entités géométriques du vecteur
    with fiona.open(in_vector, 'r') as vector:
        shapes = [(feature['geometry'], 1) for feature in vector]  # Valeur constante 1 pour toutes les géométries

    # Rasteriser les géométries
    rasterized_data = rasterize(
        shapes=shapes,
        out_shape=(height, width),
        transform=transform,
        dtype=dtype
    )

    # Sauvegarder le raster dans un fichier GeoTIFF
    with rasterio.open(out_image, 'w', **meta) as dst:
        dst.write(rasterized_data, 1)
        print(f"Raster sauvegardé dans {out_image}")

#######