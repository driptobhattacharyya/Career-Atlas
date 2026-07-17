"""Unit tests for app.github_analysis.service pure helpers."""
from app.github_analysis import service
from app.github_analysis.service import SkillEvidence


# ── select_files ─────────────────────────────────────────────────────────────

def test_select_files_manifest_first_ordering():
    tree = [
        "src/app.py",
        "README.md",
        "requirements.txt",
        "main.py",
        "utils/helpers.py",
    ]
    selected = service.select_files(tree)
    # manifests, then readme, then entrypoints, then remaining shallow source
    assert selected[0] == "requirements.txt"
    assert selected[1] == "README.md"
    # main.py and src/app.py are both entrypoints -> they precede utils/helpers.py
    assert selected.index("main.py") < selected.index("utils/helpers.py")
    assert selected.index("src/app.py") < selected.index("utils/helpers.py")


def test_select_files_skips_vendor_dirs_tests_and_deep_source():
    tree = [
        "node_modules/pkg/index.js",
        "src/a/b/c/deep.py",   # depth > 3 -> excluded from source bucket
        "tests/test_x.py",     # 'test' in name -> excluded
        "app.py",
    ]
    selected = service.select_files(tree)
    assert "node_modules/pkg/index.js" not in selected
    assert "src/a/b/c/deep.py" not in selected
    assert "tests/test_x.py" not in selected
    assert "app.py" in selected


def test_select_files_respects_cap():
    tree = [f"module{i}.py" for i in range(30)]
    assert len(service.select_files(tree, cap=5)) == 5


# ── _filter_evidence ─────────────────────────────────────────────────────────

def test_filter_evidence_keeps_path_backed_skill():
    skills = [SkillEvidence(skill="FastAPI", evidence="requirements.txt", confidence="high")]
    out = service._filter_evidence(skills, ["requirements.txt"], {})
    assert out[0].confidence == "high"


def test_filter_evidence_keeps_language_backed_skill():
    skills = [SkillEvidence(skill="Python", evidence="python is dominant", confidence="high")]
    out = service._filter_evidence(skills, [], {"Python": 90.0})
    assert out[0].confidence == "high"


def test_filter_evidence_caps_unbacked_skill_to_low():
    skills = [SkillEvidence(skill="Rust", evidence="I feel like they know rust", confidence="high")]
    out = service._filter_evidence(skills, ["package.json"], {"JavaScript": 100.0})
    assert out[0].confidence == "low"
    assert out[0].skill == "Rust"


# ── _commit_context ──────────────────────────────────────────────────────────

def test_commit_context_no_commits():
    assert service._commit_context({"commit_count": 0}) == "no owner-authored commits found"
    assert service._commit_context({}) == "no owner-authored commits found"


def test_commit_context_with_span():
    ctx = service._commit_context({
        "commit_count": 12,
        "first_commit_at": "2023-01-15T00:00:00Z",
        "last_commit_at": "2023-06-20T00:00:00Z",
    })
    assert ctx == "12 owner-authored commits between 2023-01-15 and 2023-06-20"


def test_commit_context_marks_100_plus():
    ctx = service._commit_context({"commit_count": 150})
    assert ctx.startswith("150+ owner-authored commits")
