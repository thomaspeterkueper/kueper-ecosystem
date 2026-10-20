#!/usr/bin/env python3
"""SCION readiness pilot: deterministic knowledge identity/provenance gates.

Offline checks: do not connect to repositories or mutate canonical content.
Future adapters supply observations with the same schema.
"""
from dataclasses import dataclass
import unittest

@dataclass(frozen=True)
class Observation:
    subject: str
    kind: str
    source: str
    observed_at: str
    value: str
    qualifier: str = ""

def reconcile(observations):
    groups = {}
    for item in observations:
        groups.setdefault((item.kind, item.subject), []).append(item)
    return groups

def current_value(observations, subject):
    candidates = [x for x in observations if x.subject == subject and x.qualifier == "current"]
    if len({x.value for x in candidates}) > 1:
        raise ValueError("conflicting current measurements; curator review required")
    return candidates[0].value if candidates else None

class KnowledgeHandoffPilot(unittest.TestCase):
    def test_gold_distinguishes_experiments_from_material(self):
        docs = [
            Observation("Au", "chemical_element", "KUE-SCI-0195", "2026-10-17", "atomic number 79"),
            Observation("Au+Au STAR", "heavy_ion_experiment", "OTA-SCI-0107", "2026-10-17", "QCD correlations"),
            Observation("b->s mu mu", "flavour_experiment", "OTA-SCI-0105", "2026-10-17", "CMS/LHCb"),
        ]
        groups = reconcile(docs)
        self.assertEqual(len(groups), 3)
        self.assertNotEqual(("heavy_ion_experiment", "Au+Au STAR"), ("flavour_experiment", "b->s mu mu"))

    def test_gw250114_publications_do_not_multiply_events(self):
        docs = [
            Observation("GW250114", "astronomical_event", "PRL-area-law-2025", "2025-09-10", "area law"),
            Observation("GW250114", "astronomical_event", "PRL-ringdown-2026", "2026-01-29", "Kerr modes"),
            Observation("GW250114", "astronomical_event", "OTA-SCI-0113", "2026-10-19", "evidence synthesis"),
        ]
        self.assertEqual(len(reconcile(docs)), 1)
        self.assertEqual(len(reconcile(docs)[("astronomical_event", "GW250114")]), 3)

    def test_andromeda_preserves_historical_distance(self):
        distances = [
            Observation("M31 distance", "measurement", "Hubble historical estimate", "1925", "285 kpc", "historical"),
            Observation("M31 distance", "measurement", "modern calibration approximate", "2026", "780 kpc", "current"),
        ]
        self.assertEqual(current_value(distances, "M31 distance"), "780 kpc")
        self.assertNotEqual(distances[0].value, current_value(distances, "M31 distance"))

    def test_conflicting_current_values_require_review(self):
        measurements = [
            Observation("M31 distance", "measurement", "source A", "2026", "780 kpc", "current"),
            Observation("M31 distance", "measurement", "source B", "2026", "700 kpc", "current"),
        ]
        with self.assertRaises(ValueError):
            current_value(measurements, "M31 distance")

if __name__ == "__main__":
    unittest.main()
