"""
stage1.py - STAGE 1: load and clean. Produces Checkpoint 1.

process() does the thinking and is separate from main() (which does the
downloading) so that process() can be tested on small made-up data.
"""
import json
import platform
import subprocess
import sys
from importlib import metadata

import pandas as pd

import config
from src import clean, ingest
from src.report import Report


def _version(pkg):
    try:
        return metadata.version(pkg)
    except Exception:
        return "not installed"


def process(raw, matches, expected_matches, partial=False):
    """Clean the raw events and build the checkpoint report.
    Returns (clean events table, report)."""
    rep = Report("CHECKPOINT 1 REPORT - The Gambler's Pitch (Stage 1: load and clean)")
    rep.line("Mode: " + ("PARTIAL TEST RUN (not the full tournament)" if partial else "FULL RUN"))

    # ---------- environment (an anti-mismatch step) ----------
    rep.section("Environment")
    rep.line("python " + sys.version.split()[0] + " | " + platform.system())
    for pkg in ("pandas", "numpy", "scikit-learn", "scipy", "matplotlib", "mplsoccer", "statsbombpy"):
        rep.line("%-13s %s" % (pkg, _version(pkg)))

    clean.check_required_columns(raw)

    # ---------- shoot-out removal ----------
    n_raw = len(raw)
    raw_np = clean.drop_shootout(raw)
    n_shootout = n_raw - len(raw_np)
    ev = clean.clean_events(raw_np)

    rep.section("1. Matches and sizes")
    rep.line("matches in table: %d (expected %d)" % (len(matches), expected_matches))
    rep.line("matches with events: %d" % ev["match_id"].nunique())
    teams = set(matches["home_team"]) | set(matches["away_team"])
    rep.line("teams: %d (expected %d for a full run)" % (len(teams), config.EXPECTED_TEAMS))
    rep.line("raw events: %d | shoot-out events dropped: %d | after type filter: %d" % (n_raw, n_shootout, len(ev)))
    rep.line("periods present after cleaning: " + str(sorted(ev["period"].unique().tolist())))
    per_match = ev.groupby("match_id").size()
    rep.line("kept events per match: min %d, mean %.0f, max %d" % (per_match.min(), per_match.mean(), per_match.max()))

    rep.section("2. Rows per event type (kept types)")
    rep.table(ev["type"].value_counts().rename("rows").to_frame())

    # ---------- goals check ----------
    rep.section("3. Goals check (events vs official scores)")
    goals = clean.count_goals(raw_np)
    recon = clean.reconcile_goals(matches, goals)
    bad = recon[~recon["ok"]]
    rep.line("matches where our goal count differs from the official score: %d of %d" % (len(bad), len(recon)))
    if len(bad):
        rep.table(bad)
        og = clean.own_goal_summary(raw_np)
        og = og[og["match_id"].isin(bad["match_id"])]
        rep.line("own-goal events in those matches (to help diagnose):")
        rep.table(og)

    # ---------- success flags ----------
    rep.section("4. Success flags (traps 1 and 2, carry rule)")
    sr = ev.groupby("type")["success"].agg(["mean", "count"]).dropna()
    sr = sr.rename(columns={"mean": "success_rate", "count": "n_actions"})
    sr["success_rate"] = sr["success_rate"].round(3)
    rep.table(sr)
    rep.line("pass_outcome values (blank/NaN = complete): " + str(raw["pass_outcome"].value_counts(dropna=False).to_dict()))
    rep.line("dribble_outcome values: " + str(raw["dribble_outcome"].value_counts(dropna=False).to_dict()))

    # ---------- coordinates ----------
    rep.section("5. Coordinates")
    located = ev[ev["type"].isin(config.LOCATED_TYPES)]
    missing_xy = int(located["start_x"].isna().sum())
    rep.line("Pass/Carry/Dribble/Shot rows with no start location: %d" % missing_xy)
    rep.line("start_x range: %.1f to %.1f (pitch is 0 to 120)" % (ev["start_x"].min(), ev["start_x"].max()))
    rep.line("start_y range: %.1f to %.1f (pitch is 0 to 80)" % (ev["start_y"].min(), ev["start_y"].max()))

    # ---------- columns ----------
    rep.section("6. Columns the spec lists as useful")
    absent = [c for c in clean.SPEC_USEFUL_COLUMNS if c not in raw.columns]
    rep.line("missing from the data: " + (str(absent) if absent else "none"))

    # ---------- automatic checks ----------
    rep.check("expected number of matches in table", "PASS" if len(matches) == expected_matches else "FAIL",
              "%d vs %d" % (len(matches), expected_matches))
    rep.check("every match has events", "PASS" if ev["match_id"].nunique() == len(matches) else "FAIL")
    if not partial:
        rep.check("24 teams", "PASS" if len(teams) == config.EXPECTED_TEAMS else "FAIL", str(len(teams)))
    rep.check("no shoot-out (period 5) left", "PASS" if (ev["period"] != config.SHOOTOUT_PERIOD).all() else "FAIL")
    rep.check("goals match official scores in every match", "PASS" if len(bad) == 0 else "FAIL",
              "%d mismatching matches" % len(bad))
    rep.check("all located actions have a start location", "PASS" if missing_xy == 0 else "FAIL",
              "%d missing" % missing_xy)
    rep.check("coordinates inside the 120 x 80 pitch",
              "PASS" if (ev["start_x"].dropna().between(0, 120).all() and ev["start_y"].dropna().between(0, 80).all()) else "FAIL")
    if "Pass" in sr.index:
        p = float(sr.loc["Pass", "success_rate"])
        rep.check("pass success rate looks sensible (0.70-0.95)", "PASS" if 0.70 <= p <= 0.95 else "WARN", "%.3f" % p)
    rep.check("spec columns all present", "PASS" if not absent else "WARN", str(absent) if absent else "")
    return ev, rep


def _save_pip_freeze():
    """Record the exact library versions (the 'anti-mismatch' file for the repo)."""
    try:
        out = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, timeout=120)
        (config.REPORT_DIR / "pip_freeze.txt").write_text(out.stdout, encoding="utf-8")
    except Exception as exc:
        print("(could not save pip freeze: %r)" % exc)


def main(limit=None, refresh=False):
    config.DATA_DIR.mkdir(exist_ok=True)
    print("Step 1/3: getting the data (first run takes several minutes; later runs are instant)")
    matches, raw, lineups = ingest.download_all(limit=limit, refresh=refresh)

    print("Step 2/3: cleaning and checking")
    expected = len(matches) if limit else config.EXPECTED_MATCHES
    ev, rep = process(raw, matches, expected_matches=expected, partial=bool(limit))

    print("Step 3/3: saving")
    ev.to_pickle(config.DATA_DIR / "events_clean.pkl")
    matches.to_pickle(config.DATA_DIR / "matches.pkl")
    pd.to_pickle(lineups, config.DATA_DIR / "lineups.pkl")
    _save_pip_freeze()
    text = rep.save(config.REPORT_DIR / "checkpoint_1.txt")

    print("\n" + text)
    print("\nSaved reports/checkpoint_1.txt  <-- paste the contents of this file to Claude")
    return 1 if rep.n_failed() else 0
