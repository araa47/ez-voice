---
name: ez-tts
description: Local text-to-speech using Kyutai Pocket TTS. Fast CPU-based TTS with multilingual models, preset voices, and voice cloning. Runs fully offline after model download.
---

# ez-tts - Local Text-to-Speech

Local text-to-speech using Kyutai's Pocket TTS. **Fully offline** after initial model download. ~10x realtime on CPU, no GPU needed.

Supports **english, french, german, portuguese, italian, spanish** (pocket-tts 2.x).

## Usage

```bash
# Basic English (outputs to /tmp/tts_output.wav)
uv run scripts/tts.py "Hello, this is a test"

# Specify preset voice
uv run scripts/tts.py "Hello world" --voice marius

# Other languages (default voice picked per language)
uv run scripts/tts.py "Hola mundo" --language spanish
uv run scripts/tts.py "Bonjour le monde" --language french
uv run scripts/tts.py "Ciao mondo" --language italian --voice giovanni

# Custom output file
uv run scripts/tts.py "Hello world" --out ~/my_audio.wav

# Output as OGG (for voice messages, requires ffmpeg)
uv run scripts/tts.py "Hello world" --ogg

# Voice cloning from a local sample (requires HF_TOKEN + HF access to kyutai/pocket-tts)
uv run scripts/tts.py "Hello world" --voice /path/to/sample.ogg
```

## Languages

| Language | Notes | Default voice |
|----------|-------|---------------|
| `english` (default) | Same as `english_2026-04` | `alba` |
| `english_2026-01` / `english_2026-04` | English model variants | `alba` |
| `spanish` / `spanish_24l` | `_24l` = higher quality, slower | `lola` |
| `german` / `german_24l` | | `juergen` |
| `italian` / `italian_24l` | | `giovanni` |
| `portuguese` / `portuguese_24l` | | `rafael` |
| `french_24l` | French is 24-layer only (`french` alias works) | `estelle` |

## Preset Voices

English: `alba`, `marius`, `javert`, `jean`, `fantine`, `cosette`, `eponine`, `azelma`, `anna`, `vera`, `charles`, `paul`, `george`, `mary`, `jane`, `michael`, `eve`, `bill_boerst`, `peter_yearsley`, `stuart_bell`, `caro_davy`

Other languages: `giovanni` (it), `lola` (es), `juergen` (de), `rafael` (pt), `estelle` (fr)

Custom cloned voices can be placed in the skill's `voices/` directory and used by name (e.g., `--voice myvoice` if `voices/myvoice.ogg` exists).

## Voice Cloning

Clone any voice from a clear speech sample:

```bash
uv run scripts/tts.py "Hello world" --voice ~/voices/my_voice.ogg
```

**Requirements:**
- Accept the terms on https://huggingface.co/kyutai/pocket-tts
- `HF_TOKEN` environment variable set
- Audio sample should be clear speech (WAV/OGG/MP3/FLAC)

Preset catalog voices work without cloning weights; file-path cloning needs the full model.

## Options

- `--voice/-v` — Voice name or path to audio for cloning (default depends on `--language`)
- `--language/-l` — Model language (default: `english`)
- `--out/-o` — Output file path (default: `/tmp/tts_output.wav`)
- `--ogg` — Convert output to OGG (requires ffmpeg)
- `--quiet/-q` — Suppress progress messages

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `HF_TOKEN` | Hugging Face token for model download / voice cloning |
