#!/usr/bin/env python3
"""SCION readiness pilot: deterministic knowledge identity/provenance gates.

Offline checks: do not connect to repositories or mutate canonical content.
Future adapters supply observations with the same schema.

Optional: if KG_ROOT points to a local checkout of kueper-knowledge-graph, the
KG-ID test reads its exports (read-only) and checks that the IDs SCION is told
to consume exist in the active KXF registry. Without KG_ROOT it is skipped.
"""
from dataclasses import dataclass
import json
import os
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

def results(observations, subject):
    """Only reported measurement results count as evidence; capabilities and targets do not."""
    return [x for x in observations if x.subject == subject and x.qualifier == "result"]

def kg_active_ids(kg_root):
    with open(os.path.join(kg_root, "exports/kxf-0.6.json"), encoding="utf-8") as f:
        registry = json.load(f)["registry"]
    ids = set()
    for single, plural in (("entityRegistry", "entityRegistryShards"),
                           ("documentReferenceRegistry", "documentReferenceRegistryShards")):
        for path in [registry.get(single), *registry.get(plural, [])]:
            if path:
                with open(os.path.join(kg_root, path), encoding="utf-8") as f:
                    ids.update(r["id"] for r in json.load(f).get("records", []))
    return ids

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
            Observation("M31 distance", "measurement", "Li et al. 2021, HST NIR Cepheids", "2021", "761 kpc", "current"),
        ]
        self.assertEqual(current_value(distances, "M31 distance"), "761 kpc")
        self.assertNotEqual(distances[0].value, current_value(distances, "M31 distance"))

    def test_conflicting_current_values_require_review(self):
        measurements = [
            Observation("M31 distance", "measurement", "source A", "2026", "780 kpc", "current"),
            Observation("M31 distance", "measurement", "source B", "2026", "700 kpc", "current"),
        ]
        with self.assertRaises(ValueError):
            current_value(measurements, "M31 distance")

    def test_positron_capability_is_not_cpt_result(self):
        # KG-REQ-20261022: observation vs. planned precision are asymmetric evidence
        reports = [
            Observation("positron magnetic moment", "experimental_capability", "PRL 137, 173001 (2026)", "2026-10-21",
                        "one-positron quantum cyclotron", "capability"),
            Observation("positron magnetic moment", "precision_target", "KUE-SCI-0197", "2026-11-02",
                        "about 1 part in 10^13", "planned"),
        ]
        self.assertEqual(results(reports, "positron magnetic moment"), [])
        self.assertFalse(any("violation" in x.kind for x in reports))

    @unittest.skipUnless(os.environ.get("KG_ROOT"), "KG_ROOT not set; KG-ID existence check skipped")
    def test_consumed_kg_ids_exist(self):
        ids = kg_active_ids(os.environ["KG_ROOT"])
        for kg_id in ("EVT:L1:gw250114", "PLC:AST:m31", "CON:L1:hawking-flaechensatz", "CON:L1:cpt-symmetrie",
                      "DOC:KUE:KUE-SCI-0196-2026-DE", "DOC:KUE:KUE-SCI-0197-2026-DE", "DOC:KUE:KUE-SCI-0198-2026-DE"):
            self.assertIn(kg_id, ids)
        self.assertEqual([i for i in ids if "gw250114" in i.lower()], ["EVT:L1:gw250114"])

if __name__ == "__main__":
    unittest.main()
