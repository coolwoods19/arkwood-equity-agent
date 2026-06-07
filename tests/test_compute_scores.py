import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from compute_scores import (  # noqa: E402
    compute_technical_overlay,
    compute_v2_signal,
    score_peg,
    score_ticker,
)


class ScorePegTests(unittest.TestCase):
    def test_peg_bands(self):
        self.assertEqual(score_peg(None)[0], 0)
        self.assertEqual(score_peg(0.8)[0], 10)
        self.assertEqual(score_peg(1.5)[0], 0)
        self.assertEqual(score_peg(2.3)[0], -10)
        self.assertEqual(score_peg(3.0)[0], -20)


class TechnicalOverlayTests(unittest.TestCase):
    def test_strong_setup_when_three_bullish_no_bearish(self):
        overlay = compute_technical_overlay(
            {
                "trend_signal": "UPTREND",
                "momentum_signal": "BULLISH",
                "breakout_signal": "BREAKING_OUT",
                "rs_signal": "IN_LINE",
            }
        )
        self.assertEqual(overlay["overlay_rating"], "STRONG_SETUP")

    def test_extended_takes_priority(self):
        overlay = compute_technical_overlay(
            {
                "trend_signal": "UPTREND",
                "momentum_signal": "OVERBOUGHT",
                "breakout_signal": "BREAKING_OUT",
                "rs_signal": "LEADING",
            }
        )
        self.assertEqual(overlay["overlay_rating"], "EXTENDED")

    def test_avoid_when_two_bearish(self):
        overlay = compute_technical_overlay(
            {
                "trend_signal": "DOWNTREND",
                "momentum_signal": "NEUTRAL",
                "breakout_signal": "RANGE",
                "rs_signal": "LAGGING",
            }
        )
        self.assertEqual(overlay["overlay_rating"], "AVOID")


class V2SignalTests(unittest.TestCase):
    def test_compounder_first_avoid_warns(self):
        signal = compute_v2_signal("COMPOUNDER", "AVOID", "RISK_ON", None)
        self.assertEqual(signal["v2_action"], "WATCH_EXIT")
        self.assertFalse(signal["exit_triggered"])

    def test_compounder_second_avoid_sells(self):
        signal = compute_v2_signal("COMPOUNDER", "AVOID", "RISK_ON", "AVOID")
        self.assertEqual(signal["v2_action"], "SELL")
        self.assertTrue(signal["exit_triggered"])

    def test_high_vol_requires_persistence_to_add(self):
        first_signal = compute_v2_signal("HIGH_VOL", "SETUP", "RISK_ON", None)
        second_signal = compute_v2_signal("HIGH_VOL", "SETUP", "RISK_ON", "SETUP")
        self.assertEqual(first_signal["v2_action"], "WAIT")
        self.assertEqual(second_signal["v2_action"], "ADD")

    def test_risk_off_blocks_entry(self):
        signal = compute_v2_signal("COMPOUNDER", "STRONG_SETUP", "RISK_OFF", None)
        self.assertEqual(signal["v2_action"], "RISK_OFF_HOLD")
        self.assertFalse(signal["entry_allowed"])


class ScoreTickerTests(unittest.TestCase):
    def test_full_tvs_is_pending_until_manual_scores_exist(self):
        score = score_ticker(
            {
                "fundamentals": {},
                "ark": {},
                "news": {},
                "technicals": {"trend_signal": "FLAT"},
            }
        )
        self.assertEqual(score["score_status"], "AUTO_ONLY")
        self.assertIsNone(score["manual_total"])
        self.assertIsNone(score["tvs_total"])


if __name__ == "__main__":
    unittest.main()
