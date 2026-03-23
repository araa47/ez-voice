# Contributing

1. Install dependencies: `uv sync --all-extras`
2. Make your changes.
3. Ensure pre-commit hooks pass: `prek run --all-files`
4. Ensure unit tests pass: `uv run -m pytest -m "not e2e"`
5. Run end-to-end tests (downloads real models, slow): `uv run -m pytest -m e2e`
6. Submit a PR.

## Testing

### Unit tests

Unit tests mock external dependencies and run fast:

```bash
uv run -m pytest -m "not e2e"
```

### End-to-end tests

E2E tests download and run real STT/TTS models. They are slow but verify
that the full pipeline works. Run them before submitting changes that touch
model loading, audio processing, or CLI argument handling:

```bash
uv run -m pytest -m e2e
```

### Coverage

To generate a coverage report:

```bash
uv run pytest -m "not e2e" --cov=skills/ez-stt/scripts --cov=skills/ez-tts/scripts --cov-report=term
```
