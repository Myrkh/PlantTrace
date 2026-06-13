from __future__ import annotations

import re

import pytest

from planttrace.rule_builder import (
    RuleBuildRequest,
    TEMPLATE_DOCUMENT,
    TEMPLATE_INITIALS,
    TEMPLATE_INSTRUMENT,
    TEMPLATE_LINE,
    TEMPLATE_REGEX,
    build_pattern,
    parse_prefixes,
)


def test_instrument_rule_builder_generates_project_tag_pattern() -> None:
    pattern = build_pattern(RuleBuildRequest(TEMPLATE_INSTRUMENT, prefixes="FV, PT", min_digits=3, max_digits=5))

    assert re.search(pattern, "FV1100")
    assert re.search(pattern, "PT-2045A")
    assert not re.search(pattern, "RJ45")


def test_line_rule_builder_uses_service_prefixes() -> None:
    pattern = build_pattern(RuleBuildRequest(TEMPLATE_LINE, prefixes="P, WW", allow_no_separator=False, allow_space=True))

    assert re.search(pattern, "10-P-12345")
    assert re.search(pattern, "4 WW 2201")
    assert not re.search(pattern, "FV-1100")


def test_document_and_initials_templates_are_constrained() -> None:
    doc_pattern = build_pattern(RuleBuildRequest(TEMPLATE_DOCUMENT, prefixes="HTI"))
    initials_pattern = build_pattern(RuleBuildRequest(TEMPLATE_INITIALS, prefixes="JDY, DBT"))

    assert re.search(doc_pattern, "HTI199-VEN-ELE-3799")
    assert re.search(initials_pattern, "JDY")
    assert not re.search(initials_pattern, "ABC")


def test_custom_regex_is_validated() -> None:
    assert build_pattern(RuleBuildRequest(TEMPLATE_REGEX, custom_pattern=r"\bFV\d{4}\b")) == r"\bFV\d{4}\b"
    with pytest.raises(re.error):
        build_pattern(RuleBuildRequest(TEMPLATE_REGEX, custom_pattern="["))


def test_prefix_parser_accepts_commas_and_semicolons() -> None:
    assert parse_prefixes(" fv;PT, fv ") == ["FV", "PT"]
