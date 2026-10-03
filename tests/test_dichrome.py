"""Counterexamples for paired continuation, rather than an order registry."""

import unittest
from dataclasses import replace
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import hyperorder as h


class AbsentCapabilityBaseline(unittest.TestCase):
    def test_paired_operations_and_family_convergence_exist(self):
        required = ("Position", "Continuation", "DichromeFrame", "inspect_frame",
                    "follow_path", "filtration", "closure", "converge_families",
                    "describe", "read_description", "verify_description")
        self.assertEqual([name for name in required if not hasattr(h, name)], [])


def position(name, geometry=("incidence",), commitments=("retain-meaning",), outcome="landing"):
    return h.Position(name, frozenset(geometry), frozenset(commitments), outcome)


def move(name, a, b, operation="continue", rationale="preserve both", **kwargs):
    return h.Continuation(name, a, b, operation, rationale, **kwargs)


class PairedTransportTests(unittest.TestCase):
    def test_both_colors_are_required_and_no_numeric_positions(self):
        for args in (("a", frozenset(), frozenset({"meaning"})),
                     ("a", frozenset({"geometry"}), frozenset()),
                     (True, frozenset({"geometry"}), frozenset({"meaning"}))):
            with self.assertRaises(ValueError):
                h.Position(*args)

    def test_exact_structural_transport_refuses_an_undeclared_gain(self):
        frame = h.DichromeFrame((position("a"), position("b", ("incidence", "unearned"))), (move("ab", "a", "b"),))
        report = h.inspect_frame(frame)
        self.assertFalse(report.accepted)
        self.assertEqual([(p.at, p.code) for p in report.obstructions], [("ab", "GEOMETRY_TRANSPORT")])
        with self.assertRaises(ValueError):
            h.follow_path(frame, "a", ("ab",))

    def test_geometry_success_does_not_certify_meaning_transport(self):
        frame = h.DichromeFrame((position("a"), position("b", commitments=("different",))), (move("ab", "a", "b"),))
        self.assertEqual(h.inspect_frame(frame).obstructions[0].code, "MEANING_TRANSPORT")
        self.assertIs(h.filtration(frame, "a", "b").simulation, h.Evidence.CONFLICTED)

    def test_removing_an_absent_premise_fails_even_when_target_is_correct(self):
        frame = h.DichromeFrame((position("a"), position("b")),
                               (move("ab", "a", "b", remove_commitments=frozenset({"never-present"})),))
        self.assertIn("MEANING_PREMISE", [p.code for p in h.inspect_frame(frame).obstructions])

    def test_adding_an_existing_atom_fails_instead_of_disguising_a_noop(self):
        frame = h.DichromeFrame((position("a"), position("b")),
                               (move("ab", "a", "b", add_geometry=frozenset({"incidence"})),))
        self.assertIn("GEOMETRY_FRESHNESS", [p.code for p in h.inspect_frame(frame).obstructions])

    def test_protected_commitments_survive_every_position(self):
        frame = h.DichromeFrame((position("a"),), meaning_invariants=frozenset({"consent"}))
        self.assertEqual(h.inspect_frame(frame).obstructions[0].code, "MEANING_INVARIANT")

    def test_declared_change_propagates_both_colorings(self):
        a = position("a", ("shape",), ("interpretation",))
        b = position("b", ("shape", "reflection"), ("interpretation", "self-read"))
        c = move("reflect", "a", "b", add_geometry=frozenset({"reflection"}), add_commitments=frozenset({"self-read"}))
        self.assertTrue(h.inspect_frame(h.DichromeFrame((a, b), (c,))).accepted)

    def test_bounds_and_duplicate_incidence_are_refused(self):
        with self.assertRaises(ValueError):
            h.DichromeFrame(tuple(position(str(i)) for i in range(65)))
        with self.assertRaises(ValueError):
            h.DichromeFrame((position("a"), position("a")))
        with self.assertRaises(ValueError):
            h.DichromeFrame((position("a"),), (move("escape", "a", "missing"),))
        with self.assertRaises(ValueError):
            move("contradiction", "a", "a", add_geometry=frozenset({"x"}), remove_geometry=frozenset({"x"}))


class ContinuationFiltrationTests(unittest.TestCase):
    def test_same_landing_different_routes_does_not_earn_simulation(self):
        frame, _ = h.example_frame()
        result = h.filtration(frame, "geometry-route", "meaning-route")
        self.assertIs(result.similar, h.Evidence.PASS)
        self.assertIs(result.congruent, h.Evidence.PASS)
        self.assertIs(result.simulation, h.Evidence.FAIL)
        self.assertIsNotNone(result.obstruction)

    def test_identical_geometry_but_different_reasons_obstruct_reproduction(self):
        frame = h.DichromeFrame((position("a"), position("b")),
                               (move("aa", "a", "a", rationale="protect interpretation"),
                                move("bb", "b", "b", rationale="discard interpretation")))
        result = h.filtration(frame, "a", "b")
        self.assertIs(result.congruent, h.Evidence.PASS)
        self.assertIs(result.simulation, h.Evidence.FAIL)
        self.assertEqual(result.obstruction.candidate_replies, ())

    def test_matching_labels_do_not_hide_an_obstructed_successor(self):
        frame = h.DichromeFrame((position("a"), position("b"), position("dead")),
                               (move("aa", "a", "a"), move("bd", "b", "dead")))
        result = h.filtration(frame, "a", "b")
        self.assertIs(result.simulation, h.Evidence.FAIL)
        self.assertGreater(result.obstruction.refinement, 1)
        self.assertEqual(result.obstruction.candidate_replies, ("bd",))

    def test_productive_mutual_return_is_supported_without_erasing_path(self):
        frame, _ = h.example_frame()
        self.assertIs(h.filtration(frame, "paired-form", "paired-self-read").simulation, h.Evidence.PASS)
        result = h.closure(frame, "paired-form", ("self-read", "self-return"))
        self.assertIs(result.status, h.Evidence.PASS)
        self.assertEqual(result.route.positions, ("paired-form", "paired-self-read", "paired-form"))
        self.assertEqual(result.route.continuations, ("self-read", "self-return"))

    def test_empty_route_is_not_closure(self):
        frame, _ = h.example_frame()
        self.assertIs(h.closure(frame, "paired-form", ()).status, h.Evidence.FAIL)

    def test_empty_landing_sets_do_not_vacuously_pass_filtration(self):
        frame = h.DichromeFrame((position("a", outcome=None),), (move("aa", "a", "a"),))
        report = h.filtration(frame, "a", "a")
        self.assertIs(report.similar, h.Evidence.FAIL)
        self.assertIs(report.congruent, h.Evidence.FAIL)
        self.assertIs(report.simulation, h.Evidence.FAIL)

    def test_partial_model_witnesses_overlap_but_not_complete_reproduction(self):
        frame, _ = h.example_frame(incomplete=True)
        result = h.filtration(frame, "paired-form", "paired-self-read")
        self.assertIs(result.similar, h.Evidence.PASS)
        self.assertIs(result.congruent, h.Evidence.UNKNOWN)
        self.assertIs(result.simulation, h.Evidence.UNKNOWN)

    def test_composition_retains_every_incidence_and_is_associative(self):
        frame, _ = h.example_frame()
        a = h.follow_path(frame, "paired-form", ("self-read",))
        b = h.follow_path(frame, "paired-self-read", ("self-return",))
        c = h.follow_path(frame, "paired-form", ("self-read",))
        self.assertEqual(h.compose_paths(h.compose_paths(a, b), c), h.compose_paths(a, h.compose_paths(b, c)))
        self.assertEqual(h.compose_paths(a, b), h.follow_path(frame, "paired-form", ("self-read", "self-return")))
        with self.assertRaises(ValueError):
            h.compose_paths(a, a)
        with self.assertRaises(ValueError):
            h.follow_path(frame, "paired-form", ("self-return",))

    def test_path_witness_refuses_truncated_or_unpaired_incidence(self):
        for positions, continuations, labels in (((), (), ()), (("a", "b"), (), ()),
                                                (("a", "b"), ("ab",), (("operation-only",),))):
            with self.assertRaises(ValueError):
                h.PathWitness(positions, continuations, labels)

    def test_same_observations_with_an_extra_duplicate_branch_do_not_erase_or_invent_paths(self):
        original = h.DichromeFrame((position("a"), position("b")), (move("aa", "a", "a"), move("bb", "b", "b")))
        duplicate = replace(original, continuations=original.continuations + (move("bb-again", "b", "b"),))
        self.assertIs(h.filtration(duplicate, "a", "b").simulation, h.Evidence.PASS)

    def test_nonempty_overlap_is_not_transitive(self):
        positions = (position("a", outcome=None), position("b", outcome=None), position("c", outcome=None),
                     position("x", outcome="x"), position("y", outcome="y"))
        frame = h.DichromeFrame(positions, (move("ax", "a", "x"), move("bx", "b", "x"),
                                           move("by", "b", "y"), move("cy", "c", "y")))
        self.assertIs(h.filtration(frame, "a", "b").similar, h.Evidence.PASS)
        self.assertIs(h.filtration(frame, "b", "c").similar, h.Evidence.PASS)
        self.assertIs(h.filtration(frame, "a", "c").similar, h.Evidence.FAIL)

    def test_greatest_fixed_point_matches_independent_exhaustive_relation_oracle(self):
        # Enumerate every possible relation, not another refinement algorithm.
        pairs = tuple(itertools.product(("a", "b"), repeat=2))
        for mask in range(16):
            edges = {pairs[i] for i in range(4) if mask & (1 << i)}
            frame = h.DichromeFrame((position("a"), position("b")),
                                   tuple(move(f"{a}-{b}", a, b) for a, b in sorted(edges)))
            largest = set()
            for relation_mask in range(16):
                relation = {pairs[i] for i in range(4) if relation_mask & (1 << i)}
                valid = all(
                    all(any((target, reply) in relation for source2, reply in edges if source2 == b)
                        for source, target in edges if source == a)
                    and all(any((reply, target) in relation for source2, reply in edges if source2 == a)
                            for source, target in edges if source == b)
                    for a, b in relation)
                if valid:
                    largest |= relation
            for a, b in pairs:
                result = h.filtration(frame, a, b)
                self.assertEqual(result.simulation is h.Evidence.PASS, (a, b) in largest, (mask, a, b))
                if result.simulation is h.Evidence.PASS:
                    self.assertIs(result.congruent, h.Evidence.PASS)
                    self.assertIs(result.similar, h.Evidence.PASS)


class DivergenceFamilyTests(unittest.TestCase):
    def test_distinct_divergence_families_converge_to_a_stable_reproducing_class(self):
        frame, families = h.example_frame()
        result = h.converge_families(frame, families, "paired-form")
        self.assertIs(result.status, h.Evidence.PASS)
        self.assertTrue(result.distinct_divergence_families)
        self.assertTrue(all(diverges for _, diverges in result.family_divergence))
        self.assertEqual(result.settled_class, frozenset({"paired-form", "paired-self-read"}))
        self.assertEqual(result.basin, frozenset(p.name for p in frame.positions))

    def test_one_possible_merge_does_not_certify_all_branches(self):
        frame, families = h.example_frame(escape=True)
        result = h.converge_families(frame, families, "paired-form")
        self.assertIs(result.status, h.Evidence.FAIL)
        self.assertIn(("base-divergence", "geometry-route"), result.obstructed_members)
        self.assertNotIn("unresolved-escape", result.basin)

    def test_a_nonclosing_cycle_obstructs_inevitability_without_fairness_assumptions(self):
        frame, families = h.example_frame()
        frame = replace(frame, continuations=frame.continuations + (move("stall", "geometry-route", "geometry-route"),))
        result = h.converge_families(frame, families, "paired-form")
        self.assertIs(result.status, h.Evidence.FAIL)
        self.assertNotIn("geometry-route", result.basin)

    def test_a_reachable_outside_branch_obstructs_stability(self):
        frame, families = h.example_frame()
        a, b = frame.positions[-2], frame.positions[0]
        escape = move("reopen", a.name, b.name, add_geometry=b.geometry-a.geometry, remove_geometry=a.geometry-b.geometry,
                      add_commitments=b.commitments-a.commitments, remove_commitments=a.commitments-b.commitments)
        result = h.converge_families(replace(frame, continuations=frame.continuations + (escape,)), families, a.name)
        self.assertFalse(result.stable)
        self.assertIs(result.status, h.Evidence.FAIL)

    def test_a_dead_landing_is_termination_not_a_recurrent_settled_class(self):
        frame, families = h.example_frame()
        frame = replace(frame, continuations=tuple(c for c in frame.continuations if c.name not in {"self-read", "self-return"}))
        result = h.converge_families(frame, families, "paired-form")
        self.assertFalse(result.stable)
        self.assertIs(result.status, h.Evidence.FAIL)

    def test_identical_family_profiles_are_not_divergence_of_divergences(self):
        frame, families = h.example_frame()
        same = (families[0], h.DivergenceFamily("copy", families[0].members))
        result = h.converge_families(frame, same, "paired-form")
        self.assertFalse(result.distinct_divergence_families)
        self.assertIs(result.status, h.Evidence.FAIL)

    def test_single_paths_are_not_divergence_families(self):
        frame, _ = h.example_frame()
        families = (h.DivergenceFamily("one", frozenset({"geometry-route"})),
                    h.DivergenceFamily("two", frozenset({"meaning-route"})))
        result = h.converge_families(frame, families, "paired-form")
        self.assertTrue(all(not diverges for _, diverges in result.family_divergence))
        self.assertIs(result.status, h.Evidence.FAIL)

    def test_incomplete_continuation_declarations_stay_unknown(self):
        frame, families = h.example_frame(incomplete=True)
        self.assertIs(h.converge_families(frame, families, "paired-form").status, h.Evidence.UNKNOWN)

    def test_renaming_positions_and_reversing_declaration_order_preserve_results(self):
        frame, families = h.example_frame()
        names = {p.name: f"r-{p.name}" for p in frame.positions}
        changed = replace(frame, positions=tuple(replace(p, name=names[p.name]) for p in reversed(frame.positions)),
                          continuations=tuple(replace(c, source=names[c.source], target=names[c.target])
                                              for c in reversed(frame.continuations)))
        changed_families = tuple(replace(f, members=frozenset(names[p] for p in f.members)) for f in families)
        report = h.converge_families(changed, changed_families, names["paired-form"])
        self.assertIs(report.status, h.Evidence.PASS)
        self.assertEqual(report.basin, frozenset(names.values()))
        for a, b in itertools.product(names, repeat=2):
            before, after = h.filtration(frame, a, b), h.filtration(changed, names[a], names[b])
            self.assertEqual((before.similar, before.congruent, before.simulation),
                             (after.similar, after.congruent, after.simulation))


class SelfDescriptionTests(unittest.TestCase):
    def test_recovery_retains_rules_incidence_both_colors_and_obligations(self):
        frame, _ = h.example_frame()
        record = h.describe(frame)
        recovered = h.read_description(json.loads(h.to_json(record)))
        self.assertEqual(recovered, frame)
        self.assertIs(h.verify_description(frame, record), h.Evidence.PASS)
        self.assertEqual(h.to_json(h.describe(recovered)), h.to_json(record))

    def test_same_landing_does_not_authenticate_a_tampered_rule(self):
        frame, _ = h.example_frame()
        record = h.describe(frame)
        record["continuations"][0]["rationale"] = "a different interpretation"
        self.assertTrue(h.inspect_frame(h.read_description(record)).accepted)
        self.assertIs(h.verify_description(frame, record), h.Evidence.FAIL)

    def test_omitted_incidence_or_invariant_is_detected(self):
        frame, _ = h.example_frame()
        for field in ("continuations", "meaning_invariants"):
            record = h.describe(frame)
            record[field].pop()
            self.assertIs(h.verify_description(frame, record), h.Evidence.FAIL)

    def test_missing_duplicate_and_additional_fields_are_refused(self):
        frame, _ = h.example_frame()
        for mutate in (lambda r: r.pop("classification"),
                       lambda r: r.update({"native_closure": True}),
                       lambda r: r["positions"][0]["geometry"].append(r["positions"][0]["geometry"][0]),
                       lambda r: r.update({"classification": "FORM"})):
            record = h.describe(frame)
            mutate(record)
            with self.assertRaises(ValueError):
                h.read_description(record)

    def test_rule_transport_is_rechecked_during_description_recovery(self):
        frame, _ = h.example_frame()
        record = h.describe(frame)
        record["continuations"][0]["add_commitments"] = []
        with self.assertRaises(ValueError):
            h.read_description(record)
        self.assertIs(h.verify_description(frame, record), h.Evidence.FAIL)


class CommandTests(unittest.TestCase):
    def run_command(self, *args):
        root = Path(h.__file__).resolve().parent
        result = subprocess.run([sys.executable, "-B", "-u", str(root / "hyperorder.py"), *args],
                                cwd=root, text=True, encoding="utf-8", capture_output=True, timeout=5)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def test_demo_is_executable_and_distinguishes_supported_obstructed_and_unknown(self):
        for args, code, status in (((), 0, "PASS"), (("--escape",), 1, "FAIL"), (("--incomplete",), 1, "UNKNOWN")):
            returned, report = self.run_command("demo", *args)
            self.assertEqual(returned, code)
            self.assertEqual(report["family_convergence"]["status"], status)
            self.assertEqual(report["native_adequacy"], "OPEN")

    def test_description_compare_trace_and_family_commands_work_on_retained_inputs(self):
        frame, families = h.example_frame()
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "frame.json"
            record.write_text(h.to_json(h.describe(frame)), encoding="utf-8")
            members = Path(directory) / "families.json"
            members.write_text(h.to_json({"families": families}), encoding="utf-8")
            self.assertEqual(self.run_command("inspect", str(record))[0], 0)
            self.assertEqual(self.run_command("describe", str(record))[1], h.describe(frame))
            self.assertEqual(self.run_command("compare", str(record), "paired-form", "paired-self-read")[0], 0)
            self.assertEqual(self.run_command("trace", str(record), "paired-form", "self-read", "self-return")[0], 0)
            self.assertEqual(self.run_command("converge", str(record), str(members), "paired-form")[0], 0)
            self.assertEqual(self.run_command("verify-description", str(record), str(record)), (0, "PASS"))

    def test_cli_rejects_duplicate_json_fields_and_returns_named_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            record = Path(directory) / "bad.json"
            record.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")
            code, report = self.run_command("inspect", str(record))
            self.assertEqual(code, 2)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("duplicate", report["error"])


if __name__ == "__main__":
    unittest.main()
