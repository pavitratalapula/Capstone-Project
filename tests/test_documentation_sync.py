from pathlib import Path

from src.documentation_sync import generate_report


def test_generate_report_includes_summary_and_inventory(tmp_path):
    repo_root = tmp_path / "demo_repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# Demo\n\nExample project\n", encoding="utf-8")
    (repo_root / "src").mkdir()
    (repo_root / "src" / "service.py").write_text("def status():\n    return 'ok'\n", encoding="utf-8")
    (repo_root / "tests").mkdir()
    (repo_root / "tests" / "test_service.py").write_text("def test_status():\n    assert True\n", encoding="utf-8")
    (repo_root / "docs").mkdir()

    report, warnings = generate_report(repo_root)

    assert "# Documentation Sync Report" in report
    assert "README.md" in report
    assert "service.py" in report
    assert warnings == []


def test_generate_report_reports_missing_repo(tmp_path):
    missing_repo = tmp_path / "not_here"

    try:
        generate_report(missing_repo)
        assert False, "Expected FileNotFoundError for missing repository"
    except FileNotFoundError:
        assert True
