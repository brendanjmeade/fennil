## fennil

![Fennil](https://github.com/brendanjmeade/fennil/blob/main/fennil.jpg)

Viewer for kinematic earthquake simulations

Interactively displays [`celeri`](https://github.com/brendanjmeade/celeri)
models. `fennil` is a rebuild of the original
[`result_manager`](https://github.com/brendanjmeade/result_manager).

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
it in your shell or place it in a local `.env` file (for local development):

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
# Create venv and activate
uv venv
source .venv/bin/activate

# Install & allow live code edit
uv pip install -e .

# Install all dev dependencies
uv sync --all-extras --dev
```

To run test/linting:

```console
pre-commit run --all
```

## License

This library is OpenSource and follows the MIT License. For more details, see
[LICENSE](https://github.com/brendanjmeade/fennil/blob/main/LICENSE)

## Commit message convention

Semantic release rely on
[conventional commits](https://www.conventionalcommits.org/) to generate new
releases and changelog.
