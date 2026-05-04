import numpy as np
from unittest import TestCase
from shapely.geometry import Polygon

# Importeer onze nieuwe, stateless Raster klasse
from artof_utils.gis.raster import Raster

class TestRaster(TestCase):
    
    def test_generate_array_dimensions_and_pixels(self):
        """Test of de dimensies en de numpy array correct berekend worden."""
        
        # 1. ARRANGE: Maak een vierkant van 10x10 meter
        poly = Polygon([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]])
        
        # We nemen de bounds iets ruimer (-1 tot 11) zodat we lege zwarte randen krijgen
        # Volgorde is (minx, miny, maxx, maxy)
        bounds = (-1.0, -1.0, 11.0, 11.0)
        
        # 1 pixel is 1 vierkante meter
        resolutie = 1.0  

        # 2. ACT: Laat de utils het raster berekenen (geen File I/O!)
        pixels, transform, width, height = Raster.generate_array(
            geometry=poly, 
            bounds=bounds, 
            resolution=resolutie
        )

        # 3. ASSERTS: Kloppen de afmetingen?
        # Formule was: (maxx - minx) / resolutie -> (11 - (-1)) / 1 = 12 pixels breed
        self.assertEqual(width, 12)
        self.assertEqual(height, 12)
        self.assertEqual(pixels.shape, (12, 12))

        # 4. ASSERTS: Kloppen de pixel-waardes?
        # Datatype moet uint8 zijn voor afbeeldingen
        self.assertEqual(pixels.dtype, np.uint8)
        
        # Er moeten pixels "aan" staan (255) in het midden
        self.assertEqual(np.max(pixels), 255)
        
        # Er moeten pixels "uit" staan (0) in de lege rand
        self.assertEqual(np.min(pixels), 0)

        # 5. ASSERTS: Transform matrix check
        # De origin (linksboven) van de transform moet starten op minx (-1.0) en maxy (11.0)
        self.assertEqual(transform.c, -1.0) # c = x origin
        self.assertEqual(transform.f, 11.0) # f = y origin