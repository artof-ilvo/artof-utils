import numpy as np
from scipy.spatial.transform import Rotation


class Affine:

    def __init__(self):
        self.a = np.identity(4)

    def get(self):
        return self.a

    def get_rotation_matrix(self):
        return self.a[0:3, 0:3]

    def get_translation_vector(self):
        return self.a[0:3, 3].transpose()

    def from_vectors(self, t, r):
        """
        Creates affine from two vectors
        :param t: vector (x, y, z) [m]
        :param r: (pitch, roll, yaw) [°]
        :return: affine
        """

        self.a[0:3, 3] = t.transpose()
        self.a[0:3, 0:3] = Rotation.from_euler('xyz', r, degrees=True).as_matrix()
        return self

    def to_vectors(self):
        """
        creates affine in vector format
        :return: t_(x, y, z) [m], r_(pitch, roll, yaw) [°]
        """
        t_ = self.get_translation_vector()
        r_m = self.get_rotation_matrix()
        r_ = Rotation.from_matrix(r_m).as_euler('xyz', degrees=True)
        return t_, r_
