"""
ingest.py - downloads the Euro 2024 data from StatsBomb's open data.

Good data-engineering habits used here:
  * CACHE: every match is saved to data/raw/ the first time. Re-running never
    downloads again (and an interrupted run simply resumes where it stopped).
  * RETRY: a failed download is retried 3 times with a growing pause.
  * ATOMIC SAVE: files are written under a temporary name then renamed, so a
    crash can never leave a half-written (corrupt) file behind.

(Stage 1b will rebuild this step with plain HTTP requests, to show what the
statsbombpy package does behind the scenes.)
"""
import logging
import pickle
import time
import warnings

import pandas as pd

import config


def _save_pickle(obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        pickle.dump(obj, f)
    tmp.replace(path)                      # rename = the "atomic" step


def _load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def _retry(fn, what, tries=3, wait=3):
    """Run fn(); if it fails, wait and try again (up to `tries` times)."""
    for attempt in range(1, tries + 1):
        try:
            return fn()
        except Exception as exc:           # network hiccups, timeouts, etc.
            if attempt == tries:
                raise
            pause = wait * attempt
            print("  ! %s failed (%r). Retrying in %ds..." % (what, exc, pause))
            time.sleep(pause)


def _statsbomb():
    """Import statsbombpy quietly (it prints a harmless 'no credentials' warning)."""
    warnings.filterwarnings("ignore")
    logging.getLogger("statsbombpy").setLevel(logging.ERROR)
    from statsbombpy import sb
    return sb


def load_matches(refresh=False):
    path = config.RAW_DIR / "matches.pkl"
    if path.exists() and not refresh:
        return _load_pickle(path)
    sb = _statsbomb()
    matches = _retry(lambda: sb.matches(competition_id=config.COMPETITION_ID,
                                        season_id=config.SEASON_ID), "matches table")
    matches = matches.sort_values("match_id").reset_index(drop=True)
    _save_pickle(matches, path)
    return matches


def load_match(match_id, refresh=False):
    """Events and lineups for ONE match (from cache if we already have them)."""
    ev_path = config.RAW_DIR / ("events_%d.pkl" % match_id)
    lu_path = config.RAW_DIR / ("lineups_%d.pkl" % match_id)
    if ev_path.exists() and lu_path.exists() and not refresh:
        return _load_pickle(ev_path), _load_pickle(lu_path), True
    sb = _statsbomb()
    events = _retry(lambda: sb.events(match_id=match_id), "events %d" % match_id)
    events["match_id"] = match_id          # remember which match each row came from
    lineups = _retry(lambda: sb.lineups(match_id=match_id), "lineups %d" % match_id)
    _save_pickle(events, ev_path)
    _save_pickle(lineups, lu_path)
    return events, lineups, False


def download_all(limit=None, refresh=False):
    """Returns (matches table, all events stacked together, lineups dict)."""
    matches = load_matches(refresh=refresh)
    if limit:
        matches = matches.head(limit)
    frames, lineups = [], {}
    n = len(matches)
    for i, mid in enumerate(matches["match_id"], start=1):
        events, lu, cached = load_match(int(mid), refresh=refresh)
        frames.append(events)
        lineups[int(mid)] = lu
        print("  [%2d/%d] match %d  %s  (%d events)" % (i, n, mid, "cached" if cached else "downloaded", len(events)))
    raw = pd.concat(frames, ignore_index=True)
    return matches, raw, lineups
