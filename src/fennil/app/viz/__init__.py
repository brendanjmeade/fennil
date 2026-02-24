import importlib.util
from pathlib import Path

from fennil.app.registry import FIELD_REGISTRY

FIELDS_DIRECTORY = Path(__file__).parent / "fields"


def load_all_viz():
    for f in sorted(FIELDS_DIRECTORY.glob("*.py")):
        if f.name.startswith("_"):
            continue

        name = f.stem
        spec = importlib.util.spec_from_file_location(name, f)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        FIELD_REGISTRY.register(
            name,
            module.SPEC,
            module.builder,
            module.can_render,
        )


__all__ = [
    "load_all_viz",
]
