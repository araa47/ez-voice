import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from click.testing import CliRunner
from skills.ez_stt.scripts.stt import (  # ty: ignore[unresolved-import]
    BACKENDS,
    DEFAULT_BACKEND,
    BackendInfo,
    get_all_models,
    load_env_file,
    main,
    send_to_matrix,
)


class TestBackendConfig:
    def test_backends_has_parakeet(self):
        assert "parakeet" in BACKENDS

    def test_backends_has_whisper(self):
        assert "whisper" in BACKENDS

    def test_default_backend_is_parakeet(self):
        assert DEFAULT_BACKEND == "parakeet"

    def test_parakeet_has_required_keys(self):
        info = BACKENDS["parakeet"]
        assert "models" in info
        assert "default" in info
        assert "description" in info

    def test_whisper_has_required_keys(self):
        info = BACKENDS["whisper"]
        assert "models" in info
        assert "default" in info
        assert "description" in info

    def test_parakeet_default_model(self):
        assert BACKENDS["parakeet"]["default"] == "v2"

    def test_whisper_default_model(self):
        assert BACKENDS["whisper"]["default"] == "base"

    def test_parakeet_models(self):
        models = BACKENDS["parakeet"]["models"]
        assert "v2" in models
        assert "v3" in models

    def test_whisper_models(self):
        models = BACKENDS["whisper"]["models"]
        assert "tiny" in models
        assert "base" in models
        assert "small" in models
        assert "large-v3-turbo" in models

    def test_backend_info_type(self):
        info: BackendInfo = {
            "models": {"test": "test-model"},
            "default": "test",
            "description": "Test backend",
        }
        assert info["models"]["test"] == "test-model"


class TestLoadEnvFile:
    def test_loads_simple_vars(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_STT_VAR=hello_world\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_STT_VAR", raising=False)
        load_env_file()
        assert os.environ.get("TEST_STT_VAR") == "hello_world"
        monkeypatch.delenv("TEST_STT_VAR", raising=False)

    def test_loads_from_openclaw_dir(self, tmp_path, monkeypatch):
        openclaw_dir = tmp_path / ".openclaw"
        openclaw_dir.mkdir()
        env_file = openclaw_dir / ".env"
        env_file.write_text("TEST_OC_VAR=openclaw_value\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_OC_VAR", raising=False)
        load_env_file()
        assert os.environ.get("TEST_OC_VAR") == "openclaw_value"
        monkeypatch.delenv("TEST_OC_VAR", raising=False)

    def test_strips_quotes(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text('TEST_QUOTED="quoted_value"\n')
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_QUOTED", raising=False)
        load_env_file()
        assert os.environ.get("TEST_QUOTED") == "quoted_value"
        monkeypatch.delenv("TEST_QUOTED", raising=False)

    def test_strips_single_quotes(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_SQ='single_quoted'\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_SQ", raising=False)
        load_env_file()
        assert os.environ.get("TEST_SQ") == "single_quoted"
        monkeypatch.delenv("TEST_SQ", raising=False)

    def test_handles_export_prefix(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("export TEST_EXPORT=exported\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_EXPORT", raising=False)
        load_env_file()
        assert os.environ.get("TEST_EXPORT") == "exported"
        monkeypatch.delenv("TEST_EXPORT", raising=False)

    def test_skips_comments(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\nTEST_AFTER_COMMENT=value\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_AFTER_COMMENT", raising=False)
        load_env_file()
        assert os.environ.get("TEST_AFTER_COMMENT") == "value"
        monkeypatch.delenv("TEST_AFTER_COMMENT", raising=False)

    def test_skips_empty_lines(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("\n\nTEST_EMPTY_LINES=value\n\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_EMPTY_LINES", raising=False)
        load_env_file()
        assert os.environ.get("TEST_EMPTY_LINES") == "value"
        monkeypatch.delenv("TEST_EMPTY_LINES", raising=False)

    def test_does_not_override_existing_env(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_EXISTING=new_value\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("TEST_EXISTING", "original")
        load_env_file()
        assert os.environ["TEST_EXISTING"] == "original"

    def test_no_env_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        load_env_file()

    def test_openclaw_takes_priority(self, tmp_path, monkeypatch):
        openclaw_dir = tmp_path / ".openclaw"
        openclaw_dir.mkdir()
        oc_env = openclaw_dir / ".env"
        oc_env.write_text("TEST_PRIORITY=openclaw\n")
        home_env = tmp_path / ".env"
        home_env.write_text("TEST_PRIORITY=home\n")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TEST_PRIORITY", raising=False)
        load_env_file()
        assert os.environ.get("TEST_PRIORITY") == "openclaw"
        monkeypatch.delenv("TEST_PRIORITY", raising=False)


class TestSendToMatrix:
    def test_missing_credentials_prints_warning(self, monkeypatch):
        monkeypatch.delenv("MATRIX_HOMESERVER", raising=False)
        monkeypatch.delenv("MATRIX_ACCESS_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        send_to_matrix("!room:example.com", "test text")

    def test_missing_credentials_quiet(self, monkeypatch):
        monkeypatch.delenv("MATRIX_HOMESERVER", raising=False)
        monkeypatch.delenv("MATRIX_ACCESS_TOKEN", raising=False)
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        send_to_matrix("!room:example.com", "test text", quiet=True)

    def test_successful_send(self, monkeypatch):
        monkeypatch.setenv("MATRIX_HOMESERVER", "https://matrix.example.com")
        monkeypatch.setenv("MATRIX_ACCESS_TOKEN", "test_token")
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        mock_put = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp
        with (
            patch.object(stt.requests, "put", mock_put),
            patch("builtins.open", mock_open()),
        ):
            send_to_matrix("!room:example.com", "hello world")
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        assert "matrix.example.com" in call_args[0][0]
        assert call_args[1]["json"]["body"] == "🎙️ hello world"

    def test_send_strips_room_prefix(self, monkeypatch):
        monkeypatch.setenv("MATRIX_HOMESERVER", "https://matrix.example.com")
        monkeypatch.setenv("MATRIX_ACCESS_TOKEN", "test_token")
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        mock_put = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp
        with (
            patch.object(stt.requests, "put", mock_put),
            patch("builtins.open", mock_open()),
        ):
            send_to_matrix("room:!abc:example.com", "text")
        url = mock_put.call_args[0][0]
        assert "!abc:example.com" in url
        assert "room:" not in url

    def test_send_quiet_mode(self, monkeypatch):
        monkeypatch.setenv("MATRIX_HOMESERVER", "https://matrix.example.com")
        monkeypatch.setenv("MATRIX_ACCESS_TOKEN", "test_token")
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        mock_put = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp
        with (
            patch.object(stt.requests, "put", mock_put),
            patch("builtins.open", mock_open()),
        ):
            send_to_matrix("!room:example.com", "hello", quiet=True)

    def test_send_failure_prints_error(self, monkeypatch):
        monkeypatch.setenv("MATRIX_HOMESERVER", "https://matrix.example.com")
        monkeypatch.setenv("MATRIX_ACCESS_TOKEN", "test_token")
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        with (
            patch.object(
                stt.requests, "put", side_effect=Exception("Connection failed")
            ),
            patch("builtins.open", mock_open()),
        ):
            send_to_matrix("!room:example.com", "hello")

    def test_send_failure_quiet(self, monkeypatch):
        monkeypatch.setenv("MATRIX_HOMESERVER", "https://matrix.example.com")
        monkeypatch.setenv("MATRIX_ACCESS_TOKEN", "test_token")
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        with (
            patch.object(
                stt.requests, "put", side_effect=Exception("Connection failed")
            ),
            patch("builtins.open", mock_open()),
        ):
            send_to_matrix("!room:example.com", "hello", quiet=True)

    def test_send_homeserver_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("MATRIX_HOMESERVER", "https://matrix.example.com/")
        monkeypatch.setenv("MATRIX_ACCESS_TOKEN", "test_token")
        monkeypatch.setattr(Path, "home", lambda: Path("/nonexistent"))
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        mock_put = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_put.return_value = mock_resp
        with (
            patch.object(stt.requests, "put", mock_put),
            patch("builtins.open", mock_open()),
        ):
            send_to_matrix("!room:example.com", "hello")
        url = mock_put.call_args[0][0]
        assert "matrix.example.com//" not in url


class TestGetAllModels:
    def test_returns_list(self):
        models = get_all_models()
        assert isinstance(models, list)

    def test_contains_parakeet_models(self):
        models = get_all_models()
        assert "v2" in models
        assert "v3" in models

    def test_contains_whisper_models(self):
        models = get_all_models()
        assert "tiny" in models
        assert "base" in models
        assert "small" in models
        assert "large-v3-turbo" in models

    def test_count(self):
        models = get_all_models()
        total = sum(len(b["models"]) for b in BACKENDS.values())
        assert len(models) == total


def _make_mock_onnx():
    mock_onnx = MagicMock()
    mock_model = MagicMock()
    mock_model.recognize.return_value = "hello world"
    mock_onnx.load_model.return_value = mock_model
    return mock_onnx, mock_model


class TestMainCli:
    def _invoke(self, args, sample_wav, recognize_text="hello world"):
        mock_onnx, mock_model = _make_mock_onnx()
        mock_model.recognize.return_value = recognize_text
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        with (
            patch.dict("sys.modules", {"onnx_asr": mock_onnx}),
            patch.object(stt.subprocess, "run"),
        ):
            runner = CliRunner()
            result = runner.invoke(main, args)
        return result, mock_onnx, mock_model

    def test_basic_transcription(self, sample_wav):
        result, _, _ = self._invoke([sample_wav], sample_wav)
        assert result.exit_code == 0
        assert "hello world" in result.output

    def test_strips_whitespace(self, sample_wav):
        result, _, _ = self._invoke([sample_wav, "-q"], sample_wav, "  hello world  ")
        assert result.exit_code == 0
        assert "hello world" in result.output

    def test_quiet_mode(self, sample_wav):
        result, _, _ = self._invoke(
            [sample_wav, "--quiet"], sample_wav, "transcribed text"
        )
        assert result.exit_code == 0
        assert "Loading" not in result.output
        assert "transcribed text" in result.output

    def test_whisper_backend(self, sample_wav):
        result, mock_onnx, _ = self._invoke(
            [sample_wav, "-b", "whisper", "-q"], sample_wav
        )
        assert result.exit_code == 0
        mock_onnx.load_model.assert_called_once_with(
            "whisper-base", quantization="int8"
        )

    def test_specific_model(self, sample_wav):
        result, mock_onnx, _ = self._invoke(
            [sample_wav, "-b", "whisper", "-m", "tiny", "-q"], sample_wav
        )
        assert result.exit_code == 0
        mock_onnx.load_model.assert_called_once_with(
            "whisper-tiny", quantization="int8"
        )

    def test_no_int8(self, sample_wav):
        result, mock_onnx, _ = self._invoke([sample_wav, "--no-int8", "-q"], sample_wav)
        assert result.exit_code == 0
        mock_onnx.load_model.assert_called_once_with(
            "nemo-parakeet-tdt-0.6b-v2", quantization=None
        )

    def test_invalid_model_for_backend(self, sample_wav):
        result, _, _ = self._invoke(
            [sample_wav, "-b", "parakeet", "-m", "tiny"], sample_wav
        )
        assert result.exit_code != 0

    def test_nonexistent_audio_file(self):
        runner = CliRunner()
        result = runner.invoke(main, ["/nonexistent/audio.wav"])
        assert result.exit_code != 0

    def test_with_room_id(self, sample_wav):
        mock_onnx, mock_model = _make_mock_onnx()
        mock_model.recognize.return_value = "hello"
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        with (
            patch.dict("sys.modules", {"onnx_asr": mock_onnx}),
            patch.object(stt.subprocess, "run"),
            patch.object(stt, "send_to_matrix") as mock_send,
        ):
            runner = CliRunner()
            result = runner.invoke(
                main, [sample_wav, "-q", "--room-id", "!room:example.com"]
            )
        assert result.exit_code == 0
        mock_send.assert_called_once_with("!room:example.com", "hello", True)

    def test_room_id_not_called_on_empty_text(self, sample_wav):
        mock_onnx, mock_model = _make_mock_onnx()
        mock_model.recognize.return_value = "   "
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        with (
            patch.dict("sys.modules", {"onnx_asr": mock_onnx}),
            patch.object(stt.subprocess, "run"),
            patch.object(stt, "send_to_matrix") as mock_send,
        ):
            runner = CliRunner()
            result = runner.invoke(
                main, [sample_wav, "-q", "--room-id", "!room:example.com"]
            )
        assert result.exit_code == 0
        mock_send.assert_not_called()

    def test_verbose_output(self, sample_wav):
        result, _, _ = self._invoke([sample_wav], sample_wav)
        assert "Loading" in result.stderr
        assert "Transcribing" in result.stderr

    def test_ffmpeg_called_correctly(self, sample_wav):
        mock_onnx, _ = _make_mock_onnx()
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        mock_subprocess_run = MagicMock()
        with (
            patch.dict("sys.modules", {"onnx_asr": mock_onnx}),
            patch.object(stt.subprocess, "run", mock_subprocess_run),
        ):
            runner = CliRunner()
            runner.invoke(main, [sample_wav, "-q"])
        ffmpeg_call = mock_subprocess_run.call_args_list[0]
        cmd = ffmpeg_call[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-ar" in cmd
        assert "16000" in cmd
        assert "-ac" in cmd
        assert "1" in cmd

    def test_temp_file_cleanup(self, sample_wav):
        mock_onnx, _ = _make_mock_onnx()
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        created_temps = []
        orig_named_temp = tempfile.NamedTemporaryFile

        def capture_temp(*args, **kwargs):
            t = orig_named_temp(*args, **kwargs)
            created_temps.append(t.name)
            return t

        with (
            patch.dict("sys.modules", {"onnx_asr": mock_onnx}),
            patch.object(stt.subprocess, "run"),
            patch.object(stt.tempfile, "NamedTemporaryFile", capture_temp),
        ):
            runner = CliRunner()
            runner.invoke(main, [sample_wav, "-q"])

        for tmp in created_temps:
            assert not os.path.exists(tmp)

    def test_room_id_quiet_false(self, sample_wav):
        mock_onnx, mock_model = _make_mock_onnx()
        mock_model.recognize.return_value = "hello"
        stt = sys.modules["skills.ez_stt.scripts.stt"]
        with (
            patch.dict("sys.modules", {"onnx_asr": mock_onnx}),
            patch.object(stt.subprocess, "run"),
            patch.object(stt, "send_to_matrix") as mock_send,
        ):
            runner = CliRunner()
            result = runner.invoke(main, [sample_wav, "--room-id", "!room:example.com"])
        assert result.exit_code == 0
        mock_send.assert_called_once_with("!room:example.com", "hello", False)
