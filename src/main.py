"""CLI entry point for the YouTube Shorts Automator."""

from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv

from src.config import get_settings
from src.pipeline import Pipeline
from src.scheduler.runner import PipelineScheduler


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="YouTube Shorts Automator — auto-generate and upload shorts."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- run: single pipeline run ---
    run_parser = subparsers.add_parser("run", help="Run the pipeline once")
    run_parser.add_argument(
        "--no-upload", action="store_true", help="Skip YouTube upload (local only)"
    )
    run_parser.add_argument(
        "--privacy",
        choices=["public", "unlisted", "private"],
        default="private",
        help="YouTube video privacy (default: private)",
    )
    run_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    # --- schedule: continuous pipeline ---
    sched_parser = subparsers.add_parser("schedule", help="Run pipeline on a schedule")
    sched_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    # --- generate-script: just generate a script ---
    script_parser = subparsers.add_parser("generate-script", help="Generate a script only")
    script_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    setup_logging(getattr(args, "verbose", False))
    settings = get_settings()

    if args.command == "run":
        pipeline = Pipeline(settings)
        result = pipeline.run(
            upload=not args.no_upload,
            privacy=args.privacy,
        )
        print(f"\nDone! Output: {result}")

    elif args.command == "schedule":
        scheduler = PipelineScheduler(settings)
        scheduler.start()

    elif args.command == "generate-script":
        from src.script_generator import ScriptGenerator

        gen = ScriptGenerator(settings)
        script = gen.generate()
        print(f"\nTitle: {script.title}")
        print(f"Source: {script.source}")
        print(f"Hashtags: {' '.join(script.hashtags)}")
        print(f"\n--- Script ---\n{script.text}\n")


if __name__ == "__main__":
    main()
