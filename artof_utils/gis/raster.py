from rasterio.features import rasterize
from rasterio.transform import from_origin
import numpy as np
from shapely.geometry.base import BaseGeometry

class Raster:
    
    @staticmethod
    def generate_array(geometry: BaseGeometry, bounds: tuple, resolution: float):
        """
        Berekent een raster (pixel-matrix) op basis van een Shapely geometrie en bounds.
        Geeft de numpy array en de transformatiematrix terug. Geen File I/O!
        """
        minx, miny, maxx, maxy = bounds
        
        # Bereken de grootte van het raster in pixels
        width = max(1, int(np.ceil((maxx - minx) / resolution)))
        height = max(1, int(np.ceil((maxy - miny) / resolution)))
        
        # Gebruik de West-North origin (linksboven)
        transform = from_origin(minx, maxy, resolution, resolution)
        
        # Bereken de pixels
        raster_array = rasterize(
            [(geometry, 255)], # 255 (wit) voor de actieve gebieden
            out_shape=(height, width),
            transform=transform,
            fill=0,
            all_touched=True,  # Zorgt dat dunne lijnen/punten zichtbaar zijn
            dtype='uint8'
        )

        return raster_array, transform, width, height