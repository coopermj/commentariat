"""Runtime configuration for the API."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_path: str


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url.startswith("sqlite:///"):
        database_path = database_url[len("sqlite:///") :]
    else:
        database_path = os.getenv("DATABASE_PATH", "data/commentariat.db")
    return Settings(database_path=database_path)
