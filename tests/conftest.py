import json
import sys
from pathlib import Path

import pytest

RESOURCES_DIR = Path(__file__).parent / "resources"
PROJECT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(PROJECT_ROOT / "skills" / "ez-stt" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "skills" / "ez-tts" / "scripts"))


@pytest.fixture
def sample_wav():
    return str(RESOURCES_DIR / "sample.wav")


@pytest.fixture
def silence_wav():
    return str(RESOURCES_DIR / "silence.wav")


@pytest.fixture
def short_wav():
    return str(RESOURCES_DIR / "short.wav")


@pytest.fixture
def speech_wav():
    return str(RESOURCES_DIR / "speech_16k.wav")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Write e2e-summary.json for the CI Test Report when e2e tests ran."""
    e2e_items = [
        item
        for item in session.items
        if item.get_closest_marker("e2e") is not None
        and item.get_closest_marker("e2e_slow") is None
    ]
    if not e2e_items:
        return

    # Load via file path so this works even when `tests` isn't importable as a package.
    import importlib.util

    scenarios_path = Path(__file__).parent / "e2e_scenarios.py"
    spec = importlib.util.spec_from_file_location("e2e_scenarios", scenarios_path)
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    e2e_scenarios: dict[str, dict[str, str]] = module.E2E_SCENARIOS

    reports = getattr(session.config, "_e2e_reports", {})
    scenarios = []
    for item in e2e_items:
        cls = getattr(item, "cls", None)
        key = f"{cls.__name__}::{item.name}" if cls is not None else item.name
        meta = e2e_scenarios.get(key, {})
        rep = reports.get(item.nodeid, {})
        func = getattr(item, "function", None)
        docstring = (func.__doc__ or "") if func is not None else ""
        scenarios.append(
            {
                "nodeid": item.nodeid,
                "key": key,
                "title": meta.get("title", key),
                "covers": meta.get("covers", docstring),
                "stack": meta.get("stack", ""),
                "outcome": rep.get("outcome", "unknown"),
                "duration": rep.get("duration", 0.0),
                "longrepr": rep.get("longrepr", ""),
            }
        )

    summary = {
        "exitstatus": exitstatus,
        "scenarios": scenarios,
    }
    Path("e2e-summary.json").write_text(json.dumps(summary, indent=2) + "\n")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" and not (report.when == "setup" and report.skipped):
        return
    if item.get_closest_marker("e2e") is None:
        return
    store = item.config.__dict__.setdefault("_e2e_reports", {})
    # Prefer the call-phase report; keep setup-skip if call never runs.
    existing = store.get(item.nodeid)
    if existing and report.when == "setup":
        return
    longrepr = ""
    if report.failed and report.longrepr:
        longrepr = str(report.longrepr)[:500]
    store[item.nodeid] = {
        "outcome": report.outcome,
        "duration": float(report.duration or 0.0),
        "longrepr": longrepr,
    }
