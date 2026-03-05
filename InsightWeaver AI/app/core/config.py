from __future__ import annotations

import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    data_dir: str

def load_settings() -> Settings:
    data_dir = os.getenv("DATA_DIR", "./data").strip()
    os.makedirs(data_dir, exist_ok=True)
    return Settings(data_dir=data_dir)
