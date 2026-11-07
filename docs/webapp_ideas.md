# Web app idea bank (design session happens after Checkpoint 2)

Rule: write ideas here as they come. Nothing is decided until the design session.
The app is built AFTER the analysis, model and report. Euro 2024 data only.

## Working concept: "Call the Gamble"
- 5 real Euro 2024 moments per day (position, pressure, minute, scoreline; outcome hidden).
- Five football decisions: Shoot, Dribble, Carry forward, Forward pass, Safe pass (menu changes by zone).
- Reveal: the model's pick (best on average, or "toss-up"), what actually happened next in the real match, score by regret.
- Honest wording: "best on average from this spot", never "the best decision".
- End-of-game hook: "your decision style matches [Euro 2024 player]" (for fun, links to profile card).
- Streaks and daily results kept in the browser (localStorage), no accounts.

## Other pieces
- Scouting room: player search, six percentile bars, similar players (nearest neighbours).
- Tinker mode: click the pitch for a live model value (FastAPI).

## Habit and PR ideas to explore
- Daily seed shared by everyone + shareable emoji result card (Wordle)
- Streaks (Duolingo), score by distance from the best answer (GeoGuessr)
- (add ideas below)

## Constraints to respect while modelling
- Include `success` as a feature (A1).
- Write a function that scores any hypothetical action (expected value over success / failure).
- Save real moments and player-style data into outputs/ for the app.
