## fennil

Attempt at a much faster rebuild of
[`result_manager`](https://github.com/brendanjmeade/result_manager) for larger
[`celeri`](https://github.com/brendanjmeade/celeri) models.

Viewer for kinematic earthquake simulations

## License

This library is OpenSource and follows the MIT License

## Installation

Install the application/library

```console
pip install fennil
```

Run the application

```console
fennil
```

## Mapbox token

Set a Mapbox access token so base maps render with Mapbox styles. Either export
it in your shell or place it in a local `.env` (already gitignored):

```console
export FENNIL_MAP_BOX_TOKEN="YOUR_TOKEN_HERE"
```

Or create a `.env` file in the project root containing:

```
FENNIL_MAP_BOX_TOKEN=YOUR_TOKEN_HERE
```

## Development setup

We recommend using uv for setting up and managing a virtual environment for your
development.

```console
# Create venv and install all dependencies
uv sync --all-extras --dev

# Activate environment
source .venv/bin/activate

# Install commit analysis
pre-commit install
pre-commit install --hook-type commit-msg

# Allow live code edit
uv pip install -e .
```

For running tests and checks, you can run `nox`.

```console
# run all
nox

# lint
nox -s lint

# tests
nox -s tests
```

## Commit message convention

Semantic release rely on
[conventional commits](https://www.conventionalcommits.org/) to generate new
releases and changelog.
