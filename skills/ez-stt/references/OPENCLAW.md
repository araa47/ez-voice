# OpenClaw Setup

This skill can be used with [OpenClaw](https://openclaw.dev) to automatically transcribe audio messages.

## SKILL.md Metadata

```yaml
metadata: {"openclaw":{"emoji":"🎙️","requires":{"bins":["ffmpeg"]}}}
```

## openclaw.json

Add this to your `openclaw.json` to enable automatic audio transcription:

```json
{
  "tools": {
    "media": {
      "audio": {
        "enabled": true,
        "models": [
          {
            "type": "cli",
            "command": "~/.openclaw/skills/ez-stt/scripts/stt.py",
            "args": ["--quiet", "{{MediaPath}}"],
            "timeoutSeconds": 30
          }
        ]
      }
    }
  }
}
```

The script will automatically send the transcript to the Matrix room when `--room-id` is provided.
