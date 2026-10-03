"""Hyperorder research: paired continuations, divergence-family convergence and ordinality.

The executable mechanisms are proposed [FRAME] translations of the sourced dichrome
and of Tyler's operational convergence direction; native □-formation remains [OPEN].
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from dichrome import (ClosureReport, Continuation, DichromeFrame, DivergenceFamily,
                      Evidence, FamilyConvergenceReport, FiltrationReport, FrameInspection,
                      Obstruction, PathWitness, Position, ReproductionObstruction, closure,
                      compose_paths, converge_families, describe, example_frame, filtration,
                      follow_path, inspect_frame, read_description, to_json, verify_description)

HYPERGRAMMAR = "hypergrammar d4df988be65636bf66d6d3f8ef5a85edf524d8dc"
MAX_ELEMENTS = 64
MAX_DECLARATIONS = 256


@dataclass(frozen=True)
class Sense:
    name: str
    gloss: str
    source: str


SENSES = (
    Sense("dichrome-closure",
          "the dichrome closes geometry and philosophy into a single form, the geometric "
          "philosophy and philosophical geometry of itself, in which the two are no longer "
          "separable",
          f"{HYPERGRAMMAR} docs/prerequisites/21_hypertopologies.md lines 5 and 179"),
)

# Exact terms only. There is no alias table: "order" is not "hyperorder".
_TERMS = {"hyperorder": "dichrome-closure"}


def resolve_sense(term: str) -> Sense:
    """The declared sense of a term; KeyError for anything not declared verbatim."""
    name = _TERMS[term]
    return next(s for s in SENSES if s.name == name)


@dataclass(frozen=True)
class Statement:
    said: str
    source: str
    relates: tuple[str, ...]
    status: str


REALIGNMENT = Statement(
    said=("Chaos realigns into order, this has to do with atemporality, also hyperorder "
          "and hyperchaos theories might need grounding from hyperethics, Im not sure"),
    source="Tyler Roost, 2026-09-30, USER-STATED in a working session",
    relates=("chaos", "order", "atemporality", "hyperorder", "hyperchaos", "hyperethics"),
    status="OPEN",
)


class Verdict(Enum):
    PRECEDES = "PRECEDES"
    FOLLOWS = "FOLLOWS"
    INCOMPARABLE = "INCOMPARABLE"
    UNKNOWN = "UNKNOWN"
    CONFLICTED = "CONFLICTED"


@dataclass(frozen=True)
class Precedes:
    """Declares that position ``a`` precedes position ``b``; no clock or number is implied."""

    a: str
    b: str


@dataclass(frozen=True)
class Incomparable:
    """Declares that neither of two positions precedes the other."""

    a: str
    b: str


def _is_name(x: object) -> bool:
    return isinstance(x, str) and bool(x)


@dataclass(frozen=True)
class Order:
    """Named positions and declared relations. ``total`` is a claim, checked when made."""

    elements: tuple[str, ...]
    precedes: tuple[Precedes, ...] = ()
    incomparable: tuple[Incomparable, ...] = ()
    total: bool = False

    def __post_init__(self) -> None:
        if (not isinstance(self.elements, tuple) or not 1 <= len(self.elements) <= MAX_ELEMENTS
                or not isinstance(self.precedes, tuple) or not isinstance(self.incomparable, tuple)
                or len(self.precedes) + len(self.incomparable) > MAX_DECLARATIONS
                or not isinstance(self.total, bool)):
            raise ValueError(f"finite order requires 1-{MAX_ELEMENTS} positions and at most "
                             f"{MAX_DECLARATIONS} declarations")
        if not all(_is_name(e) for e in self.elements):
            raise ValueError("positions are non-empty names, never numbers")
        if len(set(self.elements)) != len(self.elements):
            raise ValueError("duplicate position")
        known = set(self.elements)
        for kind, items in ((Precedes, self.precedes), (Incomparable, self.incomparable)):
            for item in items:
                if not isinstance(item, kind) or not (_is_name(item.a) and _is_name(item.b)):
                    raise ValueError(f"invalid {kind.__name__} declaration")
                if item.a not in known or item.b not in known:
                    raise ValueError(f"{kind.__name__} names an undeclared position")
                if item.a == item.b:
                    raise ValueError(f"{kind.__name__} relates a position to itself")
        if self.total:
            if self.incomparable:
                raise ValueError("a total order declares no incomparable pair")
            reach = _reach(self)
            for x in self.elements:
                for y in self.elements:
                    if x != y and y not in reach[x] and x not in reach[y]:
                        raise ValueError(f"declared total, but {x!r} and {y!r} are unrelated")


def _reach(order: Order) -> dict[str, set[str]]:
    succ: dict[str, set[str]] = {e: set() for e in order.elements}
    for p in order.precedes:
        succ[p.a].add(p.b)
    reach: dict[str, set[str]] = {}
    for start in order.elements:
        seen: set[str] = set()
        stack = list(succ[start])
        while stack:
            n = stack.pop()
            if n not in seen:
                seen.add(n)
                stack.extend(succ[n])
        reach[start] = seen
    return reach


def compare(order: Order, x: str, y: str) -> Verdict:
    """One of five verdicts. A relation nobody declared is UNKNOWN, never INCOMPARABLE."""
    if x not in order.elements or y not in order.elements:
        raise KeyError("compare names an undeclared position")
    if x == y:
        raise ValueError("a position is not compared with itself")
    reach = _reach(order)
    up, down = y in reach[x], x in reach[y]
    declared_apart = any({i.a, i.b} == {x, y} for i in order.incomparable)
    if (up and down) or (declared_apart and (up or down)):
        return Verdict.CONFLICTED
    if up:
        return Verdict.PRECEDES
    if down:
        return Verdict.FOLLOWS
    if declared_apart:
        return Verdict.INCOMPARABLE
    return Verdict.UNKNOWN


def main(argv: list[str] | None = None) -> int:
    """Inspectable command-line operations with explicit failure outcomes."""
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Hyperorder paired continuation research [FRAME]")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="run distinct divergence families and an obstruction")
    demo.add_argument("--escape", action="store_true", help="add a non-converging declared branch")
    demo.add_argument("--incomplete", action="store_true", help="retain UNKNOWN for undeclared continuations")
    for name in ("inspect", "describe", "compare", "trace", "converge", "verify-description"):
        command = commands.add_parser(name)
        command.add_argument("frame", type=Path)
        if name == "compare":
            command.add_argument("left")
            command.add_argument("right")
        elif name == "trace":
            command.add_argument("origin")
            command.add_argument("route", nargs="*")
        elif name == "converge":
            command.add_argument("families", type=Path)
            command.add_argument("representative")
        elif name == "verify-description":
            command.add_argument("description", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            frame, families = example_frame(escape=args.escape, incomplete=args.incomplete)
            report = converge_families(frame, families, "paired-form")
            output = {"classification": "FRAME", "inspection": inspect_frame(frame),
                      "family_convergence": report,
                      "path_sensitive_comparison": filtration(frame, "geometry-route", "meaning-route"),
                      "self_read_return": closure(frame, "paired-form", ("self-read", "self-return")),
                      "description_recovery": verify_description(frame, describe(frame)),
                      "native_adequacy": "OPEN"}
            print(to_json(output), end="")
            return 0 if report.status is Evidence.PASS else 1
        # The retained schema is deliberately small; oversized files are refused before parsing.
        def read_record(path: Path) -> dict:
            if path.stat().st_size > 2_000_000:
                raise ValueError("record exceeds the finite input limit")
            def no_duplicates(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError("duplicate JSON object field")
                    result[key] = value
                return result
            return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)
        frame = read_description(read_record(args.frame))
        if args.command == "inspect":
            result = inspect_frame(frame)
            succeeded = result.accepted
        elif args.command == "describe":
            result, succeeded = describe(frame), True
        elif args.command == "compare":
            result = filtration(frame, args.left, args.right)
            succeeded = result.simulation is Evidence.PASS
        elif args.command == "trace":
            result, succeeded = follow_path(frame, args.origin, tuple(args.route)), True
        elif args.command == "converge":
            record = read_record(args.families)
            if type(record) is not dict or set(record) != {"families"} or type(record["families"]) is not list:
                raise ValueError("families record must contain only a families array")
            families = []
            for family in record["families"]:
                if type(family) is not dict or set(family) != {"name", "members"} or type(family["members"]) is not list:
                    raise ValueError("each family has a name and distinct named members")
                if (not all(isinstance(m, str) for m in family["members"])
                        or len(set(family["members"])) != len(family["members"])):
                    raise ValueError("family members are distinct names")
                families.append(DivergenceFamily(family["name"], frozenset(family["members"])))
            result = converge_families(frame, tuple(families), args.representative)
            succeeded = result.status is Evidence.PASS
        else:
            result = verify_description(frame, read_record(args.description))
            succeeded = result is Evidence.PASS
        print(to_json(result), end="")
        return 0 if succeeded else 1
    except (ValueError, KeyError, TypeError, OSError, RecursionError, json.JSONDecodeError) as error:
        print(to_json({"classification": "FRAME", "status": "FAIL", "error": str(error)}), end="")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
