from __future__ import annotations

import re
import pandas as pd
import numpy as np

CURRENCY_RE = re.compile(r"[^0-9\.-]+")

def to_snake(name: str) -> str:
    n = (name or "").strip()
    n = re.sub(r"[\s\-\/]+", "_", n)
    n = re.sub(r"[^a-zA-Z0-9_]+", "", n)
    n = re.sub(r"_+", "_", n)
    return n.lower().strip("_") or "col"

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Clean column names
    rename = {c: to_snake(str(c)) for c in out.columns}
    out = out.rename(columns=rename)

    # Trim strings
    for c in out.columns:
        if pd.api.types.is_object_dtype(out[c]):
            out[c] = out[c].astype(str).replace({"nan": None, "None": None})
            out[c] = out[c].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Parse date-like columns
    for c in out.columns:
        if "date" in c or c.endswith("_at"):
            try:
                out[c] = pd.to_datetime(out[c], errors="coerce", dayfirst=True)
            except Exception:
                pass

    # Parse money-like columns
    for c in out.columns:
        if any(k in c for k in ["amount", "price", "cost", "total"]):
            try:
                out[c] = out[c].astype(str).apply(lambda x: None if x in {"None", "nan"} else x)
                out[c] = out[c].apply(lambda x: float(CURRENCY_RE.sub("", x)) if isinstance(x, str) and x else np.nan)
            except Exception:
                pass

    return out
