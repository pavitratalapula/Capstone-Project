import pytest

from src.documentation_sync import generate_report, main


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

    with pytest.raises(FileNotFoundError, match="does not exist"):
        generate_report(missing_repo)


def test_report_is_deterministic_and_excludes_output_file(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# Demo\n", encoding="utf-8")
    output_path = repo_root / "docs" / "report.md"
    output_path.parent.mkdir()

    monkeypatch.setattr(
        "sys.argv",
        ["documentation_sync", "--repo", str(repo_root), "--output", str(output_path)],
    )
    assert main() == 0
    first_report = output_path.read_bytes()
    assert "docs/report.md" not in output_path.read_text(encoding="utf-8")
    assert "Generated:" not in output_path.read_text(encoding="utf-8")

    assert main() == 0
    assert output_path.read_bytes() == first_report


def test_hidden_directories_are_skipped(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# Demo\n", encoding="utf-8")
    hidden_dir = repo_root / ".github"
    hidden_dir.mkdir()
    (hidden_dir / "copilot-instructions.md").write_text("instructions\n", encoding="utf-8")

    report, _ = generate_report(repo_root)

    assert "README.md" in report
    assert ".github/copilot-instructions.md" not in report


def test_empty_and_trailing_newline_line_counts_are_accurate(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "empty.md").write_text("", encoding="utf-8")
    (repo_root / "one-line.md").write_text("one line\n", encoding="utf-8")

    report, _ = generate_report(repo_root)

    assert "`empty.md` — .md (0 lines," in report
    assert "`one-line.md` — .md (1 line," in report


def test_invalid_utf8_file_is_reported_by_cli(tmp_path, monkeypatch, capsys):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "broken.md").write_bytes(b"\xff")
    output_path = tmp_path / "report.md"
    monkeypatch.setattr(
        "sys.argv",
        ["documentation_sync", "--repo", str(repo_root), "--output", str(output_path)],
    )

    assert main() == 1
    captured = capsys.readouterr()
    assert "Could not analyze repository" in captured.err
    assert str(repo_root / "broken.md") in captured.err
    assert not output_path.exists()


def test_output_write_error_is_reported_without_traceback(tmp_path, monkeypatch, capsys):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# Demo\n", encoding="utf-8")
    output_blocker = tmp_path / "not-a-directory"
    output_blocker.write_text("blocker", encoding="utf-8")
    output_path = output_blocker / "report.md"
    monkeypatch.setattr(
        "sys.argv",
        ["documentation_sync", "--repo", str(repo_root), "--output", str(output_path)],
    )

    assert main() == 1
    captured = capsys.readouterr()
    assert "Could not write report" in captured.err
    assert "Traceback" not in captured.err


def test_cli_refuses_to_overwrite_an_existing_repository_file(tmp_path, monkeypatch, capsys):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    readme = repo_root / "README.md"
    original = "# Keep this README\n"
    readme.write_text(original, encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        ["documentation_sync", "--repo", str(repo_root), "--output", str(readme)],
    )

    assert main() == 1
    captured = capsys.readouterr()
    assert "Refusing to overwrite existing repository file" in captured.err
    assert readme.read_text(encoding="utf-8") == original


def test_generate_report_rejects_a_file_as_repository(tmp_path):
    repo_file = tmp_path / "not-a-directory"
    repo_file.write_text("file", encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="not a directory"):
        generate_report(repo_file)


def test_cli_rejects_invalid_repository_path(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(
        "sys.argv",
        ["documentation_sync", "--repo", "\0", "--output", str(tmp_path / "report.md")],
    )

    assert main() == 1
    assert "Repository path does not exist or is not a directory" in capsys.readouterr().err


def test_docs_name_containing_tests_does_not_count_as_test_coverage(tmp_path):
    repo_root = tmp_path / "repo"
    docs = repo_root / "docs"
    docs.mkdir(parents=True)
    (docs / "testsetup.md").write_text("documentation only\n", encoding="utf-8")

    _, warnings = generate_report(repo_root)

    assert any("No tests directory detected" in warning for warning in warnings)
