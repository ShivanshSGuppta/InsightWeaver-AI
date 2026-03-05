from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np
from datetime import datetime

def validate(df: pd.DataFrame) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    # Heuristic rules for finance-like data
    if "amount" in df.columns:
        amt = pd.to_numeric(df["amount"], errors="coerce")
        neg = int((amt < 0).sum())
        if neg > 0:
            issues.append({"rule": "amount_non_negative", "severity": "warning", "count": neg, "message": "Negative amounts detected."})

    # date sanity
    date_cols = [c for c in df.columns if "date" in c]
    for c in date_cols:
        s = pd.to_datetime(df[c], errors="coerce")
        future = int((s > pd.Timestamp.utcnow()).sum())
        if future > 0:
            issues.append({"rule": "date_not_future", "severity": "warning", "column": c, "count": future, "message": "Future dates detected."})

    # missing value scan
    for c in df.columns:
        missing = int(df[c].isna().sum())
        if missing > 0 and missing / max(1, len(df)) > 0.25:
            issues.append({"rule": "high_missing_rate", "severity": "info", "column": c, "count": missing, "message": "High missing rate."})

    return {"issues": issues, "issue_count": len(issues)}
