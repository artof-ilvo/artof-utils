from rasterio.features import rasterize
from rasterio.transform import from_origin
import numpy as np
from shapely.geometry.base import BaseGeometry

class Raster:
    
    @staticmethod
    def generate_array(geometry: BaseGeometry, bounds: tuple, resolution: float):
        """
        generates a raster array from a Shapely geometry, given the bounds and resolution.
        """
        minx, miny, maxx, maxy = bounds
        
        # calculate the size of the raster in pixels
        width = max(1, int(np.ceil((maxx - minx) / resolution)))
        height = max(1, int(np.ceil((maxy - miny) / resolution)))
        
        # use the West-North origin (left-upper corner))
        transform = from_origin(minx, maxy, resolution, resolution)
        
        # calculate pixels
        raster_array = rasterize(
            [(geometry, 255)], 
            out_shape=(height, width),
            transform=transform,
            fill=1, 
            all_touched=True,  
            dtype='uint8'
        )

        return raster_array, transform, width, height