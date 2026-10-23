"""Loading and validating a golden set."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class SuiteError(ValueError):
    """The suite file is malformed."""


@dataclass
class Case:
    id: str
    input: str
    assertions: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    reference: str | None = None


@dataclass
class Suite:
    name: str
    cases: list[Case]

    def by_tag(self, tag: str) -> list[Case]:
        return [c for c in self.cases if tag in c.tags]


def load_suite(path: str | Path) -> Suite:
    """Read a suite from a JSON file and validate its shape."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except ValueError as exc:
        raise SuiteError(f"suite is not valid JSON: {exc}") from exc
    return parse_suite(payload)


def parse_suite(payload: dict[str, Any]) -> Suite:
    if not isinstance(payload, dict):
        raise SuiteError("suite must be a JSON object")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise SuiteError("suite must have a non-empty 'cases' list")
    cases: list[Case] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_cases):
        if not isinstance(raw, dict):
            raise SuiteError(f"case {index} is not an object")
        case_id = str(raw.get("id") or f"case_{index}")
        if case_id in seen:
            raise SuiteError(f"duplicate case id {case_id!r}")
        seen.add(case_id)
        if "input" not in raw:
            raise SuiteError(f"case {case_id!r} has no 'input'")
        assertions = raw.get("assertions", [])
        if not isinstance(assertions, list):
            raise SuiteError(f"case {case_id!r} assertions must be a list")
        cases.append(
            Case(
                id=case_id,
                input=str(raw["input"]),
                assertions=assertions,
                tags=[str(t) for t in raw.get("tags", [])],
                reference=raw.get("reference"),
            )
        )
    return Suite(name=str(payload.get("name", "unnamed")), cases=cases)
