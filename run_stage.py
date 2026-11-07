"""
run_stage.py - the one command that runs a stage.

    python run_stage.py 1                 run Stage 1 on all 51 matches
    python run_stage.py 1 --limit 2       quick test on just 2 matches (about 1 minute)
    python run_stage.py 1 --refresh       ignore the cache and download again
"""
import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):          # make Windows consoles print any team name
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(description="Run one stage of The Gambler's Pitch")
    parser.add_argument("stage", type=int, help="stage number to run (1 for now)")
    parser.add_argument("--limit", type=int, default=None, help="only use the first N matches (for a quick test)")
    parser.add_argument("--refresh", action="store_true", help="re-download instead of using the cache")
    args = parser.parse_args()

    if args.stage == 1:
        from src import stage1
        sys.exit(stage1.main(limit=args.limit, refresh=args.refresh))
    print("Stage %d is not in this pack yet." % args.stage)
    sys.exit(2)


if __name__ == "__main__":
    main()
