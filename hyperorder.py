"""Finite Hyperorder frame: its sense kept apart from plain order, and order kept ordinal.

This module does not implement hyperorder. It records the one declared sense with its
source, keeps Tyler's 2026-09-30 realignment statement open, and checks the bookkeeping
any finite claim about order must pass: named positions, declared relations, and a
missing relation read as UNKNOWN.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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
