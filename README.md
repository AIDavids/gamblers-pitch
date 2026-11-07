# The Gambler's Pitch

A plain-English analysis of UEFA Euro 2024: every pass, carry or dribble is a gamble.
We value each action as **reward if it works minus cost if the ball is lost**, then ask
where gambling pays, when a dribble beats a pass, and which players decide well.

Data provided by StatsBomb (https://statsbomb.com). Inspired by Karun Singh's Expected
Threat (xT, 2018) and Decroos et al., "Actions Speak Louder than Goals" (KDD 2019, VAEP).

**Status:** Pack 0 (project skeleton + Stage 1). No results yet.

## One-time setup (Windows, from inside this folder)
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
Next time you only need `venv\Scripts\activate`.

## Run a stage
```
python -m unittest discover -s tests -v     (optional: 13 quick self-tests, no internet)
python run_stage.py 1 --limit 2             (quick 2-match test, about a minute)
python run_stage.py 1                       (the real run, all 51 matches, several minutes)
```
Then open `reports/checkpoint_1.txt` and paste its contents to Claude.

## Folders
- `config.py`      all settings in one place
- `src/`           the code, one commented module per job
- `run_stage.py`   the command that runs a stage
- `tests/`         small self-checks on made-up data
- `docs/`          plain-English explanations, the spec change log, web app idea bank
- `data/`          big files (not uploaded to GitHub, always re-creatable)
- `outputs/`       final CSV / JSON / PNG results (uploaded)
- `reports/`       checkpoint text files (uploaded)
- `predictions.md` write your guesses here BEFORE Stage 3

## Saving to GitHub
```
git status
git add .
git commit -m "Pack 0: skeleton and Stage 1"
git push
```
