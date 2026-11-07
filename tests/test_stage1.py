"""
Tests for Stage 1 using a tiny MADE-UP match (no internet needed).
Run from the project folder with:   python -m unittest discover -s tests -v
These tests prove the logic is right on toy data. They do NOT replace the real
run on the real Euro 2024 data - that is what the checkpoint report is for.
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src import clean, stage1

NAN = np.nan


def toy_raw():
    """One made-up match, Home vs Away, ending 1-1.
    Columns match the names used by statsbombpy."""
    rows = [
        # index, period, type, team, player, location, pass_outcome, pass_end, drib_outcome, carry_end, shot_outcome
        (1, 1, "Half Start", "Home", NAN, NAN, NAN, NAN, NAN, NAN, NAN),                     # dropped (not kept type)
        (2, 1, "Pass", "Home", "A", [20, 40], NAN, [35, 40], NAN, NAN, NAN),                 # complete (outcome blank)
        (3, 1, "Ball Receipt*", "Home", "B", [35, 40], NAN, NAN, NAN, NAN, NAN),
        (4, 1, "Carry", "Home", "B", [35, 40], NAN, NAN, NAN, [50, 40], NAN),                # followed by Dispossessed -> fails
        (5, 1, "Dispossessed", "Home", "B", [50, 40], NAN, NAN, NAN, NAN, NAN),
        (6, 1, "Pass", "Away", "C", [70, 40], "Incomplete", [80, 50], NAN, NAN, NAN),        # failed pass
        (7, 1, "Dribble", "Home", "D", [90, 30], NAN, NAN, "Complete", NAN, NAN),
        (8, 1, "Carry", "Home", "D", [91, 30], NAN, NAN, NAN, [100, 35], NAN),               # followed by Pressure -> succeeds
        (9, 1, "Pressure", "Away", "E", [100, 35], NAN, NAN, NAN, NAN, NAN),
        (10, 1, "Dribble", "Home", "F", [100, 40], NAN, NAN, "Incomplete", NAN, NAN),
        (11, 2, "Shot", "Home", "D", [105, 40], NAN, NAN, NAN, NAN, "Goal"),                 # Home goal
        (12, 2, "Own Goal For", "Away", NAN, NAN, NAN, NAN, NAN, NAN, NAN),                  # Away benefits -> Away goal
        (13, 5, "Shot", "Home", "D", [108, 40], NAN, NAN, NAN, NAN, "Goal"),                 # shoot-out goal: must be ignored
    ]
    cols = ["index", "period", "type", "team", "player", "location", "pass_outcome",
            "pass_end_location", "dribble_outcome", "carry_end_location", "shot_outcome"]
    df = pd.DataFrame(rows, columns=cols)
    df["match_id"] = 1
    return df


def toy_matches(home_score=1, away_score=1):
    return pd.DataFrame([{"match_id": 1, "home_team": "Home", "away_team": "Away",
                          "home_score": home_score, "away_score": away_score}])


class TestCleaning(unittest.TestCase):
    def setUp(self):
        self.raw = toy_raw()
        self.np_raw = clean.drop_shootout(self.raw)
        self.ev = clean.clean_events(self.np_raw)

    def test_shootout_dropped(self):
        self.assertTrue((self.np_raw["period"] != 5).all())
        self.assertEqual(len(self.np_raw), len(self.raw) - 1)

    def test_unwanted_types_dropped(self):
        self.assertNotIn("Half Start", set(self.ev["type"]))
        self.assertNotIn("Own Goal For", set(self.ev["type"]))

    def test_sorted_by_match_and_index(self):
        self.assertTrue(self.ev["index"].is_monotonic_increasing)

    def test_pass_success_trap1(self):
        passes = self.ev[self.ev["type"] == "Pass"].set_index("player")["success"]
        self.assertEqual(passes["A"], 1.0)   # blank outcome = complete
        self.assertEqual(passes["C"], 0.0)   # "Incomplete" = failed

    def test_dribble_success_trap2(self):
        d = self.ev[self.ev["type"] == "Dribble"].set_index("player")["success"]
        self.assertEqual(d["D"], 1.0)
        self.assertEqual(d["F"], 0.0)

    def test_carry_failure_rule(self):
        c = self.ev[self.ev["type"] == "Carry"].set_index("player")["success"]
        self.assertEqual(c["B"], 0.0)        # next event: Dispossessed by same player
        self.assertEqual(c["D"], 1.0)        # next event: Pressure by someone else

    def test_non_actions_have_blank_success(self):
        self.assertTrue(self.ev.loc[self.ev["type"] == "Dispossessed", "success"].isna().all())
        self.assertTrue(self.ev.loc[self.ev["type"] == "Shot", "success"].isna().all())

    def test_coordinates(self):
        first_pass = self.ev[(self.ev["type"] == "Pass") & (self.ev["player"] == "A")].iloc[0]
        self.assertEqual((first_pass["start_x"], first_pass["start_y"]), (20, 40))
        self.assertEqual((first_pass["end_x"], first_pass["end_y"]), (35, 40))
        carry = self.ev[(self.ev["type"] == "Carry") & (self.ev["player"] == "B")].iloc[0]
        self.assertEqual((carry["end_x"], carry["end_y"]), (50, 40))
        dribble = self.ev[(self.ev["type"] == "Dribble") & (self.ev["player"] == "D")].iloc[0]
        self.assertEqual((dribble["end_x"], dribble["end_y"]), (90, 30))   # end = start for dribbles


class TestGoals(unittest.TestCase):
    def test_goals_reconcile(self):
        goals = clean.count_goals(clean.drop_shootout(toy_raw()))
        recon = clean.reconcile_goals(toy_matches(1, 1), goals)
        self.assertTrue(recon["ok"].all())   # shoot-out goal ignored; own goal credited to Away

    def test_mismatch_detected(self):
        goals = clean.count_goals(clean.drop_shootout(toy_raw()))
        recon = clean.reconcile_goals(toy_matches(2, 1), goals)
        self.assertFalse(recon["ok"].any())

    def test_missing_column_stops(self):
        with self.assertRaises(ValueError):
            clean.check_required_columns(toy_raw().drop(columns=["pass_outcome"]))


class TestWholeStage(unittest.TestCase):
    def test_process_runs_and_passes(self):
        ev, rep = stage1.process(toy_raw(), toy_matches(1, 1), expected_matches=1, partial=True)
        text = rep.finish()
        self.assertEqual(rep.n_failed(), 0, text)
        self.assertIn("AUTO-CHECKS", text)

    def test_process_flags_bad_score(self):
        ev, rep = stage1.process(toy_raw(), toy_matches(3, 0), expected_matches=1, partial=True)
        self.assertGreater(rep.n_failed(), 0)


if __name__ == "__main__":
    unittest.main()
