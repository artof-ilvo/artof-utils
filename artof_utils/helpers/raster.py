import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
import numpy as np
import os
from shapely.geometry import shape, MultiPoint, Polygon, LineString
from shapely.ops import unary_union
import geopandas as gpd

class Raster:
    
    @staticmethod
    def create_geotiff(geometry, bounds, resolution, output_path, crs):
        minx, miny, maxx, maxy = bounds
        
        width = max(1, int(np.ceil((maxx - minx) / resolution)))
        height = max(1, int(np.ceil((maxy - miny) / resolution)))
        
        # Gebruik de West-North origin
        transform = from_origin(minx, maxy, resolution, resolution)
        
        try:
            raster = rasterize(
                [(geometry, 255)], # Gebruik 255 (wit) ipv 1 voor visuele controle!
                out_shape=(height, width),
                transform=transform,
                fill=0,
                all_touched=True,  # Zorgt dat dunne lijnen/punten zichtbaar zijn
                dtype='uint8'
            )

            with rasterio.open(
                output_path, 'w',
                driver='GTiff',
                height=height, width=width,
                count=1, dtype='uint8',
                crs=crs,
                transform=transform
            ) as dst:
                dst.write(raster, 1)
                
            print(f"[Raster] Saved {output_path} ({width}x{height}) - Max val: {np.max(raster)}")
        except Exception as e:
            print(f"Error creating GeoTIFF: {e}")