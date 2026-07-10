"""Fast CI e2e: TTS presets, voice cloning, multilingual, then STT."""

import os
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

ROUNDTRIP_TEXT = "Hello world this is a voice test"
EXPECTED_KEYWORDS = ("hello", "world", "voice", "test")

CLONE_TEXT = "Cloning works with a custom speaker sample"
CLONE_KEYWORDS = ("cloning", "works", "custom", "speaker", "sample")

SPANISH_TEXT = "Hola mundo esta es una prueba de voz"
SPANISH_KEYWORDS = ("hola", "mundo", "prueba", "voz")


def _run(cmd: list[str], *, timeout: int = 600) -> subprocess.CompletedProcess[str]:
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


def _run_tts(
    text: str,
    output: str,
    *,
    voice: str | None = None,
    language: str = "english",
) -> subprocess.CompletedProcess[str]:
    cmd = [
        "uv",
        "run",
        "skills/ez-tts/scripts/tts.py",
        text,
        "-l",
        language,
        "-o",
        output,
        "-q",
    ]
    if voice is not None:
        cmd.extend(["-v", voice])
    return _run(cmd)


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


def _assert_keywords(
    transcript: str, keywords: tuple[str, ...], *, min_hits: int = 2
) -> None:
    normalized = re.sub(r"[^a-z0-9\s]", " ", transcript.lower())
    hits = [kw for kw in keywords if kw in normalized]
    assert len(hits) >= min_hits, (
        f"Expected at least {min_hits} of {keywords} in transcript, "
        f"got {hits!r} from {transcript!r}"
    )


class TestTtsSttRoundtrip:
    def test_generate_then_transcribe(self, tmp_path: Path) -> None:
        """TTS alba → whisper-base should recover the spoken keywords."""
        out = str(tmp_path / "roundtrip.wav")

        tts = _run_tts(ROUNDTRIP_TEXT, out, voice="alba")
        assert tts.returncode == 0, f"TTS failed:\n{tts.stderr}\n{tts.stdout}"
        assert Path(out).exists()
        assert Path(out).stat().st_size > 1000

        stt = _run_stt(out)
        assert stt.returncode == 0, f"STT failed:\n{stt.stderr}\n{stt.stdout}"
        transcript = stt.stdout.strip()
        assert transcript, "STT returned empty transcript"
        _assert_keywords(transcript, EXPECTED_KEYWORDS)


class TestVoiceCloning:
    def test_clone_from_generated_sample(self, tmp_path: Path) -> None:
        """Clone from a freshly generated wav (requires HF_TOKEN + pocket-tts access)."""
        if not os.environ.get("HF_TOKEN"):
            pytest.skip("HF_TOKEN required for voice cloning")

        # Generate a clean PCM reference clip, then clone from that file.
        reference = str(tmp_path / "reference.wav")
        ref = _run_tts(
            "This is a clear reference voice for cloning.",
            reference,
            voice="alba",
        )
        assert ref.returncode == 0, f"Reference TTS failed:\n{ref.stderr}\n{ref.stdout}"
        assert Path(reference).exists()

        out = str(tmp_path / "cloned.wav")
        tts = _run_tts(CLONE_TEXT, out, voice=reference)
        assert tts.returncode == 0, f"TTS clone failed:\n{tts.stderr}\n{tts.stdout}"
        assert Path(out).exists()
        assert Path(out).stat().st_size > 1000

        stt = _run_stt(out)
        assert stt.returncode == 0, f"STT failed:\n{stt.stderr}\n{stt.stdout}"
        _assert_keywords(stt.stdout.strip(), CLONE_KEYWORDS, min_hits=1)


class TestMultilingual:
    def test_spanish_preset_roundtrip(self, tmp_path: Path) -> None:
        """Spanish model + lola voice → whisper-base keyword check."""
        out = str(tmp_path / "spanish.wav")
        tts = _run_tts(SPANISH_TEXT, out, voice="lola", language="spanish")
        assert tts.returncode == 0, f"TTS failed:\n{tts.stderr}\n{tts.stdout}"
        assert Path(out).exists()
        assert Path(out).stat().st_size > 1000

        stt = _run_stt(out)
        assert stt.returncode == 0, f"STT failed:\n{stt.stderr}\n{stt.stdout}"
        _assert_keywords(stt.stdout.strip(), SPANISH_KEYWORDS, min_hits=1)


class TestSttFixture:
    def test_whisper_base_on_speech_fixture(self, speech_wav: str) -> None:
        """Smoke-test STT against the checked-in 16 kHz speech fixture."""
        result = _run_stt(speech_wav)
        assert result.returncode == 0, f"STT failed:\n{result.stderr}\n{result.stdout}"
        assert len(result.stdout.strip()) > 0
