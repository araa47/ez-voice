import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

PRESET_VOICES = [
    "alba",
    "marius",
    "javert",
    "jean",
    "fantine",
    "cosette",
    "eponine",
    "azelma",
]


def _run_tts(text, voice, output, ogg=False):
    cmd = [
        "uv",
        "run",
        "skills/ez-tts/scripts/tts.py",
        text,
        "-v",
        voice,
        "-o",
        output,
        "-q",
    ]
    if ogg:
        cmd.append("--ogg")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return result


class TestPresetVoices:
    @pytest.mark.parametrize("voice", PRESET_VOICES)
    def test_preset_voice_generates_audio(self, voice, tmp_path):
        out = str(tmp_path / f"{voice}.wav")
        result = _run_tts("Hello, testing voice output.", voice, out)
        assert result.returncode == 0
        assert Path(out).exists()
        assert Path(out).stat().st_size > 100


class TestOutputFormats:
    def test_wav_output(self, tmp_path):
        out = str(tmp_path / "output.wav")
        result = _run_tts("Test wav output.", "alba", out)
        assert result.returncode == 0
        assert Path(out).exists()

    def test_ogg_output(self, tmp_path):
        out = str(tmp_path / "output.wav")
        result = _run_tts("Test ogg output.", "alba", out, ogg=True)
        assert result.returncode == 0
        ogg_path = str(tmp_path / "output.ogg")
        assert Path(ogg_path).exists()
