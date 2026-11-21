import unittest
import importlib.util
from pathlib import Path

path = Path(__file__).with_name("candidate3_temporal_economic_audit.py")
spec = importlib.util.spec_from_file_location("candidate3_temporal_economic_audit", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(day, ident, saving, *, new_exact=False, new_family=False):
    return dict(day=day, occurrence_key=ident, saving_ms=saving,
                baseline_ms=20.0, alternative_ms=20.0-saving,
                new_exact=new_exact, new_family=new_family)


class TemporalEconomicAudit(unittest.TestCase):
    def setUp(self):
        self.days = ["2014-09-21", "2014-09-22", "2014-09-23"]
        self.counts = {self.days[0]: 3, self.days[1]: 1, self.days[2]: 0}
        self.samples = [row(self.days[0], key, 1.0, new_exact=True)
                        for key in ("a", "b", "c") for _ in range(2)]
        self.samples.extend([row(self.days[1], "d", 2.0, new_family=True)
                             for _ in range(2)])

    def calculate(self, records=None, **kw):
        return module.audit(self.samples if records is None else records,
                            self.counts, self.days,
                            migration_ms=kw.pop("migration_ms", 1.0),
                            semantics_pass=kw.pop("semantics_pass", True),
                            repeats=2, **kw)

    def test_exact_point_and_coverage(self):
        result = self.calculate()
        self.assertEqual(result["status"], "VALID_EXPLORATORY_ACCOUNTING")
        self.assertEqual(result["projected_unexecuted_net_ms"], 4.0)
        self.assertEqual(result["eligible_occurrences"], 4)
        self.assertEqual(result["sampled_independent_occurrences"], 4)
        self.assertEqual(result["paired_repetitions"], 8)
        self.assertEqual(result["novelty_slices"]["new_exact"]["sampled_occurrences"], 3)
        self.assertEqual(result["novelty_slices"]["new_family"]["sampled_occurrences"], 1)
        self.assertFalse(result["journal_GO"])

    def test_shuffled_occurrences_dont_change_point(self):
        x = list(reversed(self.samples))
        self.assertEqual(self.calculate(x)["projected_unexecuted_net_ms"], 4.0)

    def test_fails_closed_wrong_semantics(self):
        self.assertEqual(self.calculate(semantics_pass=False)["status"], "INVALID_SPARQL")

    def test_fails_closed_missing_repeat(self):
        self.assertEqual(self.calculate(self.samples[:-1])["status"],
                         "MISSING_OR_EXCESS_REPEATS")

    def test_fails_closed_missing_sample(self):
        reduced = [r for r in self.samples if r["occurrence_key"] != "a"]
        self.assertEqual(self.calculate(reduced)["status"], "SAMPLE_COVERAGE_MISMATCH")

    def test_fails_closed_unmatched_runtime(self):
        bad = [dict(x) for x in self.samples]
        bad[0]["saving_ms"] = 12.0
        self.assertEqual(self.calculate(bad)["status"], "UNMATCHED_PAIR")

    def test_fails_closed_nonfinite(self):
        bad = [dict(x) for x in self.samples]
        bad[0]["saving_ms"] = float("nan")
        self.assertEqual(self.calculate(bad)["status"], "INVALID_WALLCLOCK")

    def test_fails_closed_missing_novelty(self):
        bad = [dict(x) for x in self.samples]
        del bad[0]["new_exact"]
        self.assertEqual(self.calculate(bad)["status"], "MISSING_NOVELTY_LABEL")

    def test_fails_closed_invalid_cost(self):
        self.assertEqual(self.calculate(migration_ms=-1)["status"],
                         "INVALID_MIGRATION_COST")

    def test_unequal_day_volume_weighting(self):
        counts = {"a": 200, "b": 1}
        days = ["a", "b"]
        records = [row("a", str(i), 1) for i in range(12) for _ in range(2)]
        records += [row("b", "x", -10) for _ in range(2)]
        result = module.audit(records, counts, days,
                              migration_ms=0, semantics_pass=True)
        self.assertEqual(result["projected_unexecuted_net_ms"], 190)

    def test_repeated_query_text_occurrences_are_distinct(self):
        count = {"d": 2}
        rec = [row("d", key, 3) for key in ("x", "y") for _ in range(2)]
        result = module.audit(rec, count, ["d"],
                              migration_ms=1, semantics_pass=True)
        self.assertEqual(result["sampled_independent_occurrences"], 2)
        self.assertEqual(result["projected_unexecuted_net_ms"], 5)

if __name__ == "__main__":
    unittest.main()
