import numpy as np


def __numeric(value):
    """
    Check if value is numeric
    :param value: Value to check
    :return: true if value is numeric, false otherwise
    """
    return (isinstance(value, (int, float)) or
            isinstance(value, (np.float32, np.float64, np.float16)) or
            isinstance(value, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)))


def __get_depth_list(data):
    """
    Get depth of list
    :param data: List
    :return: depth of list
    """
    if not isinstance(data, list):
        return 0
    elif len(data) == 0:
        return 1
    else:
        # Item is a list, numpy array, scalar, None or object (e.g. TrajectPoint)
        return 1 + max(0 if (__numeric(item) or item is None) else
                       __get_depth_list(item) if isinstance(item, list) else
                       __get_depth_np(item) if isinstance(item, np.ndarray) else
                       1
                       for item in data)


def __get_depth_np(data):
    """"
    Get depth of numpy array.
    Numpy arrays require that every dimension is uniform,
    meaning all the nested sequences must have the same length to form a multidimensional array.
    :param data: numpy array
    :return: depth of array
    """
    depth = 0
    while isinstance(data, np.ndarray):
        depth += 1
        data = data[0] if data.size > 0 else None
    return depth


def get_depth(arr):
    """
    Get depth of array (public function)
    :param arr: array
    :return: depth of array
    """
    depth_lst = __get_depth_list(arr)
    depth_np = __get_depth_np(arr)
    return max(depth_lst, depth_np)
    #if isinstance(arr, np.ndarray) : return __get_depth_np(arr)
    #elif isinstance(arr, list) : return __get_depth_list(arr)
    #else : return 0

