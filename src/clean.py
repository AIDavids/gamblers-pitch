"""
clean.py - Stage 1 cleaning, written as small separate functions.

Each function takes a table and returns a table. That makes every step easy to
explain in an interview, and easy to test on a tiny made-up table.
"""
import numpy as np
import pandas as pd

import config

# Columns we cannot work without. If one is missing we STOP and ask (spec rule 8).
REQUIRED_COLUMNS = [
    "match_id", "index", "period", "type", "team", "player", "location",
    "pass_outcome", "pass_end_location", "dribble_outcome",
    "carry_end_location", "shot_outcome",
]

# Columns the spec lists as useful for later stages. Missing ones are only reported.
SPEC_USEFUL_COLUMNS = [
    "location", "pass_end_location", "carry_end_location", "pass_outcome",
    "dribble_outcome", "shot_statsbomb_xg", "under_pressure", "possession",
    "possession_team", "play_pattern", "pass_length", "pass_angle", "pass_cross",
    "pass_through_ball", "pass_shot_assist", "pass_goal_assist",
    "pass_assisted_shot_id", "position", "period", "minute", "team", "player",
]


def check_required_columns(df):
    """Stop with a clear message if a column we depend on is missing."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing required columns: %s. Stop and tell Claude (spec rule 8)." % missing
        )


def drop_shootout(df):
    """Trap 4: remove penalty shoot-out events (period 5). Extra time (3-4) stays."""
    return df[df["period"] != config.SHOOTOUT_PERIOD].copy()


# ----------------------------------------------------------------------------
# Goals check: do the goals we count from the events match the official scores?
# ----------------------------------------------------------------------------
def count_goals(df):
    """Goals per match and team = shots with outcome Goal + own goals.
    'Own Goal For' is credited to the team that BENEFITS from the own goal."""
    shots = df[(df["type"] == "Shot") & (df["shot_outcome"] == "Goal")]
    own = df[df["type"] == "Own Goal For"]
    both = pd.concat([shots[["match_id", "team"]], own[["match_id", "team"]]])
    if both.empty:
        return pd.DataFrame(columns=["match_id", "team", "goals"])
    return both.groupby(["match_id", "team"]).size().rename("goals").reset_index()


def reconcile_goals(matches, goals):
    """Compare our goal counts with the official home/away scores per match."""
    lookup = {(r.match_id, r.team): int(r.goals) for r in goals.itertuples()}
    out = matches[["match_id", "home_team", "away_team", "home_score", "away_score"]].copy()
    out["home_calc"] = [lookup.get((m, t), 0) for m, t in zip(out["match_id"], out["home_team"])]
    out["away_calc"] = [lookup.get((m, t), 0) for m, t in zip(out["match_id"], out["away_team"])]
    out["ok"] = (out["home_calc"] == out["home_score"]) & (out["away_calc"] == out["away_score"])
    return out


def own_goal_summary(df):
    """Helper for diagnosing mismatches: own-goal events per match, type and team."""
    og = df[df["type"].isin(["Own Goal For", "Own Goal Against"])]
    if og.empty:
        return pd.DataFrame(columns=["match_id", "type", "team", "n"])
    return og.groupby(["match_id", "type", "team"]).size().rename("n").reset_index()


# ----------------------------------------------------------------------------
# Cleaning steps
# ----------------------------------------------------------------------------
def _xy(series, i):
    """Pull the i-th number (0 = x, 1 = y) out of a [x, y] list; NaN if no list."""
    return series.apply(lambda v: v[i] if isinstance(v, (list, tuple, np.ndarray)) and len(v) > i else np.nan)


def add_coordinates(df):
    """Turn [x, y] lists into plain number columns (easier for models later).
    End point = pass end for passes, carry end for carries, otherwise the start."""
    df = df.copy()
    t = df["type"]
    df["start_x"] = _xy(df["location"], 0).astype(float)
    df["start_y"] = _xy(df["location"], 1).astype(float)
    end = df["location"].copy()
    end = end.where(t != "Carry", df["carry_end_location"])
    end = end.where(t != "Pass", df["pass_end_location"])
    df["end_x"] = _xy(end, 0).astype(float)
    df["end_y"] = _xy(end, 1).astype(float)
    return df


def add_success(df):
    """Create the success flag: 1.0 = worked, 0.0 = failed, blank = not applicable.
    The table MUST already be sorted by match_id, index (needed for carries)."""
    df = df.copy()
    t = df["type"]
    is_pass, is_dribble, is_carry = (t == "Pass"), (t == "Dribble"), (t == "Carry")

    success = pd.Series(np.nan, index=df.index, dtype="float64")

    # Trap 1: a MISSING pass_outcome means the pass was COMPLETE.
    success[is_pass] = df.loc[is_pass, "pass_outcome"].isna().astype(float)

    # Trap 2: dribble_outcome is "Complete" or "Incomplete".
    success[is_dribble] = (df.loc[is_dribble, "dribble_outcome"] == "Complete").astype(float)

    # Carries have no flag. A carry FAILS only if the very next event in the same
    # match is Dispossessed or Miscontrol by the SAME player.
    grp = df.groupby("match_id")
    next_type = grp["type"].shift(-1)
    next_player = grp["player"].shift(-1)
    carry_failed = is_carry & next_type.isin(["Dispossessed", "Miscontrol"]) & (next_player == df["player"])
    success[is_carry] = (~carry_failed[is_carry]).astype(float)

    df["success"] = success
    return df


def clean_events(raw_no_shootout):
    """The whole cleaning recipe: keep useful types, sort, coordinates, success."""
    df = raw_no_shootout[raw_no_shootout["type"].isin(config.KEEP_TYPES)]
    df = df.sort_values(["match_id", "index"]).reset_index(drop=True)
    df = add_coordinates(df)
    df = add_success(df)
    return df
