#!/usr/bin/env python3
"""Configure where agent handover documents are stored for a repository."""

from __future__ import annotations

import argparse
from pathlib import Path

import handover_config
from create_handover import git_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure agent handover document storage.")
    parser.add_argument("--cwd", default=".", help="Workspace directory.")
    parser.add_argument("--dir", help="Directory path relative to the repository root.")
    parser.add_argument("--show", action="store_true", help="Show the current configured directory.")
    args = parser.parse_args()

    repo = git_root(Path(args.cwd).resolve())
    config = handover_config.load_config(repo)

    if args.dir:
        config["handoverDir"] = handover_config.normalize_handover_dir(args.dir)
        path = handover_config.save_config(repo, config)
        print(f"Config file: {path}")
        print(f"Handover directory: {repo / config['handoverDir']}")
        return

    print(f"Config file: {handover_config.config_path(repo)}")
    print(f"Handover directory: {repo / config['handoverDir']}")
    if not handover_config.config_path(repo).exists() and not args.show:
        print()
        print("No repo preference is saved yet. Save the default with:")
        print("python3 skills/agent-handover/scripts/setup_handover.py --dir .agent-handover")


if __name__ == "__main__":
    main()
