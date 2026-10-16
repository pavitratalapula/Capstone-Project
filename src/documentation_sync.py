from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", "dist", "build"}
FILE_TYPES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"}


@dataclass
class FileSummary:
    path: str
    extension: str
    size_bytes: int
    line_count: int


def is_project_file(path: Path, repo_root: Path) -> bool:
    if not path.is_file():
        return False
    relative_parts = path.relative_to(repo_root).parts
    if any(
        part in SKIP_DIRS or part.startswith(".")
        for part in relative_parts[:-1]
    ):
        return False
    return path.suffix.lower() in FILE_TYPES or path.name.lower() == "readme.md"


def summarize_repository(
    repo_root: Path, output_path: Path | None = None
) -> list[FileSummary]:
    summaries: list[FileSummary] = []
    excluded_path = output_path.resolve() if output_path is not None else None
    def raise_scan_error(error: OSError) -> None:
        raise error

    for current_directory, directory_names, file_names in os.walk(
        repo_root, onerror=raise_scan_error
    ):
        directory_names[:] = sorted(
            name
            for name in directory_names
            if name not in SKIP_DIRS and not name.startswith(".")
        )
        current_path = Path(current_directory)
        for file_name in sorted(file_names):
            file_path = current_path / file_name
            if not is_project_file(file_path, repo_root):
                continue
            if excluded_path is not None and file_path.resolve() == excluded_path:
                continue
            relative_path = file_path.relative_to(repo_root).as_posix()
            try:
                content = file_path.read_text(encoding="utf-8")
                size_bytes = file_path.stat().st_size
            except (OSError, UnicodeError, ValueError) as exc:
                raise OSError(f"Could not read project file {file_path}: {exc}") from exc
            summaries.append(
                FileSummary(
                    path=relative_path,
                    extension=file_path.suffix.lower() or "(none)",
                    size_bytes=size_bytes,
                    line_count=len(content.splitlines()),
                )
            )
    return sorted(summaries, key=lambda summary: summary.path)


def detect_documentation_gaps(repo_root: Path, file_summaries: list[FileSummary]) -> list[str]:
    messages: list[str] = []
    has_readme = any(summary.path.lower() == "readme.md" for summary in file_summaries)
    has_docs_dir = (repo_root / "docs").is_dir()
    has_tests = any(
        any(part.lower() in {"test", "tests"} for part in Path(summary.path).parts[:-1])
        or Path(summary.path).name.lower().startswith("test_")
        or Path(summary.path).name.lower().endswith("_test.py")
        for summary in file_summaries
    )

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
            line_label = "line" if summary.line_count == 1 else "lines"
            lines.append(
                f"- `{summary.path}` — {summary.extension} "
                f"({summary.line_count} {line_label}, {summary.size_bytes} bytes)"
            )
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


def generate_report(
    repo_root: Path, output_path: Path | None = None
) -> tuple[str, list[str]]:
    if not repo_root.exists() or not repo_root.is_dir():
        raise FileNotFoundError(f"Repository path does not exist or is not a directory: {repo_root}")
    summaries = summarize_repository(repo_root, output_path)
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
        report, warnings = generate_report(args.repo, args.output)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: Could not analyze repository {args.repo}: {exc}", file=sys.stderr)
        return 1

    try:
        output_is_inside_repository = args.output.resolve().is_relative_to(
            args.repo.resolve()
        )
        if args.output.exists() and output_is_inside_repository:
            with args.output.open("r", encoding="utf-8") as output_stream:
                first_line = output_stream.readline().rstrip("\r\n")
            if first_line != "# Documentation Sync Report":
                raise FileExistsError(
                    f"Refusing to overwrite existing repository file {args.output}; "
                    "choose a separate report path."
                )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: Could not write report to {args.output}: {exc}", file=sys.stderr)
        return 1
    print(f"Documentation sync report generated at {args.output}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
