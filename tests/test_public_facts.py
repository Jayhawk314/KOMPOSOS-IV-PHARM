import sqlite3
from pathlib import Path

from validation.repurposing_benchmark import (
    DB_PATH,
    drug_disease_pairs,
    load_full_typed_view,
)


REPO = Path(__file__).resolve().parent.parent


def _text(relative_path: str) -> str:
    return (REPO / relative_path).read_text(encoding="utf-8")


def test_current_graph_counts_match_public_facts():
    category, missing = load_full_typed_view(DB_PATH)
    drugs, diseases, positives = drug_disease_pairs(category)
    object_types = {obj.name: obj.type_name for obj in category.objects()}
    terminal = [
        mor for mor in category.morphisms()
        if object_types.get(mor.target) == "Disease"
        and object_types.get(mor.source) not in {"Drug", "Disease"}
    ]

    assert missing == []
    assert len(category.objects()) == 1_143
    assert len(category.morphisms()) == 2_038
    assert len(drugs) == 757
    assert len(diseases) == 20
    assert len(positives) == 44
    assert sum(mor.name == "driver_of" for mor in terminal) == 60
    assert sum(mor.name == "associated_with" for mor in terminal) == 746

    with sqlite3.connect(REPO / DB_PATH) as conn:
        assert conn.execute("SELECT COUNT(*) FROM morphisms").fetchone()[0] == 2_462


def test_ui_does_not_turn_missing_local_labels_into_regulatory_facts():
    app = _text("app.py")

    assert '_ec_label == "POSITIVE"' not in app
    assert '"recorded" if _ec_label == "APPROVED" else "not recorded"' in app
    assert "Local NOT_APPROVED means absent" in app
    assert "Only 60" in app
    for stale in (
        "Only 37",
        "603 abstentions",
        "957 actually-scored",
        "**0.9642**",
        "NULL for all 2,439",
        "NO approval on record",
    ):
        assert stale not in app


def test_about_page_matches_repository_license_and_graph_scopes():
    app = _text("app.py")
    readme = _text("README.md")

    assert "Software source code:** Apache License 2.0" in app
    assert "No separate KOMPOSOS commercial" in app
    assert "Bundled third-party data retain their" in app
    assert "protein/biological nodes" in app
    assert "The raw database has {g['database_morphisms']:,}" in app
    assert "the source of every" in app
    assert "Commercial dual license" not in app
    assert "Commercial dual license" not in readme


def test_current_docs_match_reproducible_funnel_and_packaging_state():
    readme = _text("README.md")
    honest = _text("HONEST_VALUE.md")
    claude = _text("CLAUDE.md")

    assert "31/44 (70%)" in readme
    assert "**14.1x**" in readme
    assert "screening **24%**" in readme
    assert "setuptools.build_meta" in readme
    assert "31/44" in honest and "14.1×" in honest
    assert "**153 have a complete" in claude
    assert "**1,337" in claude
    assert "64 of 15,140" in claude

    combined = "\n".join((readme, honest, claude))
    assert "+0.0251" in honest
    assert "+0.0251" in claude
    for stale in (
        "32/44 (73%)",
        "14.5× enrichment",
        "14.5x",
        "does not currently `pip install`",
        "does not `pip install`",
        "128 have a complete",
        "1,206 reachable",
        "50 of 15,140",
        "~+0.05",
    ):
        assert stale not in combined

    funnel_source = _text("validation/enrichment_funnel.py")
    assert "Performance on genuinely novel pairs is unmeasured" in funnel_source
    assert "Novel-pair precision is lower" not in funnel_source


def test_old_overviews_are_explicitly_historical():
    for path in (
        "docs/CURRENT_STATE.md",
        "docs/TECHNICAL_OVERVIEW.md",
        "docs/SYSTEM_SUMMARY.md",
    ):
        assert "HISTORICAL" in _text(path).splitlines()[0]
