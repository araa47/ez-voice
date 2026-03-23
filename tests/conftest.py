import importlib.util
import sys
import types
from pathlib import Path

import pytest

RESOURCES_DIR = Path(__file__).parent / "resources"
PROJECT_ROOT = Path(__file__).parent.parent


def _ensure_parent_modules(name: str):
    parts = name.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            sys.modules[parent] = types.ModuleType(parent)


def _load_module(name: str, file_path: Path):
    if name in sys.modules:
        return sys.modules[name]
    _ensure_parent_modules(name)
    spec = importlib.util.spec_from_file_location(name, file_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


stt_module = _load_module(
    "skills.ez_stt.scripts.stt",
    PROJECT_ROOT / "skills" / "ez-stt" / "scripts" / "stt.py",
)
tts_module = _load_module(
    "skills.ez_tts.scripts.tts",
    PROJECT_ROOT / "skills" / "ez-tts" / "scripts" / "tts.py",
)


@pytest.fixture
def sample_wav():
    return str(RESOURCES_DIR / "sample.wav")


@pytest.fixture
def silence_wav():
    return str(RESOURCES_DIR / "silence.wav")


@pytest.fixture
def short_wav():
    return str(RESOURCES_DIR / "short.wav")


@pytest.fixture
def speech_wav():
    return str(RESOURCES_DIR / "speech_16k.wav")
