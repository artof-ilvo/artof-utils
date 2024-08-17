from unittest import TestCase
import json
import numpy as np
import math
from os import path
from artof_utils.schemas.affine import Affine


def verify_ry(R):
    angleY = R[1]
    m = np.array([
        [math.cos((math.pi / 180.0) * angleY), 0, math.sin((math.pi / 180.0) * angleY)],
        [0, 1, 0],
        [-math.sin((math.pi / 180.0) * angleY), 0, math.cos((math.pi / 180.0) * angleY)]
    ])
    return m


def verify_rz(R):
    angleZ = R[2]
    m = np.array([
        [math.cos((math.pi / 180.0) * angleZ), -math.sin((math.pi / 180.0) * angleZ), 0],
        [math.sin((math.pi / 180.0) * angleZ), math.cos((math.pi / 180.0) * angleZ), 0],
        [0, 0, 1]
    ])
    return m


def verify_vector_to_affine(t, r):
    r_ = np.matmul(verify_rz(r), verify_ry(r))
    m = np.identity(4)
    m[0:3, 0:3] = r_
    m[0:3, 3] = np.array(t).transpose()
    return m


class TestState(TestCase):
    def test_vecs_to_affine(self):
        with open(path.join(path.dirname(__file__), 'files', 'states', 'states.json')) as f:
            j_states = json.load(f)

        for j_state in j_states:
            t = np.array(j_state['state']['T'])
            r = np.array(j_state['state']['R'])

            t_, r_ = Affine().from_vectors(t, r).to_vectors()

            # If inverse angle for yaw also ok
            if abs(r_[2] - r[2]) > 0.1:
                if abs((r[2] - r_[2]) % 360.0) < 0.1:
                    r_[2] = r[2]

            print(f"Original vectors - t: {t}, r: {r}")
            print(f"Calculated vectors - t: {t_}, r: {r_}")
            print("--------------")

            self.assertTrue(np.allclose(t, t_, atol=0.1), f"Translations are not equal! "
                                                          f"Originally: {list(t)}, now: {list(t_)}")
            self.assertTrue(np.allclose(r, r_, atol=0.1), f"Rotations are not equal! "
                                                          f"Originally: {list(r)}, now: {list(r_)}")

        print("DONE!")

    def test_verify_vecs_to_affine(self):
        with open(path.join(path.dirname(__file__), 'files', 'states', 'states.json')) as f:
            j_states = json.load(f)

        for j_state in j_states:
            t = np.array(j_state['state']['T'])
            r = np.array(j_state['state']['R'])

            a_verify = verify_vector_to_affine(t, r)
            a = Affine().from_vectors(t, r).get()

            print(f"Program affine:\n {a}")
            print(f"Verify affine:\n {a_verify}")
            print("--------------")

            self.assertTrue(np.allclose(a, a_verify, atol=0.1), f"Affines are not equal! "
                                                                f"Program:\n {a} \n verify:\n {a_verify}")

        print("DONE!")
