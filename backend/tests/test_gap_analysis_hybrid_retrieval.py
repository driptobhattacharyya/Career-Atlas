"""Unit tests for app.gap_analysis.hybrid_retrieval role-slug resolution."""
from app.gap_analysis import hybrid_retrieval


def test_resolve_role_slug_canonical_titles():
    assert hybrid_retrieval.resolve_role_slug("Machine Learning Engineer") == "ml_engineer"
    assert hybrid_retrieval.resolve_role_slug("Backend Engineer") == "swe_backend"
    assert hybrid_retrieval.resolve_role_slug("Data Scientist") == "data_scientist"


def test_resolve_role_slug_is_case_and_whitespace_insensitive():
    assert hybrid_retrieval.resolve_role_slug("  FRONTEND ENGINEER  ") == "frontend_engineer"


def test_resolve_role_slug_aliases():
    assert hybrid_retrieval.resolve_role_slug("Full Stack Engineer") == "fullstack_engineer"
    assert hybrid_retrieval.resolve_role_slug("Product Manager") == "product_manager"
    assert hybrid_retrieval.resolve_role_slug("Software Engineer (Backend)") == "swe_backend"


def test_resolve_role_slug_fallback_slugifies_unknown_role():
    assert hybrid_retrieval.resolve_role_slug("Growth Marketer") == "growth_marketer"
    # Parentheses are stripped in the fallback path.
    assert hybrid_retrieval.resolve_role_slug("Nurse (ICU)") == "nurse_icu"
