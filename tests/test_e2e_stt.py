import subprocess
from pathlib import Path

import pytest

SPEECH_WAV = Path(__file__).parent / "resources" / "speech_16k.wav"

pytestmark = pytest.mark.e2e


def _run_stt(backend, model, audio=SPEECH_WAV):
    result = subprocess.run(
        [
            "uv",
            "run",
            "skills/ez-stt/scripts/stt.py",
            str(audio),
            "-b",
            backend,
            "-m",
            model,
            "-q",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result


class TestParakeetBackend:
    def test_parakeet_v2(self):
        result = _run_stt("parakeet", "v2")
        assert result.returncode == 0
        text = result.stdout.strip().lower()
        assert len(text) > 0

    def test_parakeet_v3(self):
        result = _run_stt("parakeet", "v3")
        assert result.returncode == 0
        text = result.stdout.strip().lower()
        assert len(text) > 0


class TestWhisperBackend:
    def test_whisper_tiny(self):
        result = _run_stt("whisper", "tiny")
        assert result.returncode == 0
        text = result.stdout.strip().lower()
        assert len(text) > 0

    def test_whisper_base(self):
        result = _run_stt("whisper", "base")
        assert result.returncode == 0
        text = result.stdout.strip().lower()
        assert len(text) > 0

    def test_whisper_small(self):
        result = _run_stt("whisper", "small")
        assert result.returncode == 0
        text = result.stdout.strip().lower()
        assert len(text) > 0

    def test_whisper_large_v3_turbo(self):
        result = _run_stt("whisper", "large-v3-turbo")
        assert result.returncode == 0
        text = result.stdout.strip().lower()
        assert len(text) > 0
