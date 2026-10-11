"""Settings from config.yaml and the environment (.env)."""
import os
import sqlite3
from contextlib import closing
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@lru_cache
def cfg() -> dict:
    with open(Path(__file__).with_name("config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_setting(key: str) -> str | None:
    """A value stored with the loaded data (planning start, data-card counts); None if not set."""
    try:
        with closing(sqlite3.connect(db_path())) as con:
            row = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    except sqlite3.Error:  # no database or no settings table yet
        return None
    return row[0] if row else None


def set_setting(key: str, value: str | None) -> None:
    with closing(sqlite3.connect(db_path())) as con, con:
        con.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
        if value is None:
            con.execute("DELETE FROM settings WHERE key = ?", (key,))
        else:
            con.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (key, value))


def planning_start() -> date:
    """The planning start set with the data (CLI flag, data_card.json or /ingest), else config.yaml."""
    stored = get_setting("planning_start")
    return date.fromisoformat(stored or str(cfg()["planning_start"]))


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).split("#")[0].strip()


def mock_llm() -> bool:
    return env("MOCK_LLM", "true").lower() in ("1", "true", "yes")


def db_path() -> str:
    return env("DB_PATH", str(ROOT / "allocator.db"))
