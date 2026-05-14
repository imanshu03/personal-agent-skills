#!/usr/bin/env python3
"""Repo-local configuration for agent handover documents."""

from __future__ import annotations

import json
from pathlib import Path


CONFIG_FILE = ".agent-handover.json"
DEFAULT_HANDOVER_DIR = ".agent-handover"


def config_path(repo: Path) -> Path:
    return repo / CONFIG_FILE


def default_config() -> dict:
    return {"version": 1, "handoverDir": DEFAULT_HANDOVER_DIR}


def load_config(repo: Path) -> dict:
    path = config_path(repo)
    if not path.exists():
        return default_config()
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return default_config()
    data.setdefault("version", 1)
    data.setdefault("handoverDir", DEFAULT_HANDOVER_DIR)
    return data


def save_config(repo: Path, data: dict) -> Path:
    path = config_path(repo)
    data.setdefault("version", 1)
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


def normalize_handover_dir(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("handover directory cannot be empty")
    path = Path(candidate)
    if path.is_absolute():
        raise ValueError("handover directory must be relative to the repository root")
    if ".." in path.parts:
        raise ValueError("handover directory must not contain '..'")
    return path.as_posix()


def handover_dir(repo: Path, override: str | None = None) -> Path:
    if override:
        relative = normalize_handover_dir(override)
    else:
        relative = normalize_handover_dir(str(load_config(repo).get("handoverDir", DEFAULT_HANDOVER_DIR)))
    return repo / relative
