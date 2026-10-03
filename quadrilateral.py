"""[FRAME] Selected paired path schemas and exact conditional recovery.

The off-branch ~= surface is separate from the concrete L1-inspired diagnostics.
It is neither native Form equivalence nor a closure of continuation overlap.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from dichrome import (DichromeFrame, Evidence, FiltrationReport, MAX_PATH, PathWitness,
                      _atoms, _name, _plain, describe, filtration, follow_path)


def _digest(value: object) -> str:
    encoded = json.dumps(_plain(value), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


@dataclass(frozen=True)
class ProjectionPolicy:
    """Forget identifiers; optionally forget repetition of stationary paired rules.

    This flag is a finite schema choice, never a native quantification measure.
    """

    collapse_stationary_repetition: bool = False

    def __post_init__(self) -> None:
        if type(self.collapse_stationary_repetition) is not bool:
            raise ValueError("stationary repetition policy must be an explicit Boolean")


@dataclass(frozen=True)
class PairedObservation:
    geometry: frozenset[str]
    commitments: frozenset[str]
    outcome: str | None

    def __post_init__(self) -> None:
        if (not _atoms(self.geometry) or not self.geometry
                or not _atoms(self.commitments) or not self.commitments
                or (self.outcome is not None and not _name(self.outcome))):
            raise ValueError("paired observations retain both nonempty colorings and an optional outcome")


@dataclass(frozen=True)
class SchemaStep:
    before: PairedObservation
    after: PairedObservation
    operation: str
    rationale: str
    add_geometry: frozenset[str]
    remove_geometry: frozenset[str]
    add_commitments: frozenset[str]
    remove_commitments: frozenset[str]

    def __post_init__(self) -> None:
        if (not isinstance(self.before, PairedObservation) or not isinstance(self.after, PairedObservation)
                or not _name(self.operation) or not _name(self.rationale)):
            raise ValueError("schema steps retain typed paired ends and both rule labels")
        for before, after, added, removed in (
            (self.before.geometry, self.after.geometry, self.add_geometry, self.remove_geometry),
            (self.before.commitments, self.after.commitments, self.add_commitments, self.remove_commitments),
        ):
            if (not _atoms(added) or not _atoms(removed) or added & removed
                    or not removed <= before or added & before or (before - removed) | added != after):
                raise ValueError("schema step fails exact paired transport")

    @property
    def stationary(self) -> bool:
        return (self.before == self.after and not self.add_geometry and not self.remove_geometry
                and not self.add_commitments and not self.remove_commitments)


@dataclass(frozen=True)
class PathSchema:
    start: PairedObservation
    end: PairedObservation
    steps: tuple[SchemaStep, ...]
    geometry_invariants: frozenset[str]
    meaning_invariants: frozenset[str]

    def __post_init__(self) -> None:
        if (not isinstance(self.start, PairedObservation) or not isinstance(self.end, PairedObservation)
                or not isinstance(self.steps, tuple) or len(self.steps) > MAX_PATH
                or not all(isinstance(step, SchemaStep) for step in self.steps)
                or not _atoms(self.geometry_invariants) or not _atoms(self.meaning_invariants)):
            raise ValueError("path schema is typed, immutable and finitely bounded")
        cursor = self.start
        for step in self.steps:
            if step.before != cursor:
                raise ValueError("schema order severs paired incidence")
            cursor = step.after
        if cursor != self.end:
            raise ValueError("schema endpoint does not match its ordered steps")
        for observation in (self.start, self.end, *(step.before for step in self.steps)):
            if (not self.geometry_invariants <= observation.geometry
                    or not self.meaning_invariants <= observation.commitments):
                raise ValueError("path schema loses a declared invariant")


@dataclass(frozen=True)
class PathProjection:
    policy: ProjectionPolicy
    source_digest: str
    path_digest: str
    schema: PathSchema
    classification: str = "FRAME"
    schema_version: str = "hyperorder.paired-path-projection/1"

    def __post_init__(self) -> None:
        if (not isinstance(self.policy, ProjectionPolicy) or not isinstance(self.schema, PathSchema)
                or not _is_digest(self.source_digest) or not _is_digest(self.path_digest)
                or self.classification != "FRAME" or self.schema_version != "hyperorder.paired-path-projection/1"):
            raise ValueError("projection requires its typed schema, policy and exact binding coordinates")

    @property
    def projection_digest(self) -> str:
        return _digest(self)


@dataclass(frozen=True)
class RetraceWitness:
    source_digest: str
    projection_digest: str
    origin: str
    route: tuple[str, ...]

    def __post_init__(self) -> None:
        if (not _is_digest(self.source_digest) or not _is_digest(self.projection_digest)
                or not _name(self.origin) or not isinstance(self.route, tuple)
                or len(self.route) > MAX_PATH or not all(_name(name) for name in self.route)):
            raise ValueError("retrace witness requires bounded exact route and binding coordinates")


@dataclass(frozen=True)
class AbstractionReport:
    classification: str
    status: Evidence
    left: PathProjection | None
    right: PathProjection | None
    retained: tuple[str, ...]
    forgotten: tuple[str, ...]
    qualification: str


@dataclass(frozen=True)
class RetraceReport:
    classification: str
    status: Evidence
    recovered_path: PathWitness | None
    checks: tuple[str, ...]
    reason: str
    native_semantic_promotion: Evidence = Evidence.UNKNOWN
    qualification: str = "selected finite path recovery only; native ~= adequacy and == promotion remain OPEN"


@dataclass(frozen=True)
class QuadrilateralReport:
    classification: str
    similar: Evidence
    congruent: Evidence
    simulation: Evidence
    abstracted: Evidence
    concrete: FiltrationReport
    abstraction: AbstractionReport
    left_retrace: RetraceReport
    right_retrace: RetraceReport
    qualification: str = "~~, =~, == are concrete diagnostics; ~= is a separate selected-path schema comparison [FRAME]"
    native_adequacy: str = "OPEN"


def project_path(frame: DichromeFrame, path: PathWitness, policy: ProjectionPolicy) -> PathProjection:
    """Replay first, then forget only the declared details in the selected schema."""
    if not isinstance(path, PathWitness) or not isinstance(policy, ProjectionPolicy):
        raise ValueError("projection needs an explicit typed path and policy")
    replayed = follow_path(frame, path.positions[0], path.continuations)
    if replayed != path:
        raise ValueError("supplied path witness differs from exact paired replay")
    positions = {position.name: position for position in frame.positions}
    moves = {move.name: move for move in frame.continuations}

    def observation(name: str) -> PairedObservation:
        p = positions[name]
        return PairedObservation(p.geometry, p.commitments, p.outcome)

    steps = []
    for name in path.continuations:
        move = moves[name]
        step = SchemaStep(observation(move.source), observation(move.target), move.operation, move.rationale,
                          move.add_geometry, move.remove_geometry, move.add_commitments, move.remove_commitments)
        if (policy.collapse_stationary_repetition and step.stationary
                and steps and steps[-1] == step):
            continue
        steps.append(step)
    schema = PathSchema(observation(path.positions[0]), observation(path.positions[-1]), tuple(steps),
                        frame.geometry_invariants, frame.meaning_invariants)
    return PathProjection(policy, _digest(describe(frame)), _digest(path), schema)


def path_abstraction(left_frame: DichromeFrame, left_path: PathWitness | None,
                     right_frame: DichromeFrame, right_path: PathWitness | None,
                     policy: ProjectionPolicy | None) -> AbstractionReport:
    if (policy is not None and not isinstance(policy, ProjectionPolicy)
            or left_path is not None and not isinstance(left_path, PathWitness)
            or right_path is not None and not isinstance(right_path, PathWitness)):
        raise ValueError("off-branch comparison requires typed paths and projection policy")
    retained = ("paired endpoint observations", "ordered paired rule schemas and interpretations",
                "exact structural and meaning deltas", "declared invariants", "projection policy")
    forgotten = ("position and continuation names", "unselected continuation branches")
    if policy is not None and policy.collapse_stationary_repetition:
        forgotten += ("multiplicity within consecutive identical stationary paired-rule runs",)
    if left_path is None or right_path is None or policy is None:
        return AbstractionReport("FRAME", Evidence.UNKNOWN, None, None, retained, forgotten,
                                 "off-branch comparison requires two explicit paths and a projection policy")
    left = project_path(left_frame, left_path, policy)
    right = project_path(right_frame, right_path, policy)
    status = Evidence.PASS if left.schema == right.schema else Evidence.FAIL
    return AbstractionReport("FRAME", status, left, right, retained, forgotten,
                             "schema equality of selected replayed paths; source/path bindings are distinct from equivalence")


def make_retrace_witness(frame: DichromeFrame, projection: PathProjection, path: PathWitness) -> RetraceWitness:
    """Prepare recoverable evidence only for the original bound path selection."""
    if not isinstance(projection, PathProjection) or project_path(frame, path, projection.policy) != projection:
        raise ValueError("cannot bind retrace witness to a different projection")
    return RetraceWitness(projection.source_digest, projection.projection_digest,
                          path.positions[0], path.continuations)


def conditional_retrace(frame: DichromeFrame, projection: PathProjection | None,
                        witness: RetraceWitness | None) -> RetraceReport:
    """Reconstruct a selected path; do not assume the semantic conclusion as a premise."""
    if projection is None or witness is None:
        return RetraceReport("FRAME", Evidence.UNKNOWN, None, (), "projection and exact route witness are required")
    if not isinstance(projection, PathProjection) or not isinstance(witness, RetraceWitness):
        raise ValueError("retrace requires typed projection and witness")
    checks = []
    try:
        if _digest(describe(frame)) != projection.source_digest or witness.source_digest != projection.source_digest:
            raise ValueError("SOURCE_BINDING: witness or projection belongs to a different complete frame record")
        checks.append("SOURCE_BINDING")
        if witness.projection_digest != projection.projection_digest:
            raise ValueError("PROJECTION_BINDING: witness belongs to a different schema or policy")
        checks.append("PROJECTION_BINDING")
        path = follow_path(frame, witness.origin, witness.route)
        checks.append("PAIRED_REPLAY")
        if _digest(path) != projection.path_digest:
            raise ValueError("PATH_BINDING: schema agreement cannot substitute another original route")
        checks.append("PATH_BINDING")
        if project_path(frame, path, projection.policy) != projection:
            raise ValueError("SCHEMA_RECONSTRUCTION: replay does not recover the retained projection")
        checks.append("SCHEMA_RECONSTRUCTION")
    except (ValueError, KeyError, TypeError) as error:
        return RetraceReport("FRAME", Evidence.FAIL, None, tuple(checks), str(error))
    return RetraceReport("FRAME", Evidence.PASS, path, tuple(checks), "original selected paired path recovered")


def quadrilateral(frame: DichromeFrame, a: str, b: str,
                  left_path: PathWitness | None = None, right_path: PathWitness | None = None,
                  policy: ProjectionPolicy | None = None, other: DichromeFrame | None = None,
                  left_witness: RetraceWitness | None = None,
                  right_witness: RetraceWitness | None = None) -> QuadrilateralReport:
    """Inspect four routes without ranking off-branch ~= among L1 relations."""
    right = frame if other is None else other
    if (left_path is not None and (not isinstance(left_path, PathWitness) or left_path.positions[0] != a)
            or right_path is not None and (not isinstance(right_path, PathWitness) or right_path.positions[0] != b)):
        raise ValueError("selected paths must originate at the compared positions")
    concrete = filtration(frame, a, b, right)
    abstract = path_abstraction(frame, left_path, right, right_path, policy)
    return QuadrilateralReport("FRAME", concrete.similar, concrete.congruent, concrete.simulation,
                               abstract.status, concrete, abstract,
                               conditional_retrace(frame, abstract.left, left_witness),
                               conditional_retrace(right, abstract.right, right_witness))
