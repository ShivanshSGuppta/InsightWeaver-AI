from __future__ import annotations

import os
import json
import secrets
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .core.config import load_settings
from .core.store import RunStore, RunRecord, now_iso
from .core.io import read_uploaded
from .core.schema import infer_schema
from .core.normalize import normalize
from .core.dedupe import deduplicate
from .core.validate import validate
from .core.dashboard import build_dashboard

settings = load_settings()
data_dir = Path(settings.data_dir)
runs_dir = data_dir / "runs"
runs_dir.mkdir(parents=True, exist_ok=True)

store = RunStore(str(data_dir / "runs.sqlite"))

app = FastAPI(title="InsightWeaver", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def new_run_id() -> str:
    return f"run_{now_iso().replace(':','').replace('-','').replace('T','_')}_{secrets.token_hex(3)}"

def persist_run(run_id: str, filename: str, df_in: pd.DataFrame, df_out: pd.DataFrame, duplicates_removed: int, schema: dict, validation: dict, dashboard: dict) -> Path:
    run_path = runs_dir / run_id
    run_path.mkdir(parents=True, exist_ok=True)

    # write artifacts
    (run_path / "schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    (run_path / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (run_path / "dashboard.json").write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    (run_path / "report.json").write_text(json.dumps({
        "run_id": run_id,
        "created_at": now_iso(),
        "filename": filename,
        "rows_in": int(len(df_in)),
        "rows_out": int(len(df_out)),
        "duplicates_removed": int(duplicates_removed),
        "schema": schema,
        "validation": validation,
        "dashboard": dashboard,
    }, indent=2), encoding="utf-8")

    df_out.to_csv(run_path / "normalized.csv", index=False)

    store.upsert(RunRecord(
        run_id=run_id,
        created_at=now_iso(),
        filename=filename,
        rows_in=int(len(df_in)),
        rows_out=int(len(df_out)),
        duplicates_removed=int(duplicates_removed),
    ))

    return run_path

def load_artifact(run_id: str, name: str) -> Path:
    p = runs_dir / run_id / name
    if not p.exists():
        raise FileNotFoundError("Artifact not found")
    return p

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    recent = store.list_recent(10)
    return templates.TemplateResponse("index.html", {"request": request, "recent": recent})


@app.get("/help", response_class=HTMLResponse)
def help_page(request: Request):
    return templates.TemplateResponse(
        "help.html",
        {
            "request": request,
            "title": "Help",
        },
    )

@app.get("/runs", response_class=HTMLResponse)
def runs(request: Request):
    recent = store.list_recent(50)
    return templates.TemplateResponse("runs.html", {"request": request, "recent": recent})

@app.get("/sample/run")
def run_sample():
    sample_path = Path(os.getcwd()) / "sample" / "sample_finance.csv"
    df_in = pd.read_csv(sample_path)
    return _process_and_redirect(df_in, filename="sample_finance.csv")

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    df_in = read_uploaded(file.filename, content)
    return _process_and_redirect(df_in, filename=file.filename)

def _process_and_redirect(df_in: pd.DataFrame, filename: str):
    run_id = new_run_id()

    schema = infer_schema(df_in)
    df_norm = normalize(df_in)
    df_out, removed = deduplicate(df_norm)
    validation = validate(df_out)
    dashboard = build_dashboard(df_out)

    persist_run(run_id, filename, df_in, df_out, removed, schema, validation, dashboard)
    return RedirectResponse(url=f"/report/{run_id}", status_code=303)

@app.get("/report/{run_id}", response_class=HTMLResponse)
def report(request: Request, run_id: str):
    rec = store.get(run_id)
    if not rec:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Run not found."}, status_code=404)

    report_json = json.loads(load_artifact(run_id, "report.json").read_text(encoding="utf-8"))
    return templates.TemplateResponse("report.html", {"request": request, "rec": rec, "report": report_json})

@app.get("/download/{run_id}/{artifact}")
def download(run_id: str, artifact: str):
    allow = {"normalized.csv", "schema.json", "validation.json", "dashboard.json", "report.json"}
    if artifact not in allow:
        return RedirectResponse(url=f"/report/{run_id}", status_code=303)
    p = load_artifact(run_id, artifact)
    return FileResponse(path=str(p), filename=artifact)

