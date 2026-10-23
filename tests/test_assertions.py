import pytest

from promptlab.assertions import evaluate, token_similarity


def test_contains_passes_and_fails():
    assert evaluate("hello world", {"contains": "world"}).passed is True
    assert evaluate("hello world", {"contains": "mars"}).passed is False


def test_not_contains():
    assert evaluate("hello", {"not_contains": "bye"}).passed is True
    assert evaluate("hello bye", {"not_contains": "bye"}).passed is False


def test_equals_ignores_surrounding_whitespace():
    assert evaluate("  ok  ", {"equals": "ok"}).passed is True


def test_regex():
    assert evaluate("abc123", {"regex": r"\d+"}).passed is True
    assert evaluate("abc", {"regex": r"\d+"}).passed is False


def test_invalid_regex_fails_cleanly():
    result = evaluate("abc", {"regex": "("})
    assert result.passed is False
    assert "invalid regex" in result.detail


def test_max_and_min_words():
    assert evaluate("one two three", {"max_words": 3}).passed is True
    assert evaluate("one two three four", {"max_words": 3}).passed is False
    assert evaluate("one two", {"min_words": 2}).passed is True
    assert evaluate("one", {"min_words": 2}).passed is False


def test_json_fields():
    assert evaluate('{"a":1,"b":2}', {"json_fields": ["a", "b"]}).passed is True
    assert evaluate('{"a":1}', {"json_fields": ["a", "b"]}).passed is False


def test_json_fields_rejects_non_json():
    assert evaluate("not json", {"json_fields": ["a"]}).passed is False


def test_json_fields_rejects_an_array():
    assert evaluate("[1,2]", {"json_fields": ["a"]}).passed is False


def test_similarity():
    result = evaluate("the quick brown fox", {"similarity": {"reference": "the quick brown fox", "threshold": 0.9}})
    assert result.passed is True


def test_similarity_below_threshold_fails():
    result = evaluate("completely different", {"similarity": {"reference": "the quick brown fox", "threshold": 0.9}})
    assert result.passed is False


def test_token_similarity_edge_cases():
    assert token_similarity("", "") == 1.0
    assert token_similarity("a", "") == 0.0
    assert token_similarity("a b", "a b") == 1.0


def test_unknown_assertion_kind_fails():
    assert evaluate("x", {"nonsense": 1}).passed is False


def test_multi_key_assertion_is_invalid():
    assert evaluate("x", {"contains": "x", "equals": "x"}).passed is False
