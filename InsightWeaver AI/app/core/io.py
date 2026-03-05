from __future__ import annotations

import io
import json
from typing import Tuple

import pandas as pd

SUPPORTED_EXT = {".csv", ".xlsx", ".xls", ".json"}

def read_uploaded(filename: str, content: bytes) -> pd.DataFrame:
    name = (filename or "").lower().strip()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(content))
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(io.BytesIO(content))
    if name.endswith(".json"):
        obj = json.loads(content.decode("utf-8"))
        # accept list-of-objects or dict with 'data'
        if isinstance(obj, dict) and "data" in obj:
            obj = obj["data"]
        return pd.DataFrame(obj)
    raise ValueError("Unsupported file type. Use CSV, XLSX, or JSON.")
