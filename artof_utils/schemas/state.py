from artof_utils.schemas.affine import Affine
from pydantic import BaseModel, ConfigDict, model_serializer
import numpy as np
from typing import Any, Dict


class State(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    R: np.ndarray
    T: np.ndarray
    T_cov: np.ndarray
    R_cov: np.ndarray

    @model_serializer
    def ser_model(self) -> Dict[str, Any]:
        return {'R': self.R.tolist(), 'T': self.T.tolist(), 'T_cov': self.T_cov.tolist(), 'R_cov': self.R_cov.tolist()}

    def __init__(self, j=None):
        if j is None:
            j = {'R': [0, 0, 0], 'T': [0, 0, 0], 'T_cov': [0, 0, 0], 'R_cov': [0, 0, 0]}

        super().__init__(R=np.array(j['R']),
                         T=np.array(j['T']),
                         T_cov=np.array(j['T_cov']),
                         R_cov=np.array(j['R_cov']))

    def __eq__(self, other):
        return (np.array_equal(self.R, other.R) and
                np.array_equal(self.T, other.T) and
                np.array_equal(self.T_cov, other.T_cov) and
                np.array_equal(self.R_cov, other.R_cov))

    def __str__(self):
        return f"R: {self.R.tolist()}\r\n" \
               f"T: {self.T.tolist()}\r\n" \
               f"R_cov: {self.R_cov.tolist()}\r\n" \
               f"T_cov: {self.T_cov.tolist()}\r\n"

    def as_affine(self):
        """
        Creates an affine from this state
        :return: affine
        """
        return Affine().from_vectors(self.T, self.R)

    def to_json(self):
        return {
            'R': self.R.tolist(),
            'T': self.T.tolist(),
            'T_cov': self.T_cov.tolist(),
            'R_cov': self.R_cov.tolist()
        }
