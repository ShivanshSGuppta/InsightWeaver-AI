from __future__ import annotations

import pandas as pd

PREFERRED_KEYS = ["transaction_id", "invoice_id", "id"]

def deduplicate(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    before = len(df)
    keys = [k for k in PREFERRED_KEYS if k in df.columns]
    if keys:
        out = df.drop_duplicates(subset=keys, keep="first")
    else:
        out = df.drop_duplicates(keep="first")
    removed = before - len(out)
    return out, removed
