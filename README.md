# ez-voice

Local speech-to-text and text-to-speech skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Skills

| Skill | Description |
|-------|-------------|
| **ez-stt** | Local speech-to-text using Parakeet (best English accuracy) or Whisper (fastest, multilingual) |
| **ez-tts** | Local text-to-speech using Kyutai Pocket TTS with 8 preset voices and voice cloning |

Both skills run fully offline after initial model download. No API keys needed (except for TTS voice cloning which requires a Hugging Face token).

## Installation

```bash
npx skills add araa47/ez-voice
```

This installs both `ez-stt` and `ez-tts` skills.

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- [ffmpeg](https://ffmpeg.org/) (for audio conversion)

## Quick Start

### Speech-to-Text

```bash
# Transcribe audio (Parakeet, best English accuracy)
scripts/stt.py audio.ogg

# Use Whisper backend (faster, multilingual)
scripts/stt.py audio.ogg -b whisper
```

### Text-to-Speech

```bash
# Generate speech with default voice
uv run scripts/tts.py "Hello, world"

# Choose a voice
uv run scripts/tts.py "Hello, world" --voice marius

# Output as OGG
uv run scripts/tts.py "Hello, world" --ogg
```

See each skill's `SKILL.md` for full usage details.

## Contributing

1. Install dependencies: `uv sync --all-extras`
2. Make your changes
3. Ensure pre-commit hooks pass: `prek run --all-files`
4. Ensure tests pass: `uv run -m pytest`
5. Submit a PR
