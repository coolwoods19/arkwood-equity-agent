import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "api"))

from services.chokepoint_reader import (  # noqa: E402
    build_chokepoint_overlay,
    derive_durability_class,
    derive_entry_quality,
    derive_sizing_bias,
)


class ChokepointClassificationTests(unittest.TestCase):
    def test_durability_bands(self):
        self.assertEqual(
            derive_durability_class(45),
            "Tier 1 Monopoly / Essential Chokepoint",
        )
        self.assertEqual(
            derive_durability_class(38),
            "Tier 1/Tier 2 Structural Bottleneck",
        )
        self.assertEqual(
            derive_durability_class(30),
            "Tier 2 AI Infrastructure Winner",
        )
        self.assertEqual(derive_durability_class(22), "High-Beta AI Beneficiary")
        self.assertEqual(derive_durability_class(21), "Weak Chokepoint")

    def test_entry_quality_bands(self):
        self.assertEqual(derive_entry_quality(24), "Attractive / resilient entry")
        self.assertEqual(derive_entry_quality(18), "Acceptable, selective entry")
        self.assertEqual(derive_entry_quality(12), "Risky or valuation-constrained")
        self.assertEqual(derive_entry_quality(11), "Poor entry quality")

    def test_sizing_bias_keeps_tier_one_even_when_entry_is_poor(self):
        self.assertEqual(
            derive_sizing_bias(50, 17),
            "Core watch / add on dislocation",
        )

    def test_sizing_bias_downsizes_poor_entry_quality(self):
        self.assertEqual(derive_sizing_bias(35, 8), "Satellite / tactical only")


class ChokepointOverlayTests(unittest.TestCase):
    def test_build_overlay_keeps_two_axes_separate(self):
        overlay = build_chokepoint_overlay(
            {
                "ticker": "ASML",
                "ai_role": "EUV lithography",
                "scores": {
                    "durability": {
                        "necessity": 10,
                        "structural_scarcity": 10,
                        "pricing_power": 10,
                        "supply_substitution_defense": 10,
                        "inference_resilience": 10,
                    },
                    "entry_risk": {
                        "capex_shock_resilience": 9,
                        "valuation_crowdedness": 3,
                        "concentration_idiosyncratic_risk": 5,
                    },
                },
            }
        )
        self.assertEqual(overlay["durability"]["score"], 50)
        self.assertEqual(overlay["entry_risk"]["score"], 17)
        self.assertEqual(
            overlay["durability"]["classification"],
            "Tier 1 Monopoly / Essential Chokepoint",
        )
        self.assertEqual(
            overlay["entry_risk"]["classification"],
            "Risky or valuation-constrained",
        )
        self.assertEqual(overlay["sizing_bias"], "Core watch / add on dislocation")

    def test_invalid_scores_are_rejected(self):
        with self.assertRaises(ValueError):
            build_chokepoint_overlay(
                {
                    "ticker": "BAD",
                    "scores": {
                        "durability": {"necessity": 11},
                        "entry_risk": {},
                    },
                }
            )


if __name__ == "__main__":
    unittest.main()
