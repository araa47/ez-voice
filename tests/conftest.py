import sys
from pathlib import Path

import pytest

RESOURCES_DIR = Path(__file__).parent / "resources"
PROJECT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(PROJECT_ROOT / "skills" / "ez-stt" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "skills" / "ez-tts" / "scripts"))


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
