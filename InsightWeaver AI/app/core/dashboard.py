from __future__ import annotations

from typing import Any
import pandas as pd

def build_dashboard(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}

    out["row_count"] = int(len(df))
    out["columns"] = [str(c) for c in df.columns]

    # basic KPIs
    if "amount" in df.columns:
        amt = pd.to_numeric(df["amount"], errors="coerce")
        out["amount_sum"] = float(amt.fillna(0).sum())
        out["amount_avg"] = float(amt.dropna().mean()) if amt.dropna().shape[0] else 0.0

    # by category
    if "category" in df.columns and "amount" in df.columns:
        g = df.copy()
        g["amount"] = pd.to_numeric(g["amount"], errors="coerce").fillna(0)
        by_cat = g.groupby("category")["amount"].sum().sort_values(ascending=False).head(10)
        out["by_category"] = {"labels": by_cat.index.astype(str).tolist(), "values": by_cat.values.tolist()}

    # by month
    date_col = None
    for c in df.columns:
        if "date" in c:
            date_col = c
            break

    if date_col and "amount" in df.columns:
        g = df.copy()
        g[date_col] = pd.to_datetime(g[date_col], errors="coerce")
        g = g.dropna(subset=[date_col])
        g["month"] = g[date_col].dt.to_period("M").astype(str)
        g["amount"] = pd.to_numeric(g["amount"], errors="coerce").fillna(0)
        by_month = g.groupby("month")["amount"].sum().sort_index()
        out["by_month"] = {"labels": by_month.index.astype(str).tolist(), "values": by_month.values.tolist()}

    return out
