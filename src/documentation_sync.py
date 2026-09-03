from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", "dist", "build"}
FILE_TYPES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"}


@dataclass
class FileSummary:
    path: str
    extension: str
    size_bytes: int
    line_count: int


def is_project_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if any(part in SKIP_DIRS for part in path.parts):
        return False
    return path.suffix.lower() in FILE_TYPES or path.name.lower() == "readme.md"


def summarize_repository(repo_root: Path) -> list[FileSummary]:
    summaries: list[FileSummary] = []
    for file_path in sorted(repo_root.rglob("*")):
        if not is_project_file(file_path):
            continue
        relative_path = file_path.relative_to(repo_root).as_posix()
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        summaries.append(
            FileSummary(
                path=relative_path,
                extension=file_path.suffix.lower() or "(none)",
                size_bytes=file_path.stat().st_size,
                line_count=max(content.count("\n") + 1, 0),
            )
        )
    return summaries


def detect_documentation_gaps(repo_root: Path, file_summaries: list[FileSummary]) -> list[str]:
    messages: list[str] = []
    has_readme = any(summary.path.lower() == "readme.md" for summary in file_summaries)
    has_docs_dir = (repo_root / "docs").is_dir()
    has_tests = any("tests" in summary.path.lower() for summary in file_summaries)

    if not has_readme:
        messages.append("No root README.md found; add a project overview for onboarding.")
    if not has_docs_dir:
        messages.append("No docs/ directory found; consider adding a structured documentation location.")
    if not has_tests:
        messages.append("No tests directory detected; add validation scenarios for the main repo workflow.")
    return messages


def render_report(repo_root: Path, summaries: list[FileSummary], warnings: list[str]) -> str:
    by_extension: dict[str, int] = {}
    total_lines = 0
    total_bytes = 0
    for summary in summaries:
        by_extension[summary.extension] = by_extension.get(summary.extension, 0) + 1
        total_lines += summary.line_count
        total_bytes += summary.size_bytes

    lines = [
        "# Documentation Sync Report",
        "",
        f"- Repository: `{repo_root.name}`",
        f"- Generated: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}`",
        f"- Files analyzed: `{len(summaries)}`",
        f"- Total lines: `{total_lines}`",
        f"- Total bytes: `{total_bytes}`",
        "",
        "## Overview",
        "",
        "This report is a lightweight snapshot of the repository to support documentation review and release readiness checks.",
        "",
        "## File inventory",
        "",
    ]

    if summaries:
        for summary in summaries:
            lines.append(f"- `{summary.path}` — {summary.extension} ({summary.line_count} lines, {summary.size_bytes} bytes)")
    else:
        lines.append("No project files were found in the target repository.")

    lines.extend(["", "## File-type summary", ""])
    if by_extension:
        for extension, count in sorted(by_extension.items()):
            lines.append(f"- `{extension}`: {count}")
    else:
        lines.append("No file-type summaries were available.")

    lines.extend(["", "## Documentation gaps", ""])
    if warnings:
        for warning in warnings:
            lines.append(f"- Warning: {warning}")
    else:
        lines.append("No documentation gaps detected.")

    lines.extend([
        "",
        "## Recommended next steps",
        "",
        "- Review the file inventory for stale or accidental documentation assets.",
        "- Add a root README or docs directory if the repository lacks an entry point.",
        "- Keep this output in CI or pull requests to reduce documentation drift.",
    ])
    return "\n".join(lines) + "\n"


def generate_report(repo_root: Path) -> tuple[str, list[str]]:
    if not repo_root.exists() or not repo_root.is_dir():
        raise FileNotFoundError(f"Repository path does not exist or is not a directory: {repo_root}")
    summaries = summarize_repository(repo_root)
    warnings = detect_documentation_gaps(repo_root, summaries)
    report = render_report(repo_root, summaries, warnings)
    return report, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Markdown documentation sync report for a repository.")
    parser.add_argument("--repo", type=Path, required=True, help="Path to the repository to analyze.")
    parser.add_argument("--output", type=Path, required=True, help="Destination Markdown report path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report, warnings = generate_report(args.repo)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Documentation sync report generated at {args.output}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
