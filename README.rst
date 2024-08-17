ARTOF python utils
==================

Introduction
------------

This python package is part of the `ARTOF <https://artof-ilvo.github.io>`_ project and supports python add-ons.

Usage
-----

.. code-block:: bash

    pip install ilvo-artof-utils


Build (No CI/CD)
----------------

1. Install the dependencies

.. code-block:: bash

    pip install build
    pip install twine

2. Build and publish the package

.. code-block:: bash

    python -m build

Testing (No CI/CD)
------------------

1. Execute the following commands in the project root folder

.. code-block:: bash

    export ILVO_PATH=tests/files/robot
    coverage run -m pytest tests/test_*.py

Licence
-------

This project is under the ``ILVO LICENCE``