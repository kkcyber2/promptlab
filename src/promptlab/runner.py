"""Run a suite against a model callable."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .assertions import AssertionResult, evaluate
from .suite import Case, Suite

# A model takes (rendered_prompt, case) and returns the output text.
Model = Callable[[str, Case], str]


@dataclass
class CaseResult:
    case_id: str
    output: str
    passed: bool
    assertions: list[AssertionResult] = field(default_factory=list)
    error: str | None = None

    def public(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "output": self.output,
            "passed": self.passed,
            "assertions": [a.public() for a in self.assertions],
            "error": self.error,
        }


@dataclass
class Report:
    suite_name: str
    results: list[CaseResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def failures(self) -> list[CaseResult]:
        return [r for r in self.results if not r.passed]

    def failing_assertions(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for result in self.results:
            for assertion in result.assertions:
                if not assertion.passed:
                    counts[assertion.kind] = counts.get(assertion.kind, 0) + 1
        return counts

    def public(self) -> dict[str, Any]:
        return {
            "suite": self.suite_name,
            "total": self.total,
            "passed": self.passed,
            "pass_rate": round(self.pass_rate, 4),
            "failing_assertions": self.failing_assertions(),
            "results": [r.public() for r in self.results],
        }


def render_prompt(template: str, case: Case) -> str:
    """Substitute {{input}} and {{id}} into the prompt template."""
    return template.replace("{{input}}", case.input).replace("{{id}}", case.id)


def run_case(template: str, case: Case, model: Model) -> CaseResult:
    try:
        output = model(render_prompt(template, case), case)
    except Exception as exc:  # a model failure is a case failure, not a crash
        return CaseResult(case_id=case.id, output="", passed=False, error=f"{type(exc).__name__}: {exc}")
    results = [evaluate(output, assertion) for assertion in case.assertions]
    return CaseResult(
        case_id=case.id,
        output=output,
        passed=all(r.passed for r in results),
        assertions=results,
    )


def run_suite(suite: Suite, model: Model, *, template: str = "{{input}}") -> Report:
    report = Report(suite_name=suite.name)
    for case in suite.cases:
        report.results.append(run_case(template, case, model))
    return report


def compare_reports(baseline: Report, current: Report) -> dict[str, Any]:
    """Diff two runs: which cases regressed, which improved, which are new."""
    before = {r.case_id: r.passed for r in baseline.results}
    after = {r.case_id: r.passed for r in current.results}
    regressed = [cid for cid, ok in after.items() if cid in before and before[cid] and not ok]
    fixed = [cid for cid, ok in after.items() if cid in before and not before[cid] and ok]
    added = [cid for cid in after if cid not in before]
    removed = [cid for cid in before if cid not in after]
    return {
        "regressed": sorted(regressed),
        "fixed": sorted(fixed),
        "added": sorted(added),
        "removed": sorted(removed),
        "pass_rate_delta": round(current.pass_rate - baseline.pass_rate, 4),
    }
