"""Independent finite counterexamples for the proposed Hyperorder frame."""

import unittest

import hyperorder
from hyperorder import (REALIGNMENT, SENSES, Incomparable, Order, Precedes,
                        Verdict, compare, resolve_sense)


class SenseTests(unittest.TestCase):
    def test_hyperorder_resolves_to_its_one_declared_sense(self):
        sense = resolve_sense("hyperorder")
        self.assertEqual(sense.name, "dichrome-closure")
        self.assertIn("21_hypertopologies.md", sense.source)

    def test_every_sense_names_its_source(self):
        for sense in SENSES:
            self.assertTrue(sense.gloss and sense.source, sense.name)

    def test_order_is_not_silently_hyperorder(self):
        with self.assertRaises(KeyError):
            resolve_sense("order")
        with self.assertRaises(KeyError):
            resolve_sense("Hyperorder")

    def test_the_realignment_is_recorded_open_and_names_order_not_a_sense(self):
        self.assertEqual(REALIGNMENT.status, "OPEN")
        self.assertIn("order", REALIGNMENT.relates)
        self.assertNotIn("dichrome-closure", REALIGNMENT.relates)

    def test_no_grounding_rank_or_clock_is_exported(self):
        for forbidden in ("ground", "grounds", "grounded_in", "rank", "degree",
                          "time", "clock", "index", "duration", "step"):
            self.assertFalse(hasattr(hyperorder, forbidden), forbidden)


def chain():
    return Order(("a", "b", "c", "d"), (Precedes("a", "b"), Precedes("b", "c")))


class OrdinalTests(unittest.TestCase):
    def test_declared_precedence_is_transitive_and_read_both_ways(self):
        o = chain()
        self.assertIs(compare(o, "a", "c"), Verdict.PRECEDES)
        self.assertIs(compare(o, "c", "a"), Verdict.FOLLOWS)

    def test_a_missing_relation_is_unknown_not_incomparable(self):
        self.assertIs(compare(chain(), "a", "d"), Verdict.UNKNOWN)

    def test_follows_is_not_the_same_as_not_precedes(self):
        o = chain()
        self.assertIsNot(compare(o, "d", "a"), Verdict.PRECEDES)
        self.assertIsNot(compare(o, "d", "a"), Verdict.FOLLOWS)

    def test_incomparability_must_be_declared(self):
        o = Order(("a", "b"), incomparable=(Incomparable("a", "b"),))
        self.assertIs(compare(o, "a", "b"), Verdict.INCOMPARABLE)
        self.assertIs(compare(o, "b", "a"), Verdict.INCOMPARABLE)

    def test_a_cycle_is_conflicted_not_equal(self):
        o = Order(("a", "b", "c"), (Precedes("a", "b"), Precedes("b", "c"), Precedes("c", "a")))
        self.assertIs(compare(o, "a", "c"), Verdict.CONFLICTED)

    def test_declared_incomparable_against_a_path_is_conflicted(self):
        o = Order(("a", "b", "c"), (Precedes("a", "b"), Precedes("b", "c")),
                  (Incomparable("c", "a"),))
        self.assertIs(compare(o, "a", "c"), Verdict.CONFLICTED)

    def test_positions_are_names_never_numbers(self):
        for bad in ((1, 2), (True,), ("a", 2.0), ("",)):
            with self.assertRaises(ValueError, msg=repr(bad)):
                Order(bad)

    def test_malformed_declarations_are_refused(self):
        with self.assertRaises(ValueError):
            Order(("a", "a"))
        with self.assertRaises(ValueError):
            Order(("a",), (Precedes("a", "a"),))
        with self.assertRaises(ValueError):
            Order(("a",), (Precedes("a", "z"),))
        with self.assertRaises(ValueError):
            Order(("a", "b"), incomparable=(Incomparable("a", "a"),))

    def test_totality_is_a_checked_declaration(self):
        with self.assertRaises(ValueError):
            Order(("a", "b", "c"), (Precedes("a", "b"),), total=True)
        with self.assertRaises(ValueError):
            Order(("a", "b"), incomparable=(Incomparable("a", "b"),), total=True)
        o = Order(("a", "b", "c"), (Precedes("a", "b"), Precedes("b", "c")), total=True)
        for x in o.elements:
            for y in o.elements:
                if x != y:
                    self.assertIsNot(compare(o, x, y), Verdict.UNKNOWN)

    def test_an_element_is_not_compared_with_itself(self):
        with self.assertRaises(ValueError):
            compare(chain(), "a", "a")
        with self.assertRaises(KeyError):
            compare(chain(), "a", "z")

    def test_the_frame_is_finite(self):
        with self.assertRaises(ValueError):
            Order(tuple(f"e{i}" for i in range(65)))


if __name__ == "__main__":
    unittest.main()
