"""Scenario metadata for e2e tests — used by CI Test Report comments."""

# Keys are pytest nodeid suffixes: ClassName::test_name
E2E_SCENARIOS: dict[str, dict[str, str]] = {
    "TestTtsSttRoundtrip::test_generate_then_transcribe": {
        "title": "English TTS → STT roundtrip",
        "covers": "Preset voice `alba`, english model, whisper-base transcription of spoken keywords",
        "stack": "TTS english/alba → STT whisper/base",
    },
    "TestVoiceCloning::test_clone_from_generated_sample": {
        "title": "Voice cloning",
        "covers": "Generate a PCM reference clip, clone from that wav, then STT the clone",
        "stack": "TTS clone(local wav) → STT whisper/base",
    },
    "TestMultilingual::test_spanish_preset_roundtrip": {
        "title": "Spanish multilingual",
        "covers": "Spanish model + `lola` voice, whisper-base keyword check on Spanish speech",
        "stack": "TTS spanish/lola → STT whisper/base",
    },
    "TestSttFixture::test_whisper_base_on_speech_fixture": {
        "title": "STT fixture smoke",
        "covers": "Transcribe the checked-in 16 kHz speech fixture with whisper-base",
        "stack": "STT whisper/base ← tests/resources/speech_16k.wav",
    },
}
