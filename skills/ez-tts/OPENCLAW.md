# OpenClaw Setup

This skill can be used with [OpenClaw](https://openclaw.dev) to generate voice messages.

## SKILL.md Metadata

```yaml
metadata: {"openclaw":{"emoji":"🔊","requires":{"bins":[]}}}
```

## Usage with OpenClaw

```bash
uv run ~/.openclaw/skills/ez-tts/scripts/tts.py "Hello world" --ogg
```

The script sources `~/.env` to load `HF_TOKEN` for voice cloning support.
