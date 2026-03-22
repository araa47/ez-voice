#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pocket-tts",
#     "scipy",
#     "soundfile",
#     "click",
# ]
# ///
"""Local text-to-speech using Kyutai Pocket TTS. Supports preset voices and voice cloning."""

import os
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import click  # noqa: E402

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


@click.command()
@click.argument("text")
@click.option(
    "-v", "--voice", default="alba", help="Voice name or path to audio file for cloning"
)
@click.option(
    "-o", "--out", "output", default="/tmp/tts_output.wav", help="Output file path"
)
@click.option("--ogg", is_flag=True, help="Convert output to OGG format")
@click.option("-q", "--quiet", is_flag=True, help="Suppress progress messages")
def main(text: str, voice: str, output: str, ogg: bool, quiet: bool):
    """Generate speech from TEXT using Pocket TTS."""
    load_env()

    import scipy.io.wavfile
    from pocket_tts import TTSModel

    # Determine voice source
    voice_arg = voice
    bundled_voice = VOICES_DIR / f"{voice}.ogg"

    if bundled_voice.exists():
        # Bundled cloned voice
        voice_arg = str(bundled_voice)
        if not os.environ.get("HF_TOKEN"):
            click.echo("Warning: HF_TOKEN not set. Voice cloning may fail.", err=True)
    elif Path(voice).exists():
        # File path for voice cloning
        voice_arg = voice
        if not os.environ.get("HF_TOKEN"):
            click.echo("Warning: HF_TOKEN not set. Voice cloning may fail.", err=True)
    elif voice not in PRESET_VOICES:
        bundled = (
            [f.stem for f in VOICES_DIR.glob("*.ogg")] if VOICES_DIR.exists() else []
        )
        click.echo(f"Error: Unknown voice: {voice}", err=True)
        click.echo(f"Available presets: {', '.join(PRESET_VOICES)}", err=True)
        if bundled:
            click.echo(f"Bundled clones: {', '.join(bundled)}", err=True)
        sys.exit(1)

    # Determine output path
    wav_output = output
    if ogg:
        wav_output = output.rsplit(".", 1)[0] + ".wav"

    # Generate speech using correct API
    try:
        if not quiet:
            click.echo("Loading model...", err=True)
        tts_model = TTSModel.load_model()

        if not quiet:
            click.echo(f"Loading voice: {voice_arg}", err=True)
        voice_state = tts_model.get_state_for_audio_prompt(voice_arg)  # type: ignore[invalid-argument-type]

        if not quiet:
            click.echo("Generating audio...", err=True)
        audio = tts_model.generate_audio(voice_state, text)  # type: ignore[too-many-positional-arguments]

        # Save to WAV file
        scipy.io.wavfile.write(wav_output, tts_model.sample_rate, audio.numpy())
    except Exception as e:
        click.echo(f"Error generating speech: {e}", err=True)
        sys.exit(1)

    # Convert to OGG if requested
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
