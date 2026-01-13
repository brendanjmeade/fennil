fennel
----------------------------------------

Viewer for kinematic earthquake simulations

License
----------------------------------------

This library is OpenSource and follow the MIT License

Installation
----------------------------------------

Install the application/library

.. code-block:: console

    pip install fennel

Run the application

.. code-block:: console

    fennel

Developement setup
----------------------------------------

We recommend using uv for setting up and managing a virtual environement for your development.

.. code-block:: console

    # Create venv and install all dependencies
    uv sync --all-extras --dev

    # Activate environement
    source .venv/bin/activate

    # Install commit analysis
    pre-commit install
    pre-commit install --hook-type commit-msg

    # Allow live code edit
    uv pip install -e .



For running tests and checks, you can run ``nox``.

.. code-block:: console

    # run all
    nox

    # lint
    nox -s lint

    # tests
    nox -s tests

Professional Support
----------------------------------------

* `Training <https://www.kitware.com/courses/trame/>`_: Learn how to confidently use trame from the expert developers at Kitware.
* `Support <https://www.kitware.com/trame/support/>`_: Our experts can assist your team as you build your web application and establish in-house expertise.
* `Custom Development <https://www.kitware.com/trame/support/>`_: Leverage Kitware’s 25+ years of experience to quickly build your web application.
