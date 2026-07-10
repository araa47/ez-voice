# Contributing

1. Install dependencies: `uv sync --all-extras`
2. Make your changes.
3. Ensure pre-commit hooks pass: `prek run --all-files`
4. Ensure unit tests pass: `uv run -m pytest -m "not e2e"`
5. Optionally run fast e2e (downloads models once, then cached): `uv run -m pytest -m "e2e and not e2e_slow"`
6. Submit a PR.

## Testing

### Unit tests

Unit tests mock external dependencies and run fast:

```bash
uv run -m pytest -m "not e2e"
```

### End-to-end tests

E2E tests download and run real STT/TTS models. CI runs the **fast** subset on
every PR (TTS → STT roundtrip + whisper-base fixture), with Hugging Face /
pocket-tts model caches so cold downloads only happen once.

```bash
# Fast suite (what CI runs)
uv run -m pytest -m "e2e and not e2e_slow"

# Exhaustive matrix (all preset voices + all STT models)
uv run -m pytest -m e2e_slow
```

Set `HF_TOKEN` (Hugging Face) for reliable model downloads / voice cloning.

### Coverage

To generate a coverage report:

```bash
uv run pytest -m "not e2e" --cov=skills/ez-stt/scripts --cov=skills/ez-tts/scripts --cov-report=term
```
