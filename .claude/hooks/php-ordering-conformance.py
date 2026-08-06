#!/usr/bin/env python3
"""PHP ordering conformance hook for tiny-blocks PHP libraries.

Self-contained PostToolUse hook on Edit|Write|MultiEdit. Verifies the deterministic
ordering conventions for PHP declarations:

- Parameter ordering: declaration parameters (constructors, factories, methods,
  property promotion) in three tiers, required parameters first, then defaulted
  parameters, then a variadic, each tier by identifier length ascending,
  alphabetical tie-breaker, semantic pairs preserved. A PHPUnit test method fed by
  a data provider is exempt, its parameters are the columns of its data set.
- Member ordering: constants, enum cases, constructor, static methods, instance
  methods, in that group order, each group length-ascending with alphabetical
  tie-breaker. Enum cases are exempt from the intra-group order, which is author-chosen
  per rule 6 "evident structure" (a registry such as ISO 3166 keeps its canonical order).
  Their group position is still enforced. PHPUnit test classes instead order methods as
  lifecycle hooks (in execution order), then other methods, then data providers.

The analysis is pure (FileUnit in, Violation out) and runs in three passes over
well-formed PHP: a lexical pass blanks every comment, string, and heredoc/nowdoc
body (LITERALS), a structural pass maps every bracket to its pair (bracket_spans);
extraction assigns tokens of interest to their containers by flat walks. Control
flow uses guard clauses only and nesting never exceeds two levels. Reports
violations to stderr and exits 2 to prompt Claude, exits 0 silently if no violations
or the file is out of scope.
"""

import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from pathlib import Path
from typing import Final

# --- Configuration ----------------------------------------------------------

# In-scope files: PHP sources under src/ or tests/.
SCOPE_PATTERN: Final = re.compile(r"(^|/)(src|tests)/.+\.php$")

# Semantic groups. When two or more members of a group appear in the same parameter
# list, they keep their natural order, sorting as a unit at the lead member's key.
# Groups of arbitrary length are supported (calendar and clock components included).
SEMANTIC_GROUPS: Final = (
    ("start", "end"),
    ("from", "to"),
    ("startAt", "endAt"),
    ("createdAt", "updatedAt"),
    ("before", "after"),
    ("min", "max"),
    ("year", "month", "day"),
    ("hour", "minute", "second", "nanosecond"),
)

# Each member maps to (lead, position, members). The members present in the same list
# keep their natural intra-group order, sorting as a unit at the lead member's key.
GROUP_MEMBER: Final = {
    member: (group[0], position, group)
    for group in SEMANTIC_GROUPS
    for position, member in enumerate(group)
}

MODIFIERS: Final = ("abstract", "final", "private", "protected", "public", "static")

# The lexical grammar: every PHP construct that must not be scanned as code.
# Alternatives are ordered, the heredoc label closes via backreference.
LITERALS: Final = re.compile(
    r"""
      /\*.*?\*/                                  # block comment
    | //[^\n]*                                   # line comment
    | \#(?!\[)[^\n]*                             # hash comment, never a #[ attribute
    | <<<[ \t]*(?P<quote>['"]?)(?P<label>\w+)(?P=quote)[^\n]*\n
      .*?\n[ \t]*(?P=label)\b                    # heredoc and nowdoc body
    | '(?:\\.|[^'\\])*'                          # single-quoted string
    | "(?:\\.|[^"\\])*"                          # double-quoted string
    """,
    re.DOTALL | re.MULTILINE | re.VERBOSE,
)

TYPE_DECLARATION: Final = re.compile(
    r"^[ \t]*(?:(?:abstract|final|readonly)\s+)*(class|interface|trait|enum)\s+(\w+)",
    re.MULTILINE,
)
FUNCTION_DECLARATION: Final = re.compile(r"\bfunction\s+&?(\w+)\s*\(")
METHOD_LINE: Final = re.compile(
    rf"^\s*((?:(?:{'|'.join(MODIFIERS)})\s+)+)function\s+&?(\w+)\s*\("
)
CONST_LINE: Final = re.compile(
    r"^\s*(?:(?:final|private|protected|public)\s+)*const\s+(?:[?\w|&()\s]+\s)?(\w+)\s*="
)
CASE_LINE: Final = re.compile(r"^\s*case\s+(\w+)\s*[=;]")

PARAMETER: Final = re.compile(r"\$(\w+)")
VARIADIC: Final = re.compile(r"\.\.\.\s*\$")
# A default assignment is a lone `=`, never `=>` in an array or arrow function,
# never a comparison (`==`, `!=`, `<=`, `>=`).
DEFAULT_ASSIGNMENT: Final = re.compile(r"(?<![=!<>])=(?![=>])")

# PHPUnit lifecycle hooks in fixed execution order, with detection patterns for a
# test class and for the data providers its methods reference.
LIFECYCLE_ORDER: Final = ("setUpBeforeClass", "setUp", "tearDown", "tearDownAfterClass")
LIFECYCLE_HOOKS: Final = frozenset(LIFECYCLE_ORDER)
EXTENDS_TESTCASE: Final = re.compile(r"\bextends\s+\\?(?:\w+\\)*TestCase\b")
DATA_PROVIDER_REFERENCE: Final = re.compile(
    r"#\[\s*(?:\\?\w+\\)*DataProvider\s*\(\s*['\"](\w+)['\"]"
    r"|@dataProvider\s+(\w+)"
)

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
class Source:
    """PHP source with literals blanked out at their original positions."""

    clean: str

    @staticmethod
    def blanked(literal: re.Match[str]) -> str:
        """The matched literal as spaces, newlines preserved."""
        return re.sub(r"[^\n]", " ", literal.group(0))

    @classmethod
    def from_php(cls, text: str) -> "Source":
        """A source with every comment, string, and heredoc blanked out."""
        return cls(clean=LITERALS.sub(cls.blanked, text))

    def line_of(self, index: int) -> int:
        """The 1-based line number of a character index."""
        return self.clean.count("\n", 0, index) + 1


@dataclass(frozen=True)
class FileUnit:
    """One file under analysis: its raw text and the blanked Source on demand."""

    path: str
    text: str

    @cached_property
    def source(self) -> Source:
        """The PHP source with literals blanked, computed once per file."""
        return Source.from_php(self.text)


@dataclass(frozen=True)
class Ordering:
    """Sole owner of the parameter-ordering logic for one variant."""

    group_member: dict[str, tuple[str, int, tuple[str, ...]]]

    def sorted(self, names: list[str]) -> list[str]:
        """The names in the required order."""
        present = set(names)
        return sorted(names, key=lambda name: self.key(name, present))

    def key(self, name: str, present: set[str]) -> tuple[int, str, int]:
        """Length, then alphabet, with every member of a present group at the lead key."""
        entry = self.group_member.get(name)
        if entry is not None:
            lead, position, members = entry
            if any(other in present for other in members if other != name):
                return (len(lead), lead, position)
        return (len(name), name, 0)


PARAMETER_ORDERING: Final = Ordering(group_member=GROUP_MEMBER)
MEMBER_ORDERING: Final = Ordering(group_member={})


class MemberKind(Enum):
    """Closed set of class-member groups in required declaration order.

    Ranks 0 to 4 are the production families. A PHPUnit test class keeps the
    const, case, constructor ranks then draws its methods from the test families
    (5 to 7): lifecycle hooks, other methods, data providers. A class draws its
    methods from one family set or the other, never both, so ranks stay monotonic.
    """

    CONSTANT = (0, "const")
    CASE = (1, "case")
    CONSTRUCTOR = (2, "constructor")
    STATIC_METHOD = (3, "static method")
    INSTANCE_METHOD = (4, "instance method")
    LIFECYCLE = (5, "lifecycle hook")
    METHOD = (6, "method")
    DATA_PROVIDER = (7, "data provider")

    @property
    def rank(self) -> int:
        return self.value[0]

    @property
    def label(self) -> str:
        return self.value[1]

    def precedes(self, other: "MemberKind") -> bool:
        """Whether this group must appear before the other group."""
        return self.rank < other.rank


@dataclass(frozen=True)
class Member:
    """One classified class member at its declaration line."""

    kind: MemberKind
    line: int
    name: str


@dataclass(frozen=True)
class TypeMembers:
    """The members of one class-like declaration in source order."""

    name: str
    is_test: bool
    members: list[Member]


# Parameter ordering tiers: required first, then defaulted, then a variadic.
REQUIRED_TIER: Final = 0
DEFAULT_TIER: Final = 1
VARIADIC_TIER: Final = 2


@dataclass(frozen=True)
class Parameter:
    """One declared parameter: its identifier and its ordering tier."""

    name: str
    tier: int


@dataclass(frozen=True)
class ParameterList:
    """One declaration's parameters in source order."""

    line: int
    owner: str
    params: list[Parameter]

    @property
    def names(self) -> list[str]:
        return [parameter.name for parameter in self.params]

    def in_tier(self, tier: int) -> list[str]:
        return [parameter.name for parameter in self.params if parameter.tier == tier]

    def required(self) -> list[str]:
        ordered = PARAMETER_ORDERING.sorted(self.in_tier(REQUIRED_TIER))
        ordered += PARAMETER_ORDERING.sorted(self.in_tier(DEFAULT_TIER))
        return ordered + self.in_tier(VARIADIC_TIER)

    def out_of_order(self) -> bool:
        return len(self.params) >= 2 and self.names != self.required()


# --- Structure ----------------------------------------------------------------


def bracket_spans(text: str) -> dict[int, int]:
    """Every opening bracket position mapped to its closing position."""
    spans: dict[int, int] = {}
    stack: list[int] = []

    for position, character in enumerate(text):
        if character in "([{":
            stack.append(position)

        if character in ")]}" and stack:
            spans[stack.pop()] = position

    return spans


def top_level_pieces(text: str) -> list[str]:
    """The comma-separated pieces of a list, ignoring nested separators."""
    pieces, depth, current = [], 0, []
    for character in text:
        if character in "([{":
            depth += 1

        if character in ")]}":
            depth -= 1

        if character == "," and depth == 0:
            pieces.append("".join(current))
            current = []
            continue
        current.append(character)

    tail = "".join(current).strip()

    if tail:
        pieces.append(tail)

    return pieces


# --- Extraction ---------------------------------------------------------------


def declared_signatures(source: Source) -> list[ParameterList]:
    """Every function or method declaration with its parameters."""
    signatures = []
    spans = bracket_spans(source.clean)

    for match in FUNCTION_DECLARATION.finditer(source.clean):
        open_paren = source.clean.index("(", match.end() - 1)
        inner = source.clean[open_paren + 1: spans.get(open_paren, len(source.clean))]
        params = [
            parameter_of(piece)
            for piece in top_level_pieces(inner)
            if PARAMETER.search(piece)
        ]

        signatures.append(ParameterList(
            line=source.line_of(match.start()),
            owner=match.group(1),
            params=params,
        ))
    return signatures


def parameter_of(piece: str) -> Parameter:
    """One parameter's identifier and ordering tier from its declaration piece."""
    name = PARAMETER.findall(piece)[-1]

    if VARIADIC.search(piece):
        return Parameter(name=name, tier=VARIADIC_TIER)

    if DEFAULT_ASSIGNMENT.search(piece):
        return Parameter(name=name, tier=DEFAULT_TIER)
    return Parameter(name=name, tier=REQUIRED_TIER)


def class_members(unit: FileUnit) -> list[TypeMembers]:
    """Every class-like declaration with its members in source order."""
    declarations = []
    clean = unit.source.clean
    spans = bracket_spans(clean)

    for type_match in TYPE_DECLARATION.finditer(clean):
        body_open = clean.find("{", type_match.end())

        if body_open == -1:
            continue

        body_close = spans.get(body_open, len(clean))
        is_test = bool(EXTENDS_TESTCASE.search(clean[type_match.end(): body_open]))
        providers = test_providers(unit.text[body_open + 1: body_close]) if is_test else set()
        declarations.append(TypeMembers(
            name=type_match.group(2),
            is_test=is_test,
            members=declared_members(
                at_line=unit.source.line_of(body_open),
                body=clean[body_open + 1: body_close],
                is_test=is_test,
                providers=providers,
            ),
        ))
    return declarations


def test_providers(raw_body: str) -> set[str]:
    """Every method name a data-provider attribute or annotation references."""
    names = set()
    for match in DATA_PROVIDER_REFERENCE.finditer(raw_body):
        names.add(match.group(1) or match.group(2))
    return names


def provider_consumer_lines(unit: FileUnit) -> set[int]:
    """Declaration lines of the test methods a data provider feeds.

    The consumer side of the data-provider relation: the method a
    `#[DataProvider('name')]` attribute or `@dataProvider name` tag immediately
    precedes. Its parameters are the columns of the data set, ordered by the data
    rather than by name length, so the parameter check skips these lines. Detection
    runs on the raw text, since the docblock form is blanked in the Source, then the
    next declaration in the position-aligned Source fixes the line.
    """
    clean = unit.source.clean
    lines = set()
    for reference in DATA_PROVIDER_REFERENCE.finditer(unit.text):
        method = FUNCTION_DECLARATION.search(clean, reference.end())
        if not method:
            continue
        lines.add(unit.source.line_of(method.start()))
    return lines


def declared_members(at_line: int, body: str, is_test: bool, providers: set[str]) -> list[Member]:
    """The members declared at the top level of one type body."""
    members, depth = [], 0
    for offset, line in enumerate(body.split("\n")):
        member = classified(at=at_line + offset, line=line, is_test=is_test, providers=providers)
        if depth == 0 and member:
            members.append(member)
        depth += line.count("{") - line.count("}")
    return members


def classified(at: int, line: str, is_test: bool, providers: set[str]) -> Member | None:
    """The member a line declares, when it declares one."""
    method = METHOD_LINE.match(line)
    if method:
        name = method.group(2)
        if name == "__construct":
            return Member(kind=MemberKind.CONSTRUCTOR, line=at, name=name)

        if is_test:
            return Member(kind=test_method_kind(name=name, providers=providers), line=at, name=name)

        if "static" in method.group(1).split():
            return Member(kind=MemberKind.STATIC_METHOD, line=at, name=name)
        return Member(kind=MemberKind.INSTANCE_METHOD, line=at, name=name)

    constant = CONST_LINE.match(line)

    if constant:
        return Member(kind=MemberKind.CONSTANT, line=at, name=constant.group(1))
    case = CASE_LINE.match(line)

    if case:
        return Member(kind=MemberKind.CASE, line=at, name=case.group(1))
    return None


def test_method_kind(name: str, providers: set[str]) -> MemberKind:
    """The method family a name takes inside a PHPUnit test class."""
    if name in LIFECYCLE_HOOKS:
        return MemberKind.LIFECYCLE

    if name in providers:
        return MemberKind.DATA_PROVIDER
    return MemberKind.METHOD


# --- Checks -------------------------------------------------------------------


def parameter_violations(unit: FileUnit) -> tuple[Violation, ...]:
    """Parameter ordering on every declaration a data provider does not feed."""
    exempt = provider_consumer_lines(unit)
    return tuple(
        Violation(
            line=signature.line,
            path=unit.path,
            message=(
                f"parameter order in `{signature.owner}()` is "
                f"({', '.join(signature.names)}), "
                f"required ({', '.join(signature.required())})"
            ),
        )

        for signature in declared_signatures(unit.source)
        if signature.line not in exempt and signature.out_of_order()
    )


def member_violations(unit: FileUnit) -> tuple[Violation, ...]:
    """Member ordering on group sequence and order within each group."""
    violations: list[Violation] = []
    for declared in class_members(unit):
        violations.extend(group_sequence_violations(path=unit.path, declared=declared))
        violations.extend(within_group_violations(path=unit.path, declared=declared))
    return tuple(violations)


def group_sequence_violations(path: str, declared: TypeMembers) -> tuple[Violation, ...]:
    """Members declared after a group that must come later."""
    violations = []
    order = group_order_text(declared.is_test)
    latest = MemberKind.CONSTANT
    for member in declared.members:
        if member.kind.precedes(latest):
            violations.append(Violation(
                line=member.line,
                path=path,
                message=(
                    f"`{member.name}` ({member.kind.label}) declared after a later "
                    f"group in `{declared.name}`, required group order {order}"
                ),
            ))

        if latest.precedes(member.kind):
            latest = member.kind
    return tuple(violations)


def group_order_text(is_test: bool) -> str:
    """The required group-order clause for the production or the test layout."""
    if is_test:
        return "const, case, constructor, lifecycle hooks, methods, data providers"
    return "const, case, constructor, static methods, instance methods"


def within_group_violations(path: str, declared: TypeMembers) -> tuple[Violation, ...]:
    """Groups whose members break their required intra-group order.

    Enum cases are exempt: their order is author-chosen (rule 6 "evident structure"), so a
    domain registry such as ISO 3166 may keep its canonical order. Constant and method order
    stays enforced, as does the const, case, method group sequence.
    """
    violations = []
    for kind in MemberKind:
        if kind in (MemberKind.CONSTRUCTOR, MemberKind.CASE):
            continue
        grouped = [member for member in declared.members if member.kind is kind]
        names = [member.name for member in grouped]

        if not names:
            continue
        required = required_within(kind=kind, names=names)

        if names == required:
            continue

        violations.append(Violation(
            line=grouped[0].line,
            path=path,
            message=(
                f"{kind.label} order in `{declared.name}` is ({', '.join(names)}), "
                f"required ({', '.join(required)})"
            ),
        ))
    return tuple(violations)


def required_within(kind: MemberKind, names: list[str]) -> list[str]:
    """One group's required order, lifecycle hooks by execution order, else length then alphabet."""
    if kind is MemberKind.LIFECYCLE:
        return [hook for hook in LIFECYCLE_ORDER if hook in names]
    return MEMBER_ORDERING.sorted(names)


def ordering_violations(unit: FileUnit) -> tuple[Violation, ...]:
    """Every ordering violation in one PHP file: members, parameters."""
    return (
        *member_violations(unit),
        *parameter_violations(unit),
    )


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
    """Whether the path is a PHP source under src/ or tests/."""
    return bool(SCOPE_PATTERN.search(path.as_posix())) and path.is_file()


def file_violations(path: Path) -> tuple[Violation, ...]:
    """The ordering violations for one file."""
    unit = FileUnit(
        path=path.as_posix(),
        text=path.read_text(errors="replace", encoding="utf-8"),
    )
    return ordering_violations(unit)


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
