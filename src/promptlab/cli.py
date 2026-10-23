"""Command line entry point."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runner import compare_reports, run_suite
from .suite import SuiteError, load_suite


def _echo_model(prompt: str, case) -> str:
    """Default model: echo the input, so the suite can be smoke-tested offline."""
    return case.input


def render(report) -> str:
    lines = [
        f"Suite  : {report.suite_name}",
        f"Result : {report.passed}/{report.total} passed ({report.pass_rate:.0%})",
        "",
    ]
    for result in report.results:
        mark = "PASS" if result.passed else "FAIL"
        lines.append(f"[{mark}] {result.case_id}")
        if result.error:
            lines.append(f"       error: {result.error}")
        for assertion in result.assertions:
            if not assertion.passed:
                lines.append(f"       {assertion.kind}: {assertion.detail}")
    failing = report.failing_assertions()
    if failing:
        lines.append("")
        lines.append(f"Failing assertion kinds: {failing}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="promptlab", description="Prompt regression testing")
    parser.add_argument("suite", help="path to the suite JSON")
    parser.add_argument("--prompt", help="path to a prompt template file")
    parser.add_argument("--json", metavar="PATH", help="write the report as JSON")
    parser.add_argument("--baseline", metavar="PATH", help="compare against a previous report")
    parser.add_argument("--min-pass-rate", type=float, default=1.0)
    args = parser.parse_args(argv)

    try:
        suite = load_suite(args.suite)
    except (SuiteError, OSError) as exc:
        print(f"could not load suite: {exc}", file=sys.stderr)
        return 2

    template = "{{input}}"
    if args.prompt:
        try:
            template = Path(args.prompt).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"could not read prompt: {exc}", file=sys.stderr)
            return 2

    report = run_suite(suite, _echo_model, template=template)
    print(render(report))

    if args.baseline:
        try:
            baseline_payload = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"could not read baseline: {exc}", file=sys.stderr)
            return 2
        from .runner import CaseResult, Report

        baseline = Report(
            suite_name=baseline_payload.get("suite", "baseline"),
            results=[
                CaseResult(case_id=r["case_id"], output=r.get("output", ""), passed=r["passed"])
                for r in baseline_payload.get("results", [])
            ],
        )
        print()
        print(json.dumps(compare_reports(baseline, report), indent=2))

    if args.json:
        Path(args.json).write_text(json.dumps(report.public(), indent=2), encoding="utf-8")
        print(f"\nJSON report written to {args.json}")

    return 0 if report.pass_rate >= args.min_pass_rate else 1


if __name__ == "__main__":
    sys.exit(main())
