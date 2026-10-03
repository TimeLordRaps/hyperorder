# Hyperorder

**The form in which geometry and philosophy are no longer separable.** In
[Hypergrammar](https://github.com/TimeLordRaps/hypergrammar/blob/d4df988be65636bf66d6d3f8ef5a85edf524d8dc/docs/prerequisites/21_hypertopologies.md),
the dichrome closes geometry and philosophy into a single form, hyperorder:
"the geometric philosophy and philosophical geometry of itself". Hyperorder
generates its own hypertopology, and hypermath is formed from that
self-description. Hypergrammar calls that build chain a closure, not a line.

On 2026-09-30 Tyler Roost / The TimeLord added a second statement:

> "Chaos realigns into order, this has to do with atemporality, also
> hyperorder and hyperchaos theories might need grounding from hyperethics,
> Im not sure"

On 2026-10-03 Tyler clarified the operational direction: divergences diverging
into convergent states are associated with hyperorder; convergence towards
divergence is associated with hyperchaos. A butterfly effect redirecting one
orderly trajectory is first-order chaos. The distinction is part of this
field's research program; it does not identify every converging process with
the native dichrome.

This repository now develops [the theory](THEORY.md) and an executable
[paired continuation frame](dichrome.py). Each position retains geometric
structure and interpretive commitments. Each continuation must reproduce
both colorings exactly. An undeclared structural change, a missing meaning
premise or a lost invariant is an explicit obstruction.

The field follows the published
[quadrilateral filtration architecture](https://github.com/TimeLordRaps/hypermath/blob/dc89cbb4f154844ca4909d7c1c359ee3882323e2/docs/research/QUADRILATERAL_FILTRATION.md):
`~~`, `=~`, `==` remain the concrete branch, while **`~=` is a separate
path-schema abstraction surface**. The executable version is an explicit
[FRAME] proposal with selected-path evidence and guarded retrace. It does
not insert `~=` as a linear L1 midpoint or claim a native relation proof.

The mechanisms support:

- Continuation capacity overlap, full substance-landings coincidence and
  mutual path reproduction. The last check retains both operation and
  rationale and follows successors through a greatest-fixed-point
  calculation. A shared landing cannot hide a different path.
- Retained path traversal and associative composition. A non-empty paired
  return has its own bounded closure diagnostic.
- Typed paired path projection: retain ordered structure, interpretations,
  both color transforms and invariants, while forgetting incidental names
  and unselected branches in the schema. An explicit optional policy can
  forget only multiplicity of identical stationary paired rules.
- Conditional retrace bound to the complete frame, retained projection and
  original route. Forged or transplanted evidence fails. PASS reports
  selected path recovery; global path reproduction is reported separately.
- Convergence of **distinct divergence families** to a productive stable
  continuation class. Every declared alternative must enter the basin;
  one favorable path cannot hide an escape or an outside cycle.
- A complete operational self-description: recover positions, both
  colorings, rules, incidences and invariants, then recheck them. A changed
  rule fails the exact description binding even with the same landing.
- An installable standard-library Python package and a command-line
  interface (CLI) for these operations. No service or dependency is needed
  to execute the model.

Try the retained model:

```console
python -B -u hyperorder.py demo
python -B -u hyperorder.py demo --escape
python -B -u hyperorder.py demo --incomplete
python -B -u hyperorder.py converge examples/paired-frame.json examples/divergence-families.json paired-form
python -B -u hyperorder.py compare examples/paired-frame.json geometry-route meaning-route
python -B -u hyperorder.py trace examples/paired-frame.json paired-form self-read self-return
python -B -u hyperorder.py quad examples/paired-frame.json paired-form paired-form --left-route self-read --right-route self-read self-return self-read --projection stationary --retrace
python -B -u hyperorder.py quad examples/abstraction-escape-frame.json left-start right-start --left-route left-step --right-route right-step --projection exact --retrace
python -B -u hyperorder.py describe examples/paired-frame.json
```

The first demo reports PASS for two distinct divergence families entering
one stable paired path class. The escape variant reports FAIL; the
incomplete variant reports UNKNOWN. Geometry-first and meaning-first
routes share substance landings but fail mutual path reproduction.
`compare` exits 1 for that supported obstruction, rather than reporting
a successful simulation.

The `quad` command compares one self-read with a three-step stationary run.
Its optional policy produces matching schemas, while the retrace reports
recover the original one-step and three-step paths separately. Use
`--projection exact` to retain their multiplicity and observe abstraction
FAIL. Without explicit paths and policy, abstraction stays UNKNOWN. The
demo includes all four statuses, exact witness bindings and a separate
native-promotion UNKNOWN. The `abstraction-escape-frame` example reports
selected abstraction and both original path recoveries PASS while global
congruence/simulation FAIL. Its exit 0 supports the requested selected
schema/recovery proposition; the separately reported escape remains an
obstruction. [The theory](THEORY.md) explains the distinction.

Install with `python -m pip install .` to use the `hyperorder` command.
Python 3.12 or later is required. Input records are retained as ordinary
JSON (JavaScript Object Notation), with a strict finite schema.

The original [ordinal bookkeeping](hyperorder.py) remains available:

- **No silent identification.** `hyperorder` resolves to its one sourced
  sense. `order` resolves to nothing. The 2026-09-30 statement is recorded,
  open, beside the sense, and is not merged into it.
- **Ordinal, not numeric.** Positions are names, never numbers. Relations are
  declared, and a comparison has five verdicts: PRECEDES, FOLLOWS,
  INCOMPARABLE, UNKNOWN and CONFLICTED. A relation nobody declared is
  UNKNOWN, not INCOMPARABLE. A cycle is CONFLICTED, not equality.
  Totality is a claim, checked when it is made.

[FRAME] The mechanisms use named positions and declared continuations,
without a physical time coordinate. Computation's finite refinement rounds
and admission layers do not turn hyperorder into a numerical rank. Ordering
among reality presentations belongs to
[Hypertime](https://github.com/TimeLordRaps/hypertime).
[Hyperchaos](https://github.com/TimeLordRaps/hyperchaos)'s divergence direction
is held apart from this field's convergence direction. The sibling adapter
is not yet implemented. [FIELD.json](FIELD.json) is an integration
descriptor, not a Verifier Standard (VSTD) certificate.

[OPEN] The Python operations are proposed finite research mechanisms. They
do not produce native □-formation, establish the full self-closing
hypertopology or discharge Hypermath's relation-adequacy and transfinite
obligations. The exact gaps and the finite propositions are in
[THEORY.md](THEORY.md), rather than hidden behind a generic implementation
claim.

Run the full standard-library suite with `python -B -u validate.py`. The runner
streams named tests under a 20-second overall deadline. It has no per-test
process isolation. Open questions are in [FIELD_SPEC.md](FIELD_SPEC.md),
sources in [PROVENANCE.md](PROVENANCE.md), obligations in
[TECHNICAL_DEBT.md](TECHNICAL_DEBT.md), and the next step in
[AGENT_HANDOFF.md](AGENT_HANDOFF.md).
