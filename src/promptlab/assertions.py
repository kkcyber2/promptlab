"""Assertion evaluation."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class AssertionResult:
    kind: str
    passed: bool
    detail: str

    def public(self) -> dict[str, Any]:
        return {"kind": self.kind, "passed": self.passed, "detail": self.detail}


def token_similarity(a: str, b: str) -> float:
    """Jaccard similarity over lowercased word tokens."""
    left = set(re.findall(r"[a-z0-9]+", a.lower()))
    right = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def evaluate(output: str, assertion: dict[str, Any]) -> AssertionResult:
    """Evaluate one assertion against an output string."""
    if not isinstance(assertion, dict) or len(assertion) != 1:
        return AssertionResult("invalid", False, "an assertion must be a single-key object")
    kind, expected = next(iter(assertion.items()))

    if kind == "contains":
        ok = str(expected) in output
        return AssertionResult(kind, ok, f"expected to contain {expected!r}")
    if kind == "not_contains":
        ok = str(expected) not in output
        return AssertionResult(kind, ok, f"expected NOT to contain {expected!r}")
    if kind == "equals":
        ok = output.strip() == str(expected).strip()
        return AssertionResult(kind, ok, f"expected exactly {expected!r}")
    if kind == "regex":
        try:
            ok = re.search(str(expected), output) is not None
        except re.error as exc:
            return AssertionResult(kind, False, f"invalid regex: {exc}")
        return AssertionResult(kind, ok, f"expected to match /{expected}/")
    if kind == "max_words":
        count = len(output.split())
        return AssertionResult(kind, count <= int(expected), f"{count} words, max {expected}")
    if kind == "min_words":
        count = len(output.split())
        return AssertionResult(kind, count >= int(expected), f"{count} words, min {expected}")
    if kind == "json_fields":
        try:
            payload = json.loads(output)
        except (ValueError, TypeError):
            return AssertionResult(kind, False, "output is not valid JSON")
        if not isinstance(payload, dict):
            return AssertionResult(kind, False, "output is not a JSON object")
        missing = [f for f in expected if f not in payload]
        return AssertionResult(
            kind, not missing, f"missing fields: {missing}" if missing else "all fields present"
        )
    if kind == "similarity":
        reference = str(expected.get("reference", ""))
        threshold = float(expected.get("threshold", 0.6))
        score = token_similarity(output, reference)
        return AssertionResult(
            kind, score >= threshold, f"similarity {score:.3f} vs threshold {threshold}"
        )
    return AssertionResult(kind, False, f"unknown assertion kind {kind!r}")
