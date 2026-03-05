from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np

def infer_schema(df: pd.DataFrame) -> dict[str, Any]:
    schema: dict[str, Any] = {"columns": [], "row_count": int(len(df)), "column_count": int(df.shape[1])}

    for col in df.columns:
        s = df[col]
        nulls = int(s.isna().sum())
        null_rate = float(nulls / max(1, len(s)))
        dtype = str(s.dtype)

        # infer "semantic" type
        semantic = "string"
        if pd.api.types.is_bool_dtype(s):
            semantic = "boolean"
        elif pd.api.types.is_integer_dtype(s):
            semantic = "integer"
        elif pd.api.types.is_float_dtype(s):
            semantic = "number"
        elif pd.api.types.is_datetime64_any_dtype(s):
            semantic = "datetime"
        else:
            # try datetime parse on object
            if pd.api.types.is_object_dtype(s):
                try:
                    parsed = pd.to_datetime(s.dropna().astype(str), errors="raise", utc=True)
                    if len(parsed) >= max(3, int(0.4 * len(s.dropna()))):
                        semantic = "datetime"
                except Exception:
                    semantic = "string"

        examples = s.dropna().astype(str).head(3).tolist()

        col_info: dict[str, Any] = {
            "name": str(col),
            "dtype": dtype,
            "semantic_type": semantic,
            "nulls": nulls,
            "null_rate": round(null_rate, 4),
            "unique": int(s.nunique(dropna=True)),
            "examples": examples,
        }

        if semantic in {"integer", "number"}:
            try:
                col_info["min"] = float(pd.to_numeric(s, errors="coerce").min())
                col_info["max"] = float(pd.to_numeric(s, errors="coerce").max())
            except Exception:
                pass

        schema["columns"].append(col_info)

    return schema
