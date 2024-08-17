from unittest import TestCase
from artof_utils.shapefile import Shapefile, GeomType
from os import path
import numpy as np


class TestShapefile(TestCase):
    def test_init_empty_shapefile(self):
        # Arrange
        folder_path = path.join(path.dirname(__file__), 'files', 'shapefile', 'empty_new')
        # Act
        shapefile = Shapefile(folder_path)
        # Assert
        self.assertTrue(path.exists(shapefile.file_path))

    def test_context_linestring(self):
        # Arrange
        folder_path = path.join(path.dirname(__file__), 'files', 'shapefile', 'linestring')
        shapefile = Shapefile(folder_path)
        ref_points = np.array([[[0.0, 0.0], [0.0, 100.00], [100.0, 100.0], [100.0, 0.0]]])
        # Act
        context = shapefile.context
        # Assert
        self.assertEqual(context['wkid'], 32631)
        self.assertEqual(context['hasZ'], False)
        self.assertTrue(np.array(context['paths']).shape == np.array(context['latlng']).shape)
        self.assertTrue(np.allclose(ref_points, np.array(context['paths'])))

    def test_context_polygon(self):
        # Arrange
        folder_path = path.join(path.dirname(__file__), 'files', 'shapefile', 'polygon')
        shapefile = Shapefile(folder_path)
        ref_points = np.array([[[0.0, 0.0], [0.0, 100.00], [100.0, 100.0], [100.0, 0.0], [0.0, 0.0]]])
        # Act
        context = shapefile.context
        # Assert
        self.assertEqual(context['wkid'], 32631)
        self.assertEqual(context['hasZ'], False)
        self.assertTrue(np.array(context['rings']).shape == np.array(context['latlng']).shape)
        self.assertTrue(np.allclose(ref_points, np.array(context['rings'][0])))

    def test_context_polygons(self):
        # Arrange
        folder_path = path.join(path.dirname(__file__), 'files', 'shapefile', 'polygons')
        shapefile = Shapefile(folder_path)
        ref_points = np.array([[[0.0, 0.0], [0.0, 100.00], [100.0, 100.0], [100.0, 0.0], [0.0, 0.0]]])
        # Act
        context = shapefile.context
        # Assert
        self.assertEqual(context['wkid'], 32631)
        self.assertEqual(context['hasZ'], False)
        self.assertTrue(np.allclose(ref_points, np.array(context['rings'][0])))
        self.assertEqual(len(context['rings']), 3)
        self.assertEqual(len(context['latlng']), 3)

    def test_context_points(self):
        # Arrange
        folder_path = path.join(path.dirname(__file__), 'files', 'shapefile', 'points')
        shapefile = Shapefile(folder_path)
        ref_points = np.array([[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.00]])
        # Act
        context = shapefile.context
        # Assert
        self.assertEqual(context['wkid'], 32631)
        self.assertEqual(context['hasZ'], False)
        self.assertTrue(np.allclose(ref_points, np.array(context['points'])))
        self.assertTrue(np.array(context['points']).shape == np.array(context['latlng']).shape)

    def test_context_multipoints(self):
        # Arrange
        folder_path = path.join(path.dirname(__file__), 'files', 'shapefile', 'multipoints')
        shapefile = Shapefile(folder_path)
        ref_points = np.array([[0.0, 0.0], [0.0, 100.00], [100.0, 100.0], [100.0, 0.0]])
        # Act
        context = shapefile.context
        # Assert
        self.assertEqual(context['wkid'], 32631)
        self.assertEqual(context['hasZ'], False)
        self.assertTrue(np.allclose(ref_points, np.array(context['points'])))
        self.assertTrue(np.array(context['points']).shape == np.array(context['latlng']).shape)

    def test_context_multipoints2(self):
        # Arrange
        folder_path = path.join(path.dirname(__file__), 'files', 'shapefile', 'multipoints2')
        shapefile = Shapefile(folder_path)
        # Act
        context = shapefile.context
        # Assert
        self.assertEqual(context['wkid'], 32631)
        self.assertEqual(context['hasZ'], False)

    def test_new_polygon(self):
        # Arrange
        coords_1 = [[[0.0, 0.0], [0.0, 100.00], [100.0, 100.0], [100.0, 0.0]]]
        coords_2 = np.array([[0.0, 0.0], [0.0, 100.00], [100.0, 100.0]])
        coords_3 = [[[0.0, 0.0], [0.0, 100.00], [100.0, 100.0], [100.0, 0.0], [0.0, 0.0]]]
        coords_4 = [coords_1[0], coords_2, coords_3[0]]
        coords_1_ref = np.array([[[0.0, 0.0], [0.0, 100.00], [100.0, 100.0], [100.0, 0.0], [0.0, 0.0]]])
        coords_2_ref = np.array([[[0.0, 0.0], [0.0, 100.00], [100.0, 100.0], [0.0, 0.0]]])
        coords_3_ref = np.array([[[0.0, 0.0], [0.0, 100.00], [100.0, 100.0], [100.0, 0.0], [0.0, 0.0]]])
        coords_4_ref = [coords_3_ref[0], coords_2_ref[0], coords_3_ref[0]]
        folder_path_1 = path.join(path.dirname(__file__), 'files', 'shapefile', 'polygon1_new')
        folder_path_2 = path.join(path.dirname(__file__), 'files', 'shapefile', 'polygon2_new')
        folder_path_3 = path.join(path.dirname(__file__), 'files', 'shapefile', 'polygon3_new')
        folder_path_4 = path.join(path.dirname(__file__), 'files', 'shapefile', 'polygon4_new')
        # Act
        shapefile_1 = Shapefile(folder_path_1)
        shapefile_2 = Shapefile(folder_path_2)
        shapefile_3 = Shapefile(folder_path_3)
        shapefile_4 = Shapefile(folder_path_4)
        shapefile_1.update(coords_1, GeomType.POLYGON)
        shapefile_2.update(coords_2, GeomType.POLYGON)
        shapefile_3.update(coords_3, GeomType.POLYGON)
        shapefile_4.update(coords_4, GeomType.POLYGON)
        # Assert
        self.assertEqual(shapefile_1.context['wkid'], 32631)
        self.assertEqual(shapefile_2.context['wkid'], 32631)
        self.assertEqual(shapefile_3.context['wkid'], 32631)
        self.assertEqual(shapefile_4.context['wkid'], 32631)
        self.assertTrue(path.exists(shapefile_1.file_path))
        self.assertTrue(path.exists(shapefile_2.file_path))
        self.assertTrue(path.exists(shapefile_3.file_path))
        self.assertTrue(path.exists(shapefile_4.file_path))
        self.assertTrue(np.allclose(coords_1_ref, np.array(shapefile_1.context['rings'])))
        self.assertTrue(np.allclose(coords_2_ref, np.array(shapefile_2.context['rings'])))
        self.assertTrue(np.allclose(coords_3_ref, np.array(shapefile_3.context['rings'])))
        self.assertTrue(np.array(shapefile_1.context['rings']).shape == np.array(shapefile_1.context['latlng']).shape)
        self.assertTrue(np.array(shapefile_2.context['rings']).shape == np.array(shapefile_2.context['latlng']).shape)
        self.assertTrue(np.array(shapefile_3.context['rings']).shape == np.array(shapefile_3.context['latlng']).shape)

        for i in range(len(coords_4_ref)):
            self.assertTrue(np.allclose(coords_4_ref[i], np.array(shapefile_4.context['rings'][i])))

    def test_new_linestring(self):
        # Arrange
        coords_1 = np.array([[[0.0, 0.0], [0.0, 100.00], [100.0, 100.0]]])
        coords_2 = [[0.0, 0.0], [0.0, 100.00], [100.0, 100.0]]
        folder_path_1 = path.join(path.dirname(__file__), 'files', 'shapefile', 'linestring1_new')
        folder_path_2 = path.join(path.dirname(__file__), 'files', 'shapefile', 'linestring2_new')
        coords_1_ref = coords_1
        coords_2_ref = coords_1
        # Act
        shapefile_1 = Shapefile(folder_path_1)
        shapefile_2 = Shapefile(folder_path_2)
        shapefile_1.update(coords_1, GeomType.LINESTRING)
        shapefile_2.update(coords_2, GeomType.LINESTRING)
        # Assert
        self.assertEqual(shapefile_1.context['wkid'], 32631)
        self.assertEqual(shapefile_2.context['wkid'], 32631)
        self.assertTrue(path.exists(shapefile_1.file_path))
        self.assertTrue(path.exists(shapefile_2.file_path))
        self.assertTrue(np.allclose(coords_1_ref, np.array(shapefile_1.context['paths'])))
        self.assertTrue(np.allclose(coords_2_ref, np.array(shapefile_2.context['paths'])))
        self.assertTrue(np.array(shapefile_1.context['paths']).shape == np.array(shapefile_1.context['latlng']).shape)
        self.assertTrue(np.array(shapefile_2.context['paths']).shape == np.array(shapefile_2.context['latlng']).shape)

    def test_new_points(self):
        # Arrange
        coords_1 = [[0.0, 0.0], [0.0, 100.00], [100.0, 100.0]]
        folder_path_1 = path.join(path.dirname(__file__), 'files', 'shapefile', 'points1_new')
        # Act
        shapefile_1 = Shapefile(folder_path_1)
        shapefile_1.update(coords_1, GeomType.POINT)
        # Assert
        self.assertEqual(shapefile_1.context['wkid'], 32631)
        self.assertTrue(path.exists(shapefile_1.file_path))
        self.assertTrue(np.allclose(coords_1, np.array(shapefile_1.context['points'])))
        self.assertTrue(np.array(shapefile_1.context['points']).shape == np.array(shapefile_1.context['latlng']).shape)

    def test_shapefile_empty(self):
        # Arrange
        folder_path = path.join(path.dirname(__file__), 'files', 'shapefile', 'empty')
        # Act
        shapefile = Shapefile(folder_path)
        # Assert
        self.assertEqual(shapefile.context['empty'], True)

    def test_update_latlng(self):
        # Arrange
        folder_path = path.join(path.dirname(__file__), 'files', 'shapefile', 'traject_latlng_new')
        shapefile = Shapefile(folder_path)
        data_utm = [[[554356.9501732234, 5647897.73942658], [554304.8298267765, 5647995.610573417],
                     [554306.4898267768, 5647996.4905734155], [554358.6101732232, 5647898.619426582],
                     [554359.8901732232, 5647899.289426582], [554307.7698267768, 5647997.160573415],
                     [554309.0898267763, 5647997.870573415], [554361.2101732236, 5647899.999426585],
                     [554362.5401732236, 5647900.699426582], [554310.4198267765, 5647998.570573414],
                     [554311.7398267763, 5647999.280573415], [554363.8601732237, 5647901.409426584],
                     [554365.1801732233, 5647902.109426583], [554313.0598267767, 5647999.980573417],
                     [554314.3898267763, 5648000.690573414], [554366.5101732236, 5647902.819426582],
                     [554367.830173223, 5647903.519426583], [554315.7098267768, 5648001.390573415],
                     [554317.0398267768, 5648002.100573416], [554369.1601732231, 5647904.229426583],
                     [554370.4801732232, 5647904.9294265825], [554318.3598267768, 5648002.800573416]]]
        data_latlng = [[[50.9801038330035, 3.7743247519946936], [50.98098878064322, 3.7735969850426625],
                        [50.98099653675816, 3.7736207616938873], [50.98011158897294, 3.7743485283119287],
                        [50.980117492559124, 3.774366860583644], [50.98100244045656, 3.773639094224294],
                        [50.981008700046935, 3.773658002499855], [50.98012375203382, 3.7743857685950313],
                        [50.980129920644025, 3.7744048175536555], [50.98101486877373, 3.77367705172676],
                        [50.981021128357916, 3.7736959600124296], [50.98013618011252, 3.774423725575141],
                        [50.98014234966079, 3.7744426321057896], [50.98102729802194, 3.7737148668086364],
                        [50.981033556656456, 3.7737339175451745], [50.98014860817873, 3.7744616825754176],
                        [50.98015477772084, 3.7744805891160937], [50.981039726314265, 3.7737528243514107],
                        [50.98104598494257, 3.7737718750980958], [50.98016103623252, 3.7744996395958577],
                        [50.98016720576842, 3.774518546146571], [50.981052154594174, 3.7737907819143555]]]
        # Act
        shapefile.update(data_latlng, GeomType.LINESTRING, epsg=4326)
        # Assert
        self.assertTrue(np.allclose(np.array(data_utm), list(shapefile.gdf.geometry[0].coords)))
