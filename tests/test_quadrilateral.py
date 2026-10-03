"""Refutable gates for the separate path-schema abstraction branch [FRAME]."""

import unittest
from dataclasses import replace
import itertools
import json
from pathlib import Path
import subprocess
import sys
import hyperorder as h


class AbsentQuadrilateralBaseline(unittest.TestCase):
    def test_typed_path_abstraction_and_guarded_retrace_exist(self):
        required = ("ProjectionPolicy", "PairedObservation", "SchemaStep", "PathSchema",
                    "PathProjection", "RetraceWitness", "AbstractionReport", "RetraceReport",
                    "QuadrilateralReport", "project_path", "path_abstraction",
                    "make_retrace_witness", "conditional_retrace", "quadrilateral")
        self.assertEqual([name for name in required if not hasattr(h, name)], [])


def paired(name, geometry=("incidence",), meaning=("interpretation",), outcome=None):
    return h.Position(name, frozenset(geometry), frozenset(meaning), outcome)


def transform(name, before, after, operation="reconcile", rationale="retain both"):
    return h.Continuation(name, before.name, after.name, operation, rationale,
                          after.geometry - before.geometry, before.geometry - after.geometry,
                          after.commitments - before.commitments, before.commitments - after.commitments)


def selected_frame(prefix="left", escape=False):
    start = paired(prefix + "-start")
    end = paired(prefix + "-end", ("incidence", "self-description"),
                 ("interpretation", "joint-meaning"), "paired-landing")
    positions, moves = (start, end), (transform(prefix + "-step", start, end),)
    if escape:
        outside = paired(prefix + "-escape", ("incidence", "unresolved"),
                         ("interpretation", "unresolved-meaning"), "other-landing")
        positions += (outside,)
        moves += (transform(prefix + "-alternate", start, outside, "escape", "remain unresolved"),)
    return h.DichromeFrame(positions, moves, frozenset({"incidence"}), frozenset({"interpretation"}))


def selected_path(frame):
    return h.follow_path(frame, frame.positions[0].name, (frame.continuations[0].name,))


class SelectedSchemaTests(unittest.TestCase):
    def test_abstract_agreement_and_global_concrete_mismatch_are_separate(self):
        left, right = selected_frame(), selected_frame("right", escape=True)
        a, b = selected_path(left), selected_path(right)
        report = h.quadrilateral(left, a.positions[0], b.positions[0], a, b, h.ProjectionPolicy(), right)
        self.assertIs(report.similar, h.Evidence.PASS)
        self.assertIs(report.congruent, h.Evidence.FAIL)
        self.assertIs(report.simulation, h.Evidence.FAIL)
        self.assertIs(report.abstracted, h.Evidence.PASS)
        self.assertIs(report.left_retrace.status, h.Evidence.UNKNOWN)
        self.assertEqual(report.native_adequacy, "OPEN")
        self.assertNotEqual(report.abstraction.left.source_digest, report.abstraction.right.source_digest)
        self.assertNotEqual(report.abstraction.left.path_digest, report.abstraction.right.path_digest)
        self.assertEqual(report.abstraction.left.schema, report.abstraction.right.schema)

    def test_missing_paths_or_projection_policy_stay_unknown(self):
        frame, policy = selected_frame(), h.ProjectionPolicy()
        path = selected_path(frame)
        for left, right, choice in ((None, path, policy), (path, None, policy), (path, path, None)):
            with self.subTest(left=left is not None, right=right is not None, policy=choice is not None):
                self.assertIs(h.path_abstraction(frame, left, frame, right, choice).status, h.Evidence.UNKNOWN)
        report = h.quadrilateral(frame, path.positions[0], path.positions[0])
        self.assertIs(report.simulation, h.Evidence.PASS)
        self.assertIs(report.abstracted, h.Evidence.UNKNOWN)

    def test_selected_path_origin_must_match_the_compared_position(self):
        frame, path = selected_frame(), selected_path(selected_frame())
        with self.assertRaisesRegex(ValueError, "originate"):
            h.quadrilateral(frame, frame.positions[1].name, path.positions[0], path, path, h.ProjectionPolicy())

    def test_a_manually_forged_path_is_replayed_before_projection(self):
        frame = selected_frame()
        path = selected_path(frame)
        for forged in (replace(path, labels=(("reconcile", "forged meaning"),)),
                       replace(path, positions=(path.positions[0], path.positions[0]))):
            with self.subTest(forged=forged):
                with self.assertRaisesRegex(ValueError, "exact paired replay"):
                    h.project_path(frame, forged, h.ProjectionPolicy())

    def test_ordered_structure_and_meaning_are_retained_independently(self):
        frame = selected_frame()
        policy = h.ProjectionPolicy()
        path = selected_path(frame)
        projection = h.project_path(frame, path, policy)
        step = projection.schema.steps[0]
        self.assertEqual(step.add_geometry, frozenset({"self-description"}))
        self.assertEqual(step.add_commitments, frozenset({"joint-meaning"}))
        self.assertEqual(projection.schema.geometry_invariants, frozenset({"incidence"}))
        for changes in ({"rationale": "other interpretation"}, {"operation": "other structure"}):
            other = replace(frame, continuations=(replace(frame.continuations[0], **changes),))
            self.assertIs(h.path_abstraction(frame, path, other, selected_path(other), policy).status, h.Evidence.FAIL)

    def test_invariant_declaration_change_is_not_forgotten(self):
        frame = selected_frame()
        other = replace(frame, geometry_invariants=frozenset())
        self.assertIs(h.path_abstraction(frame, selected_path(frame), other, selected_path(other),
                                        h.ProjectionPolicy()).status, h.Evidence.FAIL)

    def test_outcome_changes_are_not_stationary_even_with_identical_colors(self):
        start, end = paired("a", outcome="first"), paired("b", outcome="second")
        frame = h.DichromeFrame((start, end), (transform("ab", start, end), transform("ba", end, start)))
        path = h.follow_path(frame, "a", ("ab", "ba", "ab"))
        projection = h.project_path(frame, path, h.ProjectionPolicy(True))
        self.assertEqual(len(projection.schema.steps), 3)
        self.assertFalse(any(step.stationary for step in projection.schema.steps))

    def test_incidental_renaming_and_source_array_permutations_do_not_change_schema(self):
        frame = selected_frame()
        renamed = selected_frame("unrelated")
        reordered = replace(renamed, positions=tuple(reversed(renamed.positions)))
        original = h.project_path(frame, selected_path(frame), h.ProjectionPolicy())
        other_path = h.follow_path(reordered, "unrelated-start", ("unrelated-step",))
        alternate = h.project_path(reordered, other_path, h.ProjectionPolicy())
        self.assertEqual(original.schema, alternate.schema)
        self.assertNotEqual(original.projection_digest, alternate.projection_digest)

    def test_typed_schema_and_policy_reject_coercion_severing_and_bounds(self):
        frame = selected_frame()
        projection = h.project_path(frame, selected_path(frame), h.ProjectionPolicy())
        with self.assertRaises(ValueError):
            h.ProjectionPolicy(1)
        with self.assertRaises(ValueError):
            replace(projection.schema.steps[0], add_geometry=frozenset())
        with self.assertRaises(ValueError):
            replace(projection.schema, steps=())
        with self.assertRaises(ValueError):
            replace(projection.schema, steps=projection.schema.steps * 257)
        with self.assertRaises(ValueError):
            replace(projection, source_digest="true")
        with self.assertRaises(ValueError):
            h.project_path(frame, selected_path(frame), None)
        with self.assertRaises(ValueError):
            h.path_abstraction(frame, None, frame, None, True)


class StationaryProjectionTests(unittest.TestCase):
    def setUp(self):
        self.frame, _ = h.example_frame()
        self.short = h.follow_path(self.frame, "paired-form", ("self-read",))
        self.long = h.follow_path(self.frame, "paired-form", ("self-read", "self-return", "self-read"))

    def test_repetition_is_forgotten_only_under_an_explicit_policy(self):
        for collapse, expected in ((False, h.Evidence.FAIL), (True, h.Evidence.PASS)):
            with self.subTest(collapse=collapse):
                report = h.path_abstraction(self.frame, self.short, self.frame, self.long, h.ProjectionPolicy(collapse))
                self.assertIs(report.status, expected)
                self.assertNotEqual(report.left.path_digest, report.right.path_digest)
                self.assertEqual(len(report.left.schema.steps), 1)
                self.assertEqual(len(report.right.schema.steps), 1 if collapse else 3)

    def test_zero_length_and_nonempty_stationary_paths_do_not_collapse_together(self):
        empty = h.follow_path(self.frame, "paired-form", ())
        self.assertIs(h.path_abstraction(self.frame, empty, self.frame, self.short,
                                        h.ProjectionPolicy(True)).status, h.Evidence.FAIL)

    def test_repetition_projection_is_idempotent_and_does_not_reorder_rules(self):
        start = paired("a", outcome="landing")
        labels = {letter: h.Continuation(letter, "a", "a", letter, "meaning-" + letter) for letter in ("x", "y")}
        frame = h.DichromeFrame((start,), tuple(labels.values()))
        policy = h.ProjectionPolicy(True)
        # An independent run-length oracle covers all binary route words of lengths 0..6.
        for length in range(7):
            for word in itertools.product("xy", repeat=length):
                expected = tuple(letter for i, letter in enumerate(word) if i == 0 or letter != word[i - 1])
                schema = h.project_path(frame, h.follow_path(frame, "a", word), policy).schema
                self.assertEqual(tuple(step.operation for step in schema.steps), expected)
                reduced = h.project_path(frame, h.follow_path(frame, "a", expected), policy).schema
                self.assertEqual(schema, reduced)

    def test_alternating_nonstationary_transforms_never_collapse(self):
        a = paired("a", outcome="landing")
        b = paired("b", ("incidence", "reflection"), ("interpretation", "self-read"), "landing")
        frame = h.DichromeFrame((a, b), (transform("ab", a, b), transform("ba", b, a)))
        path = h.follow_path(frame, "a", ("ab", "ba", "ab", "ba"))
        schema = h.project_path(frame, path, h.ProjectionPolicy(True)).schema
        self.assertEqual(len(schema.steps), 4)
        self.assertFalse(any(step.stationary for step in schema.steps))


class GuardedRetraceTests(unittest.TestCase):
    def setUp(self):
        self.frame = selected_frame()
        self.path = selected_path(self.frame)
        self.projection = h.project_path(self.frame, self.path, h.ProjectionPolicy())
        self.witness = h.make_retrace_witness(self.frame, self.projection, self.path)

    def test_recovery_replays_every_obligation_and_never_claims_native_promotion(self):
        report = h.conditional_retrace(self.frame, self.projection, self.witness)
        self.assertIs(report.status, h.Evidence.PASS)
        self.assertEqual(report.recovered_path, self.path)
        self.assertEqual(report.checks, ("SOURCE_BINDING", "PROJECTION_BINDING", "PAIRED_REPLAY",
                                        "PATH_BINDING", "SCHEMA_RECONSTRUCTION"))
        self.assertIs(report.native_semantic_promotion, h.Evidence.UNKNOWN)

    def test_missing_witness_and_missing_projection_stay_unknown(self):
        self.assertIs(h.conditional_retrace(self.frame, self.projection, None).status, h.Evidence.UNKNOWN)
        self.assertIs(h.conditional_retrace(self.frame, None, self.witness).status, h.Evidence.UNKNOWN)

    def test_projection_cannot_be_transplanted_to_a_frame_with_an_unused_branch(self):
        unused = paired("unused", outcome="unselected")
        other = replace(self.frame, positions=self.frame.positions + (unused,),
                        continuations=self.frame.continuations + (transform("unused-loop", unused, unused),))
        coarse = h.project_path(other, self.path, self.projection.policy)
        self.assertEqual(coarse.schema, self.projection.schema)
        report = h.conditional_retrace(other, self.projection, self.witness)
        self.assertIs(report.status, h.Evidence.FAIL)
        self.assertIn("SOURCE_BINDING", report.reason)

    def test_a_witness_for_an_abstractly_equal_different_route_is_refused(self):
        frame, _ = h.example_frame()
        short = h.follow_path(frame, "paired-form", ("self-read",))
        long = h.follow_path(frame, "paired-form", ("self-read", "self-return", "self-read"))
        policy = h.ProjectionPolicy(True)
        projection = h.project_path(frame, short, policy)
        witness = h.make_retrace_witness(frame, projection, short)
        forged = replace(witness, route=long.continuations)
        self.assertEqual(projection.schema, h.project_path(frame, long, policy).schema)
        report = h.conditional_retrace(frame, projection, forged)
        self.assertIs(report.status, h.Evidence.FAIL)
        self.assertIn("PATH_BINDING", report.reason)
        with self.assertRaises(ValueError):
            h.make_retrace_witness(frame, projection, long)

    def test_forged_retained_meaning_is_refused_even_with_a_recomputed_projection_digest(self):
        step = replace(self.projection.schema.steps[0], rationale="forged interpretation")
        fake = replace(self.projection, schema=replace(self.projection.schema, steps=(step,)))
        forged_witness = replace(self.witness, projection_digest=fake.projection_digest)
        report = h.conditional_retrace(self.frame, fake, forged_witness)
        self.assertIs(report.status, h.Evidence.FAIL)
        self.assertIn("SCHEMA_RECONSTRUCTION", report.reason)

    def test_forged_paired_delta_is_refused_even_when_its_fake_schema_is_internally_valid(self):
        end = replace(self.projection.schema.end, commitments=frozenset({"interpretation", "invented"}))
        step = replace(self.projection.schema.steps[0], after=end, add_commitments=frozenset({"invented"}))
        fake = replace(self.projection, schema=replace(self.projection.schema, end=end, steps=(step,)))
        forged_witness = replace(self.witness, projection_digest=fake.projection_digest)
        report = h.conditional_retrace(self.frame, fake, forged_witness)
        self.assertIs(report.status, h.Evidence.FAIL)
        self.assertIn("SCHEMA_RECONSTRUCTION", report.reason)

    def test_single_bit_binding_tamper_and_missing_route_are_refused(self):
        changed = format(int(self.witness.projection_digest[0], 16) ^ 1, "x") + self.witness.projection_digest[1:]
        for witness in (replace(self.witness, projection_digest=changed),
                        replace(self.witness, route=("nonexistent",))):
            with self.subTest(witness=witness):
                self.assertIs(h.conditional_retrace(self.frame, self.projection, witness).status, h.Evidence.FAIL)

    def test_incomplete_global_declaration_does_not_hide_selected_recovery_scope(self):
        frame = replace(self.frame, exhaustive=False)
        projection = h.project_path(frame, self.path, self.projection.policy)
        witness = h.make_retrace_witness(frame, projection, self.path)
        report = h.quadrilateral(frame, self.path.positions[0], self.path.positions[0],
                                 self.path, self.path, self.projection.policy, left_witness=witness)
        self.assertIs(report.simulation, h.Evidence.UNKNOWN)
        self.assertIs(report.abstracted, h.Evidence.PASS)
        self.assertIs(report.left_retrace.status, h.Evidence.PASS)
        self.assertIs(report.left_retrace.native_semantic_promotion, h.Evidence.UNKNOWN)


class QuadrilateralCommandTests(unittest.TestCase):
    def run_cli(self, *arguments):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-B", "-u", str(root / "hyperorder.py"), *arguments],
                                cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=5)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def test_demo_inspects_all_four_routes_and_recovery_separately(self):
        code, record = self.run_cli("demo")
        self.assertEqual(code, 0)
        quad = record["quadrilateral"]
        self.assertEqual([quad[name] for name in ("similar", "congruent", "simulation", "abstracted")], ["PASS"] * 4)
        self.assertEqual(quad["left_retrace"]["status"], "PASS")
        self.assertEqual(quad["left_retrace"]["native_semantic_promotion"], "UNKNOWN")

    def test_quad_command_requires_explicit_path_and_policy_evidence(self):
        code, record = self.run_cli("quad", "examples/paired-frame.json", "paired-form", "paired-form")
        self.assertEqual(code, 1)
        self.assertEqual(record["abstracted"], "UNKNOWN")
        code, record = self.run_cli("quad", "examples/paired-frame.json", "paired-form", "paired-form",
                                    "--left-route", "self-read", "--right-route", "self-read", "self-return", "self-read",
                                    "--projection", "stationary", "--retrace")
        self.assertEqual(code, 0)
        self.assertEqual(record["abstracted"], "PASS")
        self.assertEqual(len(record["right_retrace"]["recovered_path"]["continuations"]), 3)
        code, record = self.run_cli("quad", "examples/paired-frame.json", "paired-form", "paired-form",
                                    "--left-route", "self-read", "--right-route", "self-read", "self-return", "self-read",
                                    "--projection", "exact")
        self.assertEqual(code, 1)
        self.assertEqual(record["abstracted"], "FAIL")

    def test_cli_preserves_an_escape_obstruction_beside_selected_recovery(self):
        code, record = self.run_cli("quad", "examples/abstraction-escape-frame.json", "left-start", "right-start",
                                    "--left-route", "left-step", "--right-route", "right-step",
                                    "--projection", "exact", "--retrace")
        self.assertEqual(code, 0)  # The requested selected schema/recovery proposition is supported.
        self.assertEqual(record["similar"], "PASS")
        self.assertEqual(record["congruent"], "FAIL")
        self.assertEqual(record["simulation"], "FAIL")
        self.assertEqual(record["abstracted"], "PASS")
        self.assertEqual(record["left_retrace"]["status"], "PASS")
        self.assertEqual(record["right_retrace"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
