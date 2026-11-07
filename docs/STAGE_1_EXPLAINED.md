# Stage 1 explained: load and clean

## What this stage does, in one sentence
It downloads every event from the 51 Euro 2024 matches, tidies the table so later stages
can trust it, and proves with automatic checks that the data is complete and correct.

## Why it matters
Every later number comes from this table. If a pass is wrongly marked "failed", every
value, map and player score built on it is wrong. So we check before we build.

## The steps (in the order the code runs)

1. **Download (src/ingest.py).** For each match we fetch the events (every pass, carry, shot...)
   and the lineups (who played where). Each match is saved in `data/raw/` the first time, so
   re-running is instant and an interrupted run resumes where it stopped. Failed downloads
   are retried 3 times.
2. **Drop the penalty shoot-out (trap 4).** Shoot-out kicks are period 5. They are not
   normal play, so they go. Extra time (periods 3 and 4) stays.
3. **Check the goals (before filtering).** We count goals from the events (shots with outcome
   Goal, plus own goals credited to the team that benefits) and compare with the official score
   of every match. If they match, the data is complete. This is the project's first big test.
4. **Keep the useful event types.** We keep Pass, Carry, Dribble, Shot, Dispossessed,
   Miscontrol, Ball Receipt*, Duel, Interception, Ball Recovery, Clearance, Block, Foul Won,
   Foul Committed and Pressure. Everything else (substitutions, half starts...) is dropped.
5. **Sort** by match and event order, because several rules look at "the next event".
6. **Coordinates.** `location` is a list like [x, y]. We split it into `start_x`, `start_y`, and
   build `end_x`, `end_y` (pass end for passes, carry end for carries, otherwise the start).
   The pitch is 120 by 80 and the attacking team always attacks toward x = 120.
7. **The success flag** (this is what amendment A1 needs):
   - **Pass:** if `pass_outcome` is EMPTY the pass was completed (trap 1). Anything else
     (Incomplete, Out, Pass Offside, Unknown) means it failed.
   - **Dribble:** "Complete" = success, "Incomplete" = failure (trap 2).
   - **Carry:** carries have no flag. A carry fails only if the very next event is Dispossessed
     or Miscontrol by the same player.
   - Other events get a blank, because "success" does not apply to them.
8. **Save** the clean table to `data/events_clean.pkl` (plus matches and lineups), and write
   `reports/checkpoint_1.txt` and `reports/pip_freeze.txt` (the exact library versions).

## How to read the checkpoint report
- **AUTO-CHECKS at the bottom:** PASS is good. WARN means "look at this, probably fine".
  FAIL means stop and tell Claude (spec rule 8: do not silently change the method).
- **Goals check:** ideally "0 of 51" differ. If some differ, the report lists them plus the
  own-goal events, which is the most likely cause, so Claude can fix the rule.
- **Success rates:** passes should be completed most of the time (roughly 80 to 90 percent).
  A very different number would suggest a mistake in trap 1.

## What is NOT done yet
No models, no values, no maps. Those start in Stage 2 after Checkpoint 1 is approved.
