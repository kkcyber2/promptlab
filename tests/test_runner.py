from promptlab.runner import compare_reports, render_prompt, run_case, run_suite
from promptlab.suite import Case, parse_suite


def test_render_prompt_substitutes_input():
    case = Case(id="a", input="hello")
    assert render_prompt("Q: {{input}}", case) == "Q: hello"


def test_render_prompt_substitutes_id():
    case = Case(id="abc", input="x")
    assert render_prompt("id={{id}}", case) == "id=abc"


def test_run_case_passes_when_assertions_hold():
    case = Case(id="a", input="x", assertions=[{"contains": "x"}])
    result = run_case("{{input}}", case, lambda p, c: c.input)
    assert result.passed is True


def test_run_case_fails_when_an_assertion_fails():
    case = Case(id="a", input="x", assertions=[{"contains": "y"}])
    result = run_case("{{input}}", case, lambda p, c: c.input)
    assert result.passed is False


def test_model_exception_becomes_a_case_failure():
    def boom(prompt, case):
        raise RuntimeError("model exploded")

    case = Case(id="a", input="x", assertions=[{"contains": "x"}])
    result = run_case("{{input}}", case, boom)
    assert result.passed is False
    assert "model exploded" in result.error


def test_run_suite_reports_pass_rate():
    suite = parse_suite(
        {
            "name": "s",
            "cases": [
                {"id": "a", "input": "x", "assertions": [{"contains": "x"}]},
                {"id": "b", "input": "y", "assertions": [{"contains": "z"}]},
            ],
        }
    )
    report = run_suite(suite, lambda p, c: c.input)
    assert report.total == 2
    assert report.passed == 1
    assert report.pass_rate == 0.5


def test_failing_assertions_are_grouped():
    suite = parse_suite(
        {"cases": [{"id": "a", "input": "x", "assertions": [{"contains": "z"}, {"max_words": 0}]}]}
    )
    report = run_suite(suite, lambda p, c: c.input)
    assert report.failing_assertions() == {"contains": 1, "max_words": 1}


def test_compare_reports_detects_a_regression():
    suite = parse_suite({"cases": [{"id": "a", "input": "x", "assertions": [{"contains": "x"}]}]})
    good = run_suite(suite, lambda p, c: c.input)
    bad = run_suite(suite, lambda p, c: "nope")
    diff = compare_reports(good, bad)
    assert diff["regressed"] == ["a"]
    assert diff["pass_rate_delta"] < 0


def test_compare_reports_detects_a_fix():
    suite = parse_suite({"cases": [{"id": "a", "input": "x", "assertions": [{"contains": "x"}]}]})
    bad = run_suite(suite, lambda p, c: "nope")
    good = run_suite(suite, lambda p, c: c.input)
    assert compare_reports(bad, good)["fixed"] == ["a"]


def test_compare_reports_handles_added_and_removed():
    one = parse_suite({"cases": [{"id": "a", "input": "x"}]})
    two = parse_suite({"cases": [{"id": "b", "input": "x"}]})
    diff = compare_reports(run_suite(one, lambda p, c: c.input), run_suite(two, lambda p, c: c.input))
    assert diff["added"] == ["b"]
    assert diff["removed"] == ["a"]


def test_empty_report_pass_rate_is_zero():
    from promptlab.runner import Report

    assert Report(suite_name="x").pass_rate == 0.0
