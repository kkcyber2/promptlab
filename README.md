# PromptLab

Regression testing for prompts. You keep a golden set of inputs and the outputs you
expect; PromptLab runs a prompt against the set, scores each case, and fails the build
when quality drops.

Prompts change constantly and silently. Without a test suite, "I tweaked the wording"
is indistinguishable from "I broke extraction for every invoice with a foreign
currency".

## How scoring works

Each case declares one or more **assertions**:

| Assertion | Meaning |
|---|---|
| `contains` | the output must contain a substring |
| `not_contains` | the output must not contain a substring |
| `regex` | the output must match a pattern |
| `json_fields` | the output must be JSON with these fields present |
| `equals` | the output must equal a value exactly |
| `max_words` / `min_words` | length bounds |
| `similarity` | token-overlap similarity to a reference, above a threshold |

A case passes when every assertion passes. The suite reports a pass rate and a
per-assertion breakdown, so a regression points at the exact behaviour that changed.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
promptlab examples/suite.json --prompt examples/prompt.txt
promptlab examples/suite.json --prompt examples/prompt.txt --json report.json
```

## As a library

```python
from promptlab.suite import load_suite
from promptlab.runner import run_suite

suite = load_suite("examples/suite.json")
report = run_suite(suite, lambda prompt, case: my_model(prompt, case.input))
print(report.pass_rate)
```

## Tests

```bash
pytest -q
```

## License

MIT — see `LICENSE`.
