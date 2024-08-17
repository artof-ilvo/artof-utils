class Singleton(type):
    """
    A metaclass that creates a Singleton instance for a class.

    The Singleton pattern ensures that a class has only one instance and provides a global point of access to it.
    This metaclass implements the pattern by intercepting calls to the class's constructor to ensure that only one
    instance is created throughout the lifetime of the application. If the class has already been instantiated,
    the original instance is returned to all subsequent callers.

    Attributes:
        _instances (dict): A class-level dictionary that maps a class to its single instance.
    """

    _instances = {}  # Stores the singleton instance for each class.

    def __call__(cls, *args, **kwargs):
        """
        This method checks if the class instance already exists in the `_instances` dictionary.
        If it does, it returns that instance. If not, it creates a new instance, stores it in
        `_instances`, and then returns it.

        :param cls: The class for which the singleton instance is being requested.
        :param *args: Positional arguments to pass to the class constructor.
        :param *kwargs: Keyword arguments to pass to the class constructor.

        :return:The singleton instance of the class.
        """
        if cls not in cls._instances:
            # If the instance does not exist, create it and store it in the _instances dict.
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
