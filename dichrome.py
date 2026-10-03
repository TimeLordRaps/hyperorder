"""[FRAME] Paired structural/semantic continuation; not native □ formation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
import json
from typing import Any


MAX_POSITIONS = 64
MAX_CONTINUATIONS = 256
MAX_ATOMS = 64
MAX_PATH = 256


def _name(value: object) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 256


def _atoms(value: object) -> bool:
    return (isinstance(value, frozenset) and len(value) <= MAX_ATOMS
            and all(_name(atom) for atom in value))


@dataclass(frozen=True)
class Position:
    name: str
    geometry: frozenset[str]
    commitments: frozenset[str]
    outcome: str | None = None

    def __post_init__(self) -> None:
        if (not _name(self.name) or not _atoms(self.geometry) or not self.geometry
                or not _atoms(self.commitments) or not self.commitments
                or (self.outcome is not None and not _name(self.outcome))):
            raise ValueError("a position requires a name, both non-empty colorings and an optional outcome")


@dataclass(frozen=True)
class Continuation:
    name: str
    source: str
    target: str
    operation: str
    rationale: str
    add_geometry: frozenset[str] = frozenset()
    remove_geometry: frozenset[str] = frozenset()
    add_commitments: frozenset[str] = frozenset()
    remove_commitments: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not all(_name(x) for x in (self.name, self.source, self.target,
                                      self.operation, self.rationale)):
            raise ValueError("continuations require named ends, an operation and its rationale")
        deltas = (self.add_geometry, self.remove_geometry,
                  self.add_commitments, self.remove_commitments)
        if not all(_atoms(delta) for delta in deltas):
            raise ValueError("continuation changes are finite frozen sets of names")
        if self.add_geometry & self.remove_geometry or self.add_commitments & self.remove_commitments:
            raise ValueError("a continuation cannot add and remove the same atom")

    @property
    def label(self) -> tuple[str, str]:
        return self.operation, self.rationale


@dataclass(frozen=True)
class DichromeFrame:
    positions: tuple[Position, ...]
    continuations: tuple[Continuation, ...] = ()
    geometry_invariants: frozenset[str] = frozenset()
    meaning_invariants: frozenset[str] = frozenset()
    exhaustive: bool = True

    def __post_init__(self) -> None:
        if (not isinstance(self.positions, tuple) or not 1 <= len(self.positions) <= MAX_POSITIONS
                or not all(isinstance(p, Position) for p in self.positions)
                or not isinstance(self.continuations, tuple)
                or len(self.continuations) > MAX_CONTINUATIONS
                or not all(isinstance(c, Continuation) for c in self.continuations)
                or not _atoms(self.geometry_invariants) or not _atoms(self.meaning_invariants)
                or type(self.exhaustive) is not bool):
            raise ValueError("a dichrome frame is bounded, typed and immutable")
        names = [p.name for p in self.positions]
        if len(set(names)) != len(names):
            raise ValueError("duplicate position")
        move_names = [c.name for c in self.continuations]
        if len(set(move_names)) != len(move_names):
            raise ValueError("duplicate continuation")
        if any(c.source not in names or c.target not in names for c in self.continuations):
            raise ValueError("continuation names an undeclared position")


@dataclass(frozen=True)
class Obstruction:
    at: str
    code: str
    detail: str


@dataclass(frozen=True)
class FrameInspection:
    accepted: bool
    obstructions: tuple[Obstruction, ...]


def inspect_frame(frame: DichromeFrame) -> FrameInspection:
    """Check both transforms exactly; neither color can certify the other."""
    positions = {p.name: p for p in frame.positions}
    problems: list[Obstruction] = []
    for p in frame.positions:
        if not frame.geometry_invariants <= p.geometry:
            problems.append(Obstruction(p.name, "GEOMETRY_INVARIANT", "a declared geometric invariant is absent"))
        if not frame.meaning_invariants <= p.commitments:
            problems.append(Obstruction(p.name, "MEANING_INVARIANT", "a declared meaning invariant is absent"))
    for c in frame.continuations:
        a, b = positions[c.source], positions[c.target]
        for color, before, after, added, removed in (
            ("GEOMETRY", a.geometry, b.geometry, c.add_geometry, c.remove_geometry),
            ("MEANING", a.commitments, b.commitments, c.add_commitments, c.remove_commitments),
        ):
            if not removed <= before:
                problems.append(Obstruction(c.name, color + "_PREMISE", "removal requires an absent source atom"))
            if added & before:
                problems.append(Obstruction(c.name, color + "_FRESHNESS", "addition is already present at the source"))
            if (before - removed) | added != after:
                problems.append(Obstruction(c.name, color + "_TRANSPORT", "declared change does not reproduce target coloring"))
    return FrameInspection(not problems, tuple(problems))


def _accepted(frame: DichromeFrame) -> None:
    report = inspect_frame(frame)
    if not report.accepted:
        raise ValueError("obstructed frame: " + ", ".join(p.code + "@" + p.at for p in report.obstructions))


def _maps(frame: DichromeFrame) -> tuple[dict[str, Position], dict[str, tuple[Continuation, ...]]]:
    positions = {p.name: p for p in frame.positions}
    outgoing = {name: tuple(c for c in frame.continuations if c.source == name) for name in positions}
    return positions, outgoing


def _reachable(frame: DichromeFrame, origin: str) -> frozenset[str]:
    positions, outgoing = _maps(frame)
    if origin not in positions:
        raise KeyError(origin)
    seen, pending = {origin}, [origin]
    while pending:
        for c in outgoing[pending.pop()]:
            if c.target not in seen:
                seen.add(c.target)
                pending.append(c.target)
    return frozenset(seen)


def _observation(p: Position) -> tuple[frozenset[str], frozenset[str], str | None]:
    return p.geometry, p.commitments, p.outcome


def _landings(frame: DichromeFrame, origin: str) -> frozenset[tuple]:
    positions, _ = _maps(frame)
    return frozenset(_observation(positions[name]) for name in _reachable(frame, origin)
                     if positions[name].outcome is not None)


class Evidence(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    CONFLICTED = "CONFLICTED"


@dataclass(frozen=True)
class PathWitness:
    positions: tuple[str, ...]
    continuations: tuple[str, ...]
    labels: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if (not isinstance(self.positions, tuple) or not self.positions
                or not all(_name(p) for p in self.positions)
                or not isinstance(self.continuations, tuple) or len(self.continuations) > MAX_PATH
                or not all(_name(c) for c in self.continuations)
                or not isinstance(self.labels, tuple) or len(self.labels) != len(self.continuations)
                or len(self.positions) != len(self.continuations) + 1
                or not all(isinstance(label, tuple) and len(label) == 2 and all(_name(s) for s in label)
                           for label in self.labels)):
            raise ValueError("path witness must retain one more position than its named paired continuations")


def follow_path(frame: DichromeFrame, origin: str, route: tuple[str, ...]) -> PathWitness:
    _accepted(frame)
    positions, _ = _maps(frame)
    if origin not in positions:
        raise KeyError(origin)
    if not isinstance(route, tuple) or len(route) > MAX_PATH or not all(_name(c) for c in route):
        raise ValueError("a route is a finite tuple of named continuations")
    moves = {c.name: c for c in frame.continuations}
    trace, labels = [origin], []
    for name in route:
        c = moves[name]
        if c.source != trace[-1]:
            raise ValueError("path is severed before " + name)
        trace.append(c.target)
        labels.append(c.label)
    return PathWitness(tuple(trace), route, tuple(labels))


def compose_paths(left: PathWitness, right: PathWitness) -> PathWitness:
    if not left.positions or not right.positions or left.positions[-1] != right.positions[0]:
        raise ValueError("path ends do not meet")
    if len(left.continuations) + len(right.continuations) > MAX_PATH:
        raise ValueError("composed path exceeds finite route bound")
    return PathWitness(left.positions + right.positions[1:], left.continuations + right.continuations,
                       left.labels + right.labels)


@dataclass(frozen=True)
class ReproductionObstruction:
    pair: tuple[str, str]
    refinement: int
    attacking_side: str
    continuation: str | None
    candidate_replies: tuple[str, ...]
    reason: str


def _mutual_reproduction(left: DichromeFrame, right: DichromeFrame) -> tuple[set[tuple[str, str]], dict]:
    """Greatest finite strong bisimulation; a proposed sufficient path test."""
    lp, lo = _maps(left)
    rp, ro = _maps(right)
    retained, removed = set(), {}
    for a in lp:
        for b in rp:
            if _observation(lp[a]) == _observation(rp[b]):
                retained.add((a, b))
            else:
                removed[a, b] = ReproductionObstruction((a, b), 0, "both", None, (), "paired observations differ")
    refinement = 0
    while True:
        rejected = {}
        refinement += 1
        for a, b in sorted(retained):
            for side, attacks, replies in (("left", lo[a], ro[b]), ("right", ro[b], lo[a])):
                for attack in attacks:
                    candidates = tuple(reply for reply in replies if reply.label == attack.label)
                    if not any((attack.target, reply.target) in retained if side == "left"
                               else (reply.target, attack.target) in retained for reply in candidates):
                        rejected[a, b] = ReproductionObstruction(
                            (a, b), refinement, side, attack.name,
                            tuple(reply.name for reply in candidates),
                            "no reply with both colors" if not candidates else "all matching continuation pairs were eliminated")
                        break
                if (a, b) in rejected:
                    break
        if not rejected:
            return retained, removed
        retained.difference_update(rejected)
        removed.update(rejected)


@dataclass(frozen=True)
class FiltrationReport:
    classification: str
    similar: Evidence
    congruent: Evidence
    simulation: Evidence
    left_landings: frozenset[tuple]
    right_landings: frozenset[tuple]
    obstruction: ReproductionObstruction | None
    qualification: str


def filtration(frame: DichromeFrame, a: str, b: str, other: DichromeFrame | None = None) -> FiltrationReport:
    """Finite diagnostics inspired by ~~, =~, ==; not a native relation derivation."""
    right = frame if other is None else other
    if a not in _maps(frame)[0] or b not in _maps(right)[0]:
        raise KeyError("filtration names an undeclared position")
    if not inspect_frame(frame).accepted or not inspect_frame(right).accepted:
        return FiltrationReport("FRAME", Evidence.CONFLICTED, Evidence.CONFLICTED, Evidence.CONFLICTED,
                                frozenset(), frozenset(), None, "paired transport or invariants are obstructed")
    left_landings, right_landings = _landings(frame, a), _landings(right, b)
    complete = frame.exhaustive and right.exhaustive
    similar = Evidence.PASS if left_landings & right_landings else Evidence.FAIL if complete else Evidence.UNKNOWN
    congruent = (Evidence.PASS if complete and left_landings and left_landings == right_landings
                 else Evidence.FAIL if complete else Evidence.UNKNOWN)
    retained, removed = _mutual_reproduction(frame, right)
    simulation = (Evidence.PASS if complete and congruent is Evidence.PASS and (a, b) in retained
                  else Evidence.FAIL if complete else Evidence.UNKNOWN)
    return FiltrationReport("FRAME", similar, congruent, simulation, left_landings, right_landings,
                            removed.get((a, b)), "finite declared transitions; native bisimulation bridge remains OPEN")


@dataclass(frozen=True)
class ClosureReport:
    classification: str
    status: Evidence
    route: PathWitness
    return_relation: FiltrationReport
    qualification: str


def closure(frame: DichromeFrame, origin: str, route: tuple[str, ...]) -> ClosureReport:
    path = follow_path(frame, origin, route)
    relation = filtration(frame, origin, path.positions[-1])
    status = relation.simulation if route else Evidence.FAIL
    return ClosureReport("FRAME", status, path, relation,
                         "productive paired path return; neither a native □-closure nor universal convergence")


@dataclass(frozen=True)
class DivergenceFamily:
    name: str
    members: frozenset[str]

    def __post_init__(self) -> None:
        if not _name(self.name) or not _atoms(self.members) or not self.members:
            raise ValueError("a divergence family requires a name and finite non-empty membership")


@dataclass(frozen=True)
class FamilyConvergenceReport:
    classification: str
    status: Evidence
    family_divergence: tuple[tuple[str, bool], ...]
    distinct_divergence_families: bool
    settled_class: frozenset[str]
    stable: bool
    inevitability_layers: tuple[frozenset[str], ...]
    basin: frozenset[str]
    obstructed_members: tuple[tuple[str, str], ...]
    qualification: str


def converge_families(frame: DichromeFrame, families: tuple[DivergenceFamily, ...],
                     representative: str) -> FamilyConvergenceReport:
    """Universal convergence of distinct divergence families to a stable paired path class."""
    _accepted(frame)
    positions, outgoing = _maps(frame)
    if representative not in positions:
        raise KeyError(representative)
    if (not isinstance(families, tuple) or not 1 <= len(families) <= MAX_POSITIONS
            or not all(isinstance(f, DivergenceFamily) for f in families)
            or len({f.name for f in families}) != len(families)
            or any(not f.members <= positions.keys() for f in families)):
        raise ValueError("convergence requires distinct named families of declared positions")
    relation, _ = _mutual_reproduction(frame, frame)
    productive = bool(_landings(frame, representative))
    settled = frozenset(p for p in positions if productive and (representative, p) in relation)
    stable = bool(settled) and all(outgoing[p] and all(c.target in settled for c in outgoing[p]) for p in settled)
    family_divergence = tuple((f.name, any((a, b) not in relation for a in f.members for b in f.members))
                              for f in families)
    profiles = [frozenset(frozenset(q for q in positions if (p, q) in relation) for p in f.members)
                for f in families]
    distinct = len(profiles) >= 2 and len(set(profiles)) >= 2
    layers: list[frozenset[str]] = [settled] if stable else []
    basin = set(settled) if stable else set()
    while stable:
        layer = frozenset(p for p in positions if p not in basin and outgoing[p]
                          and all(c.target in basin for c in outgoing[p]))
        if not layer:
            break
        layers.append(layer)
        basin.update(layer)
    outside = tuple((f.name, p) for f in families for p in sorted(f.members - basin))
    succeeds = stable and distinct and all(d for _, d in family_divergence) and not outside
    status = Evidence.PASS if succeeds and frame.exhaustive else Evidence.FAIL if frame.exhaustive else Evidence.UNKNOWN
    return FamilyConvergenceReport("FRAME", status, family_divergence, distinct, settled, stable,
                                   tuple(layers), frozenset(basin), outside,
                                   "all declared choices converge; incomplete declarations stay UNKNOWN; native hyperorder identity OPEN")


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted((_plain(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    return value


def to_json(value: Any) -> str:
    return json.dumps(_plain(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def describe(frame: DichromeFrame) -> dict:
    """Every retained incidence, coloring and rule; summaries are not trusted inputs."""
    _accepted(frame)
    return {"schema": "hyperorder.paired-continuation/1", "classification": "FRAME",
            "positions": _plain(frame.positions), "continuations": _plain(frame.continuations),
            "geometry_invariants": _plain(frame.geometry_invariants),
            "meaning_invariants": _plain(frame.meaning_invariants), "exhaustive": frame.exhaustive}


def _exact_fields(value: Any, required: set[str]) -> None:
    if type(value) is not dict or set(value) != required:
        raise ValueError("description has missing or additional fields")


def _read_atoms(value: Any) -> frozenset[str]:
    if (type(value) is not list or len(value) > MAX_ATOMS or not all(_name(x) for x in value)
            or len(set(value)) != len(value)):
        raise ValueError("description atoms must be distinct named strings")
    return frozenset(value)


def read_description(record: dict) -> DichromeFrame:
    _exact_fields(record, {"schema", "classification", "positions", "continuations", "geometry_invariants",
                           "meaning_invariants", "exhaustive"})
    if record["schema"] != "hyperorder.paired-continuation/1" or record["classification"] != "FRAME":
        raise ValueError("unsupported description schema or stronger classification")
    if (type(record["positions"]) is not list or not 1 <= len(record["positions"]) <= MAX_POSITIONS
            or type(record["continuations"]) is not list or len(record["continuations"]) > MAX_CONTINUATIONS):
        raise ValueError("description exceeds finite frame bounds")
    positions, continuations = [], []
    for p in record["positions"]:
        _exact_fields(p, {"name", "geometry", "commitments", "outcome"})
        positions.append(Position(p["name"], _read_atoms(p["geometry"]), _read_atoms(p["commitments"]), p["outcome"]))
    for c in record["continuations"]:
        _exact_fields(c, {"name", "source", "target", "operation", "rationale", "add_geometry", "remove_geometry",
                          "add_commitments", "remove_commitments"})
        continuations.append(Continuation(c["name"], c["source"], c["target"], c["operation"], c["rationale"],
                                          *(_read_atoms(c[key]) for key in ("add_geometry", "remove_geometry",
                                                                          "add_commitments", "remove_commitments"))))
    frame = DichromeFrame(tuple(positions), tuple(continuations), _read_atoms(record["geometry_invariants"]),
                          _read_atoms(record["meaning_invariants"]), record["exhaustive"])
    _accepted(frame)
    return frame


def verify_description(frame: DichromeFrame, record: dict) -> Evidence:
    """Bind recovery to the whole original frame; same endpoints do not certify rules."""
    try:
        recovered = read_description(record)
    except (ValueError, TypeError, KeyError):
        return Evidence.FAIL
    return Evidence.PASS if describe(frame) == describe(recovered) else Evidence.FAIL


def example_frame(*, escape: bool = False, incomplete: bool = False) -> tuple[DichromeFrame, tuple[DivergenceFamily, ...]]:
    """Two divergences-of-branches converge while keeping both colorings operational."""
    core_geometry = frozenset({"paired-incidence"})
    core_meaning = frozenset({"retain-both-colors"})
    positions = (
        Position("geometry-route", core_geometry | {"geometry-first"}, core_meaning | {"interpret-shape"}),
        Position("meaning-route", core_geometry | {"meaning-first"}, core_meaning | {"shape-interpretation"}),
        Position("meta-geometry-route", core_geometry | {"meta-geometry-first"}, core_meaning | {"interpret-rules"}),
        Position("meta-meaning-route", core_geometry | {"meta-meaning-first"}, core_meaning | {"rules-interpretation"}),
        Position("paired-form", core_geometry | {"self-description"}, core_meaning | {"joint-interpretation"}, "paired-landing"),
        Position("paired-self-read", core_geometry | {"self-description"}, core_meaning | {"joint-interpretation"}, "paired-landing"),
    )
    target = positions[-2]
    moves = [Continuation("close-" + p.name, p.name, "paired-form", "join-" + p.name,
                          "retain and reconcile both colorings", target.geometry - p.geometry,
                          p.geometry - target.geometry, target.commitments - p.commitments,
                          p.commitments - target.commitments) for p in positions[:4]]
    moves.extend((Continuation("self-read", "paired-form", "paired-self-read", "self-read", "retain incidence and commitments"),
                  Continuation("self-return", "paired-self-read", "paired-form", "self-read", "retain incidence and commitments")))
    if escape:
        p = Position("unresolved-escape", core_geometry | {"escape"}, core_meaning | {"not-reconciled"})
        first = positions[0]
        positions += (p,)
        moves.append(Continuation("escape", first.name, p.name, "unreconciled-branch", "retain but fail to reconcile",
                                  p.geometry - first.geometry, first.geometry - p.geometry,
                                  p.commitments - first.commitments, first.commitments - p.commitments))
    frame = DichromeFrame(positions, tuple(moves), core_geometry, core_meaning, not incomplete)
    families = (DivergenceFamily("base-divergence", frozenset({"geometry-route", "meaning-route"})),
                DivergenceFamily("meta-divergence", frozenset({"meta-geometry-route", "meta-meaning-route"})))
    return frame, families
