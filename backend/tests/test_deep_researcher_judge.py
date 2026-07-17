"""Unit tests for app.deep_researcher.judge text helpers."""
from app.deep_researcher import judge
from app.deep_researcher.schemas import DroppedResource, GapIn, ValidationResult


def test_gaps_text_formats_each_gap():
    gaps = [
        GapIn(skill="Kubernetes", category="devops", relevance=9, difficulty="hard", prerequisites=["Docker"]),
        GapIn(skill="gRPC", category="backend", relevance=6, difficulty="medium"),
    ]
    text = judge._gaps_text(gaps)
    assert "Kubernetes (rel=9, hard, prereqs=['Docker'])" in text
    assert "gRPC (rel=6, medium, prereqs=[])" in text
    assert text.count("\n") == 1  # two lines


def test_validation_text_when_nothing_dropped():
    assert judge._validation_text(None) == "(no resources dropped — all links grounded and live)"
    assert judge._validation_text(ValidationResult(checked=3, kept=3)) == (
        "(no resources dropped — all links grounded and live)"
    )


def test_validation_text_lists_dropped():
    vr = ValidationResult(
        checked=2,
        kept=1,
        dropped=[DroppedResource(milestone_skill="Python", title="Bad Doc", url="https://x/y", reason="dead_link")],
    )
    text = judge._validation_text(vr)
    assert "1/2 resources kept" in text
    assert "[Python] Bad Doc — dead_link (https://x/y)" in text
