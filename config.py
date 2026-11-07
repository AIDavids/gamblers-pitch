"""
config.py - every project setting lives here, in ONE place.

Why: if a number (like the 10-event window) is typed in five different files,
it is easy to change one and forget the others. Here, we change it once.
"""
from pathlib import Path

# ---------- Folders (always relative to this file, so it works on any PC) ----------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"          # big files, NOT uploaded to GitHub (see .gitignore)
RAW_DIR = DATA_DIR / "raw"        # raw downloads, cached so we never download twice
OUTPUT_DIR = ROOT / "outputs"     # final CSV / JSON / PNG files (these DO go to GitHub)
REPORT_DIR = ROOT / "reports"     # small checkpoint text files you paste back to Claude

# ---------- The dataset (spec rule 1: Euro 2024 only) ----------
COMPETITION_ID = 55
SEASON_ID = 282
EXPECTED_MATCHES = 51
EXPECTED_TEAMS = 24

# ---------- Modelling settings (used from Stage 2 onward) ----------
RANDOM_STATE = 42                 # spec rule 4: same random seed everywhere
EVENT_WINDOW = 10                 # "did a shot follow in the next 10 events?"
WINDOW_CHECKS = (5, 10, 15)       # amendment A4: robustness check on the window
GAMBLE_MIN_X_GAIN = 10            # a "gamble" ends >= 10 pitch units closer to goal
GAMBLE_THRESHOLD_CHECKS = (5, 10, 15)   # amendment A5 (PENDING approval)

# ---------- Stage 1 cleaning ----------
SHOOTOUT_PERIOD = 5               # trap 4: penalty shoot-out events are dropped
KEEP_TYPES = [
    "Pass", "Carry", "Dribble", "Shot", "Dispossessed", "Miscontrol",
    "Ball Receipt*", "Duel", "Interception", "Ball Recovery", "Clearance",
    "Block", "Foul Won", "Foul Committed", "Pressure",
]
LOCATED_TYPES = ["Pass", "Carry", "Dribble", "Shot"]   # types that must have a location

# ---------- Figure style (spec section 4) ----------
PAPER = "#F9F9F7"
INK = "#111111"
