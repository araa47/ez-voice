#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pocket-tts>=4.0.1",
#     "scipy",
#     "soundfile",
#     "click",
# ]
# ///
"""Local text-to-speech using Kyutai Pocket TTS. Supports preset voices, languages, and voice cloning."""

import os
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import click  # noqa: E402

# Catalog from pocket-tts 2.x (_ORIGINS_OF_PREDEFINED_VOICES).
PRESET_VOICES = [
    "alba",
    "marius",
    "javert",
    "jean",
    "fantine",
    "cosette",
    "eponine",
    "azelma",
    "anna",
    "vera",
    "charles",
    "paul",
    "george",
    "mary",
    "jane",
    "michael",
    "eve",
    "bill_boerst",
    "peter_yearsley",
    "stuart_bell",
    "caro_davy",
    "giovanni",  # Italian
    "lola",  # Spanish
    "juergen",  # German
    "rafael",  # Portuguese
    "estelle",  # French
]

# Config stems shipped with pocket-tts (see pocket_tts/config/*.yaml).
LANGUAGES = [
    "english",
    "english_2026-01",
    "english_2026-04",
    "french_24l",
    "german",
    "german_24l",
    "italian",
    "italian_24l",
    "portuguese",
    "portuguese_24l",
    "spanish",
    "spanish_24l",
]

# Friendly aliases → config stem (pocket-tts rejects bare "french").
LANGUAGE_ALIASES = {
    "french": "french_24l",
    "en": "english",
    "fr": "french_24l",
    "de": "german",
    "it": "italian",
    "pt": "portuguese",
    "es": "spanish",
}

DEFAULT_VOICE_FOR_LANGUAGE = {
    "italian": "giovanni",
    "spanish": "lola",
    "german": "juergen",
    "portuguese": "rafael",
    "french": "estelle",
}

SKILL_DIR = Path(__file__).parent.parent
VOICES_DIR = SKILL_DIR / "voices"


def load_env():
    """Load environment variables from ~/.env if it exists."""
    env_paths = [Path.home() / ".env"]
    for env_file in env_paths:
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    value = value.strip().strip('"').strip("'")
                    if key.startswith("export "):
                        key = key[7:]
                    os.environ.setdefault(key.strip(), value)


def resolve_language(language: str) -> str:
    """Map aliases to a pocket-tts config stem and validate."""
    resolved = LANGUAGE_ALIASES.get(language, language)
    if resolved not in LANGUAGES:
        click.echo(f"Error: Unknown language: {language}", err=True)
        click.echo(f"Available: {', '.join(LANGUAGES)}", err=True)
        click.echo(f"Aliases: {', '.join(sorted(LANGUAGE_ALIASES))}", err=True)
        sys.exit(1)
    return resolved


def default_voice_for_language(language: str) -> str:
    for key, voice in DEFAULT_VOICE_FOR_LANGUAGE.items():
        if key in language:
            return voice
    return "alba"


@click.command()
@click.argument("text")
@click.option(
    "-v",
    "--voice",
    default=None,
    help="Voice name or path to audio file for cloning (default depends on language)",
)
@click.option(
    "-l",
    "--language",
    default="english",
    help="Model language (english, spanish, german, italian, portuguese, french_24l, …)",
)
@click.option(
    "-o", "--out", "output", default="/tmp/tts_output.wav", help="Output file path"
)
@click.option("--ogg", is_flag=True, help="Convert output to OGG format")
@click.option("-q", "--quiet", is_flag=True, help="Suppress progress messages")
def main(
    text: str, voice: str | None, language: str, output: str, ogg: bool, quiet: bool
):
    """Generate speech from TEXT using Pocket TTS."""
    load_env()

    import scipy.io.wavfile
    from pocket_tts import TTSModel

    language = resolve_language(language)
    if voice is None:
        voice = default_voice_for_language(language)

    # Determine voice source
    voice_arg = voice
    bundled_voice = VOICES_DIR / f"{voice}.ogg"
    cloning = False

    if bundled_voice.exists():
        voice_arg = str(bundled_voice)
        cloning = True
    elif Path(voice).exists():
        voice_arg = voice
        cloning = True
    elif voice not in PRESET_VOICES:
        bundled = (
            [f.stem for f in VOICES_DIR.glob("*.ogg")] if VOICES_DIR.exists() else []
        )
        click.echo(f"Error: Unknown voice: {voice}", err=True)
        click.echo(f"Available presets: {', '.join(PRESET_VOICES)}", err=True)
        if bundled:
            click.echo(f"Bundled clones: {', '.join(bundled)}", err=True)
        sys.exit(1)

    if cloning and not os.environ.get("HF_TOKEN"):
        click.echo(
            "Warning: HF_TOKEN not set. Voice cloning requires accepting "
            "https://huggingface.co/kyutai/pocket-tts terms and a token.",
            err=True,
        )

    # Determine output path
    wav_output = output
    if ogg:
        wav_output = output.rsplit(".", 1)[0] + ".wav"

    try:
        if not quiet:
            click.echo(f"Loading model ({language})...", err=True)
        tts_model = TTSModel.load_model(language=language)

        if not quiet:
            click.echo(f"Loading voice: {voice_arg}", err=True)
        voice_state = tts_model.get_state_for_audio_prompt(voice_arg)  # type: ignore[invalid-argument-type]

        if not quiet:
            click.echo("Generating audio...", err=True)
        audio = tts_model.generate_audio(voice_state, text)  # type: ignore[too-many-positional-arguments]

        # Write int16 PCM WAV — pocket-tts voice cloning uses wave.open (no float WAV).
        pcm_i16 = (audio.detach().cpu().clamp(-1, 1) * 32767).short().numpy()
        scipy.io.wavfile.write(wav_output, tts_model.sample_rate, pcm_i16)
    except Exception as e:
        click.echo(f"Error generating speech: {e}", err=True)
        sys.exit(1)

    if ogg:
        ogg_output = output.rsplit(".", 1)[0] + ".ogg"
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    wav_output,
                    "-c:a",
                    "libopus",
                    "-b:a",
                    "64k",
                    ogg_output,
                ],
                capture_output=True,
                check=True,
            )
            os.remove(wav_output)
            click.echo(ogg_output)
        except FileNotFoundError:
            if not quiet:
                click.echo("Warning: ffmpeg not found, keeping WAV format", err=True)
            click.echo(wav_output)
        except subprocess.CalledProcessError:
            if not quiet:
                click.echo(
                    "Warning: ffmpeg conversion failed, keeping WAV format", err=True
                )
            click.echo(wav_output)
    else:
        click.echo(wav_output)


if __name__ == "__main__":
    main()
