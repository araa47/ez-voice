"""Fast CI e2e: generate speech with TTS, then transcribe with STT."""

import os
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

# Distinctive phrase with common words whisper-base can catch.
ROUNDTRIP_TEXT = "Hello world this is a voice test"
EXPECTED_KEYWORDS = ("hello", "world", "voice", "test")


def _run(cmd: list[str], *, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    env.setdefault("PYTHONWARNINGS", "ignore")
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def _run_tts(text: str, voice: str, output: str) -> subprocess.CompletedProcess[str]:
    return _run(
        [
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
    )


def _run_stt(
    audio: str, *, backend: str = "whisper", model: str = "base"
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "uv",
            "run",
            "skills/ez-stt/scripts/stt.py",
            audio,
            "-b",
            backend,
            "-m",
            model,
            "-q",
        ]
    )


class TestTtsSttRoundtrip:
    def test_generate_then_transcribe(self, tmp_path: Path) -> None:
        """TTS alba → whisper-base should recover the spoken keywords."""
        out = str(tmp_path / "roundtrip.wav")

        tts = _run_tts(ROUNDTRIP_TEXT, "alba", out)
        assert tts.returncode == 0, f"TTS failed:\n{tts.stderr}\n{tts.stdout}"
        assert Path(out).exists()
        assert Path(out).stat().st_size > 1000

        stt = _run_stt(out)
        assert stt.returncode == 0, f"STT failed:\n{stt.stderr}\n{stt.stdout}"

        transcript = stt.stdout.strip().lower()
        assert transcript, "STT returned empty transcript"
        # Normalize punctuation so keyword checks are stable across models.
        normalized = re.sub(r"[^a-z0-9\s]", " ", transcript)
        hits = [kw for kw in EXPECTED_KEYWORDS if kw in normalized]
        assert len(hits) >= 2, (
            f"Expected at least 2 of {EXPECTED_KEYWORDS} in transcript, "
            f"got {hits!r} from {transcript!r}"
        )


class TestSttFixture:
    def test_whisper_base_on_speech_fixture(self, speech_wav: str) -> None:
        """Smoke-test STT against the checked-in 16 kHz speech fixture."""
        result = _run_stt(speech_wav)
        assert result.returncode == 0, f"STT failed:\n{result.stderr}\n{result.stdout}"
        assert len(result.stdout.strip()) > 0
