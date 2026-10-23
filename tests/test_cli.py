import json
from pathlib import Path

from promptlab.cli import main, render
from promptlab.runner import run_suite
from promptlab.suite import load_suite

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_example_suite_passes_with_the_echo_model():
    suite = load_suite(EXAMPLES / "suite.json")
    report = run_suite(suite, lambda p, c: c.input)
    assert report.pass_rate == 1.0


def test_render_lists_every_case():
    suite = load_suite(EXAMPLES / "suite.json")
    text = render(run_suite(suite, lambda p, c: c.input))
    assert "usd-simple" in text
    assert "PASS" in text


def test_cli_runs_the_example(tmp_path):
    out = tmp_path / "r.json"
    code = main([str(EXAMPLES / "suite.json"), "--prompt", str(EXAMPLES / "prompt.txt"), "--json", str(out)])
    assert code == 0
    assert json.loads(out.read_text())["pass_rate"] == 1.0


def test_cli_missing_suite_returns_2():
    assert main(["/nonexistent/suite.json"]) == 2


def test_cli_min_pass_rate_gate(tmp_path):
    suite_path = tmp_path / "s.json"
    suite_path.write_text(json.dumps({"cases": [{"id": "a", "input": "x", "assertions": [{"contains": "zzz"}]}]}))
    assert main([str(suite_path), "--min-pass-rate", "0.5"]) == 1
