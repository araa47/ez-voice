import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import tts as tts_mod  # ty: ignore[unresolved-import]
from click.testing import CliRunner
from tts import (  # ty: ignore[unresolved-import]
    PRESET_VOICES,
    SKILL_DIR,
    VOICES_DIR,
    load_env,
    main,
)


class TestConstants:
    def test_preset_voices_list(self):
        assert isinstance(PRESET_VOICES, list)
        assert len(PRESET_VOICES) == 8

    def test_preset_voices_contents(self):
        expected = [
            "alba",
            "marius",
            "javert",
            "jean",
            "fantine",
            "cosette",
            "eponine",
            "azelma",
        ]
        assert PRESET_VOICES == expected

    def test_skill_dir(self):
        assert SKILL_DIR == Path(__file__).parent.parent / "skills" / "ez-tts"

    def test_voices_dir(self):
        assert VOICES_DIR == SKILL_DIR / "voices"


class TestLoadEnv:
    def test_loads_vars_from_env_file(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_TTS_VAR=tts_value\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_TTS_VAR", raising=False)
        load_env()
        assert os.environ.get("TEST_TTS_VAR") == "tts_value"
        monkeypatch.delenv("TEST_TTS_VAR", raising=False)

    def test_strips_double_quotes(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text('TEST_DQ="double_quoted"\n')
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_DQ", raising=False)
        load_env()
        assert os.environ.get("TEST_DQ") == "double_quoted"
        monkeypatch.delenv("TEST_DQ", raising=False)

    def test_strips_single_quotes(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_SQ='single_quoted'\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_SQ", raising=False)
        load_env()
        assert os.environ.get("TEST_SQ") == "single_quoted"
        monkeypatch.delenv("TEST_SQ", raising=False)

    def test_handles_export_prefix(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("export TEST_EXP=exported\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_EXP", raising=False)
        load_env()
        assert os.environ.get("TEST_EXP") == "exported"
        monkeypatch.delenv("TEST_EXP", raising=False)

    def test_skips_comments(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\nTEST_COMMENT=val\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_COMMENT", raising=False)
        load_env()
        assert os.environ.get("TEST_COMMENT") == "val"
        monkeypatch.delenv("TEST_COMMENT", raising=False)

    def test_skips_empty_lines(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("\n\nTEST_EMPTY=val\n\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_EMPTY", raising=False)
        load_env()
        assert os.environ.get("TEST_EMPTY") == "val"
        monkeypatch.delenv("TEST_EMPTY", raising=False)

    def test_does_not_override_existing(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_EXIST=new\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("TEST_EXIST", "original")
        load_env()
        assert os.environ["TEST_EXIST"] == "original"

    def test_no_env_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        load_env()


def _make_mock_tts():
    mock_tts_cls = MagicMock()
    mock_model = MagicMock()
    mock_model.sample_rate = 24000
    mock_audio = MagicMock()
    mock_model.generate_audio.return_value = mock_audio
    mock_tts_cls.load_model.return_value = mock_model
    return mock_tts_cls, mock_model


def _mock_modules(mock_tts_cls=None):
    if mock_tts_cls is None:
        mock_tts_cls, _ = _make_mock_tts()
    mock_pocket = MagicMock()
    mock_pocket.TTSModel = mock_tts_cls
    mock_scipy = MagicMock()
    return {
        "pocket_tts": mock_pocket,
        "scipy": mock_scipy,
        "scipy.io": mock_scipy.io,
        "scipy.io.wavfile": mock_scipy.io.wavfile,
    }, mock_scipy


class TestMainCli:
    def _invoke(self, args, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        mock_tts_cls, mock_model = _make_mock_tts()
        modules, mock_scipy = _mock_modules(mock_tts_cls)
        tts = tts_mod
        with patch.dict("sys.modules", modules), patch.object(tts.subprocess, "run"):
            runner = CliRunner()
            result = runner.invoke(main, args)
        return result, mock_tts_cls, mock_model, mock_scipy

    def test_basic_tts_preset_voice(self, monkeypatch):
        result, mock_tts_cls, mock_model, _ = self._invoke(
            ["hello world", "-v", "alba", "-q"], monkeypatch
        )
        assert result.exit_code == 0
        mock_tts_cls.load_model.assert_called_once()
        mock_model.get_state_for_audio_prompt.assert_called_once_with("alba")
        mock_model.generate_audio.assert_called_once()

    def test_default_voice_is_alba(self, monkeypatch):
        result, _, mock_model, _ = self._invoke(["test text", "-q"], monkeypatch)
        assert result.exit_code == 0
        mock_model.get_state_for_audio_prompt.assert_called_once_with("alba")

    def test_custom_output_path(self, tmp_path, monkeypatch):
        out_path = str(tmp_path / "output.wav")
        result, _, _, _ = self._invoke(["text", "-o", out_path, "-q"], monkeypatch)
        assert result.exit_code == 0
        assert out_path in result.output

    def test_verbose_output(self, monkeypatch):
        result, _, _, _ = self._invoke(["hello"], monkeypatch)
        assert "Loading model" in result.stderr
        assert "Loading voice" in result.stderr
        assert "Generating audio" in result.stderr

    def test_unknown_voice_error(self, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        runner = CliRunner()
        result = runner.invoke(main, ["text", "-v", "nonexistent_voice_xyz", "-q"])
        assert result.exit_code != 0
        assert "Unknown voice" in result.output

    def test_unknown_voice_shows_presets(self, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        runner = CliRunner()
        result = runner.invoke(main, ["text", "-v", "nonexistent_voice_xyz", "-q"])
        assert "Available presets" in result.output

    def test_voice_file_path(self, tmp_path, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        voice_file = tmp_path / "custom_voice.wav"
        voice_file.write_bytes(b"fake audio data")
        result, _, mock_model, _ = self._invoke(
            ["text", "-v", str(voice_file)], monkeypatch
        )
        assert result.exit_code == 0
        mock_model.get_state_for_audio_prompt.assert_called_once_with(str(voice_file))
        assert "HF_TOKEN" in result.stderr

    def test_voice_file_with_hf_token(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HF_TOKEN", "hf_test")
        voice_file = tmp_path / "custom_voice.wav"
        voice_file.write_bytes(b"fake audio data")
        result, _, _, _ = self._invoke(
            ["text", "-v", str(voice_file), "-q"], monkeypatch
        )
        assert result.exit_code == 0
        assert "HF_TOKEN" not in result.stderr

    def test_bundled_voice(self, tmp_path, monkeypatch):
        monkeypatch.delenv("HF_TOKEN", raising=False)
        voices_dir = tmp_path / "voices"
        voices_dir.mkdir()
        bundled = voices_dir / "custom_clone.ogg"
        bundled.write_bytes(b"fake ogg")
        tts = tts_mod
        monkeypatch.setattr(tts, "VOICES_DIR", voices_dir)
        result, _, mock_model, _ = self._invoke(
            ["text", "-v", "custom_clone"], monkeypatch
        )
        assert result.exit_code == 0
        mock_model.get_state_for_audio_prompt.assert_called_once_with(str(bundled))
        assert "HF_TOKEN" in result.stderr

    def test_bundled_voice_with_hf_token(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HF_TOKEN", "hf_test")
        voices_dir = tmp_path / "voices"
        voices_dir.mkdir()
        bundled = voices_dir / "custom_clone.ogg"
        bundled.write_bytes(b"fake ogg")
        tts = tts_mod
        monkeypatch.setattr(tts, "VOICES_DIR", voices_dir)
        result, _, _, _ = self._invoke(
            ["text", "-v", "custom_clone", "-q"], monkeypatch
        )
        assert result.exit_code == 0
        assert "HF_TOKEN" not in result.stderr

    def test_unknown_voice_shows_bundled(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        voices_dir = tmp_path / "voices"
        voices_dir.mkdir()
        (voices_dir / "my_clone.ogg").write_bytes(b"fake")
        tts = tts_mod
        monkeypatch.setattr(tts, "VOICES_DIR", voices_dir)
        runner = CliRunner()
        result = runner.invoke(main, ["text", "-v", "bad_voice", "-q"])
        assert result.exit_code != 0
        assert "Bundled clones" in result.output
        assert "my_clone" in result.output

    def test_ogg_conversion(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        out_path = str(tmp_path / "output.wav")
        Path(out_path).write_bytes(b"fake wav")
        mock_tts_cls, _ = _make_mock_tts()
        modules, _ = _mock_modules(mock_tts_cls)
        tts = tts_mod
        mock_subrun = MagicMock()
        with (
            patch.dict("sys.modules", modules),
            patch.object(tts.subprocess, "run", mock_subrun),
        ):
            runner = CliRunner()
            result = runner.invoke(main, ["text", "-o", out_path, "--ogg", "-q"])
        assert result.exit_code == 0
        mock_subrun.assert_called_once()
        cmd = mock_subrun.call_args[0][0]
        assert "ffmpeg" in cmd
        assert "libopus" in cmd

    def test_ogg_ffmpeg_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        out_path = str(tmp_path / "output.wav")
        mock_tts_cls, _ = _make_mock_tts()
        modules, _ = _mock_modules(mock_tts_cls)
        tts = tts_mod
        with (
            patch.dict("sys.modules", modules),
            patch.object(tts.subprocess, "run", side_effect=FileNotFoundError),
        ):
            runner = CliRunner()
            result = runner.invoke(main, ["text", "-o", out_path, "--ogg"])
        assert result.exit_code == 0
        assert "ffmpeg not found" in result.stderr
        assert out_path in result.output

    def test_ogg_ffmpeg_conversion_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        out_path = str(tmp_path / "output.wav")
        mock_tts_cls, _ = _make_mock_tts()
        modules, _ = _mock_modules(mock_tts_cls)
        tts = tts_mod
        with (
            patch.dict("sys.modules", modules),
            patch.object(
                tts.subprocess,
                "run",
                side_effect=subprocess.CalledProcessError(1, "ffmpeg"),
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(main, ["text", "-o", out_path, "--ogg"])
        assert result.exit_code == 0
        assert "conversion failed" in result.stderr
        assert out_path in result.output

    def test_tts_generation_error(self, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        mock_tts_cls = MagicMock()
        mock_tts_cls.load_model.side_effect = Exception("Model load failed")
        modules, _ = _mock_modules(mock_tts_cls)
        tts = tts_mod
        with patch.dict("sys.modules", modules), patch.object(tts.subprocess, "run"):
            runner = CliRunner()
            result = runner.invoke(main, ["text", "-q"])
        assert result.exit_code != 0
        assert "Error generating speech" in result.output

    def test_wav_output_path_printed(self, monkeypatch):
        result, _, _, _ = self._invoke(["text", "-q"], monkeypatch)
        assert result.exit_code == 0
        assert "/tmp/tts_output.wav" in result.output

    def test_ogg_removes_intermediate_wav(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        out_path = str(tmp_path / "output.wav")
        mock_tts_cls, _ = _make_mock_tts()
        modules, _ = _mock_modules(mock_tts_cls)
        tts = tts_mod
        mock_remove = MagicMock()
        with (
            patch.dict("sys.modules", modules),
            patch.object(tts.subprocess, "run"),
            patch.object(tts.os, "remove", mock_remove),
        ):
            runner = CliRunner()
            result = runner.invoke(main, ["text", "-o", out_path, "--ogg", "-q"])
        assert result.exit_code == 0
        mock_remove.assert_called_once_with(out_path)

    def test_ogg_outputs_ogg_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        out_path = str(tmp_path / "output.wav")
        ogg_path = str(tmp_path / "output.ogg")
        Path(out_path).write_bytes(b"fake wav")
        mock_tts_cls, _ = _make_mock_tts()
        modules, _ = _mock_modules(mock_tts_cls)
        tts = tts_mod
        with patch.dict("sys.modules", modules), patch.object(tts.subprocess, "run"):
            runner = CliRunner()
            result = runner.invoke(main, ["text", "-o", out_path, "--ogg", "-q"])
        assert result.exit_code == 0
        assert ogg_path in result.output

    def test_ogg_flag_changes_wav_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        out_path = str(tmp_path / "speech.ogg")
        mock_tts_cls, _ = _make_mock_tts()
        modules, mock_scipy = _mock_modules(mock_tts_cls)
        tts = tts_mod
        with patch.dict("sys.modules", modules), patch.object(tts.subprocess, "run"):
            runner = CliRunner()
            runner.invoke(main, ["text", "-o", out_path, "--ogg", "-q"])
        write_call = mock_scipy.io.wavfile.write.call_args
        assert write_call[0][0].endswith(".wav")
