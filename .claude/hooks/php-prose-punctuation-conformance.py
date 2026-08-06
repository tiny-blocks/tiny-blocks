#!/usr/bin/env python3
"""Prose punctuation conformance hook for tiny-blocks PHP libraries.

Self-contained PostToolUse hook on Edit|Write|MultiEdit. Verifies prose punctuation:
no em-dash, en-dash, or ` -- ` as a clause separator in Markdown prose or
PHP comments, plus no `;` separator in Markdown. The checks read raw text only, so
this script carries no PHP lexer. Markdown files route to the prose check, PHP
sources to the comment check.

Control flow uses guard clauses only and nesting never exceeds two levels. Reports
violations to stderr and exits 2 to prompt Claude with feedback; exits 0 silently if
no violations or the file is out of scope.
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

# --- Configuration ----------------------------------------------------------

# In-scope files: PHP sources under src/ or tests/, plus any Markdown file.
SCOPE_PATTERN: Final = re.compile(r"(^|/)(src|tests)/.+\.php$")
MARKDOWN_PATTERN: Final = re.compile(r"\.md$")

# Prohibited prose punctuation as clause separators. Em-dash U+2014, en-dash U+2013,
# spaced double hyphen, and (Markdown only) the semicolon.
PROSE_PUNCTUATION: Final = re.compile(r"[\u2014\u2013]| -- |;")
PROSE_DASHES: Final = re.compile(r"[\u2014\u2013]| -- ")
FENCE: Final = re.compile(r"^\s*```")
PHP_COMMENT: Final = re.compile(r"/\*.*?\*/|//[^\n]*|#(?!\[)[^\n]*", re.DOTALL)
INLINE_CODE: Final = re.compile(r"`[^`]*`")

# String and heredoc bodies, blanked before the PHP comment scan so a `//` or ` -- `
# inside a string literal is never mistaken for a comment.
STRING_LITERAL: Final = re.compile(
    r"""
      <<<[ \t]*(?P<quote>['"]?)(?P<label>\w+)(?P=quote)[^\n]*\n
      .*?\n[ \t]*(?P=label)\b
    | '(?:\\.|[^'\\])*'
    | "(?:\\.|[^"\\])*"
    """,
    re.DOTALL | re.VERBOSE,
)

# HTML entities (&amp;, &#39;) and URLs carry legitimate semicolons, so they are
# stripped from a Markdown line before the prose-punctuation scan.
HTML_ENTITY: Final = re.compile(r"&(?:\w+|#\d+);")
URL: Final = re.compile(r"https?://\S+")
# A line indented by four or more spaces is a Markdown indented code block.
INDENTED_CODE: Final = re.compile(r"^ {4,}\S")

MAX_ERRORS_REPORTED = 30


# --- Types --------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    """One style violation at a source position."""

    line: int
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


@dataclass(frozen=True)
class FileUnit:
    """One file under analysis: its path and raw text. No lexing needed here."""

    path: str
    text: str


# --- Checks -------------------------------------------------------------------


def blanked(literal: re.Match[str]) -> str:
    """The matched literal as spaces, newlines preserved."""
    return re.sub(r"[^\n]", " ", literal.group(0))


def is_markdown(path: str) -> bool:
    """Whether the path is a Markdown file, routed to the Markdown prose check."""
    return bool(MARKDOWN_PATTERN.search(path))


def markdown_violations(unit: FileUnit) -> tuple[Violation, ...]:
    """No `;`, em-dash, en-dash, or ` -- ` as a clause
    separator in Markdown prose. Fenced code and table rows are exempt."""
    violations = []
    in_fence = False
    for number, line in enumerate(unit.text.split("\n"), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue

        if in_fence or "|" in line or INDENTED_CODE.match(line):
            continue

        prose = URL.sub("", HTML_ENTITY.sub("", INLINE_CODE.sub("", line)))

        if PROSE_PUNCTUATION.search(prose):
            violations.append(Violation(
                line=number,
                path=unit.path,
                message=(
                    "prohibited prose punctuation (`;`, em-dash, en-dash, or ` -- `), "
                    "split the sentence or use a comma, colon, or parentheses"
                ),
            ))
    return tuple(violations)


def comment_violations(unit: FileUnit) -> tuple[Violation, ...]:
    """In PHPDoc and comments: no em-dash, en-dash,
    or ` -- ` as a separator. The `;` is not checked in PHP comments (it terminates
    statements in commented code)."""
    violations = []
    source = STRING_LITERAL.sub(blanked, unit.text)
    for match in PHP_COMMENT.finditer(source):
        if PROSE_DASHES.search(INLINE_CODE.sub("", match.group(0))):
            violations.append(Violation(
                line=source.count("\n", 0, match.start()) + 1,
                path=unit.path,
                message=(
                    "prohibited prose punctuation (em-dash, en-dash, or ` -- `) in a "
                    "comment"
                ),
            ))
    return tuple(violations)


def punctuation_violations(unit: FileUnit) -> tuple[Violation, ...]:
    """Punctuation violations for one file: Markdown prose for `.md`, comments otherwise."""
    if is_markdown(unit.path):
        return markdown_violations(unit)
    return comment_violations(unit)


# --- Shell --------------------------------------------------------------------


def requested_paths() -> list[Path]:
    """The paths to verify, from argv or from the hook's stdin payload."""
    if len(sys.argv) > 1:
        return [Path(argument) for argument in sys.argv[1:]]
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return []

    file_path = (payload.get("tool_input") or {}).get("file_path")

    if isinstance(file_path, str):
        return [Path(file_path)]
    return []


def in_scope(path: Path) -> bool:
    """Whether the path is a PHP source or any Markdown this hook covers."""
    posix = path.as_posix()
    matched = SCOPE_PATTERN.search(posix) or MARKDOWN_PATTERN.search(posix)
    return bool(matched) and path.is_file()


def file_violations(path: Path) -> tuple[Violation, ...]:
    """The punctuation violations for one file."""
    unit = FileUnit(
        path=path.as_posix(),
        text=path.read_text(errors="replace", encoding="utf-8"),
    )
    return punctuation_violations(unit)


def main() -> int:
    violations = [
        violation
        for path in requested_paths()
        if in_scope(path)
        for violation in file_violations(path)
    ]

    if not violations:
        return 0

    for violation in violations[:MAX_ERRORS_REPORTED]:
        print(violation, file=sys.stderr)
    overflow = len(violations) - MAX_ERRORS_REPORTED

    if overflow > 0:
        print(f"... and {overflow} more violations", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
