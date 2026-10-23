import json

import pytest

from promptlab.suite import SuiteError, load_suite, parse_suite


def test_parse_a_minimal_suite():
    suite = parse_suite({"name": "s", "cases": [{"id": "a", "input": "x"}]})
    assert suite.name == "s"
    assert suite.cases[0].id == "a"


def test_missing_cases_is_an_error():
    with pytest.raises(SuiteError):
        parse_suite({"name": "s"})


def test_empty_cases_is_an_error():
    with pytest.raises(SuiteError):
        parse_suite({"name": "s", "cases": []})


def test_duplicate_ids_are_rejected():
    with pytest.raises(SuiteError):
        parse_suite({"cases": [{"id": "a", "input": "1"}, {"id": "a", "input": "2"}]})


def test_case_without_input_is_rejected():
    with pytest.raises(SuiteError):
        parse_suite({"cases": [{"id": "a"}]})


def test_assertions_must_be_a_list():
    with pytest.raises(SuiteError):
        parse_suite({"cases": [{"id": "a", "input": "x", "assertions": "nope"}]})


def test_ids_are_generated_when_absent():
    suite = parse_suite({"cases": [{"input": "x"}]})
    assert suite.cases[0].id == "case_0"


def test_by_tag_filters():
    suite = parse_suite(
        {"cases": [{"id": "a", "input": "1", "tags": ["x"]}, {"id": "b", "input": "2", "tags": ["y"]}]}
    )
    assert [c.id for c in suite.by_tag("x")] == ["a"]


def test_load_suite_from_disk(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"cases": [{"id": "a", "input": "x"}]}))
    assert load_suite(path).cases[0].id == "a"


def test_load_suite_rejects_bad_json(tmp_path):
    path = tmp_path / "s.json"
    path.write_text("{not json")
    with pytest.raises(SuiteError):
        load_suite(path)


def test_example_suite_loads():
    from pathlib import Path

    example = Path(__file__).resolve().parents[1] / "examples" / "suite.json"
    suite = load_suite(example)
    assert len(suite.cases) == 3
