import importlib.util
from pathlib import Path


def _load_legacy_module():
    legacy_path = Path(__file__).with_name("app.checkmoney.py")
    spec = importlib.util.spec_from_file_location("legacy_app_checkmoney", legacy_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    _load_legacy_module().main()
