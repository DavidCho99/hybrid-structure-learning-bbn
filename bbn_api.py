from __future__ import annotations

import argparse
import json
import threading
import time
import traceback
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pandas as pd

from arges import run_arges_like
from evaluation import edges_to_frame
from h2pc import run_h2pc
from make_head_to_head_results import render_head_to_head_table
from mmhc import run_mmhc
from preprocessing import DEFAULT_DATASET_PATH


class JobStore:
    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root
        self._lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}

    def create(self, payload: dict[str, Any]) -> str:
        job_id = uuid.uuid4().hex
        with self._lock:
            self._jobs[job_id] = {
                "id": job_id,
                "status": "queued",
                "created_at": time.time(),
                "started_at": None,
                "finished_at": None,
                "payload": payload,
                "error": None,
                "paths": {},
                "summary": None,
            }
        return job_id

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return None if job is None else dict(job)

    def update(self, job_id: str, **updates: Any) -> None:
        with self._lock:
            if job_id not in self._jobs:
                return
            self._jobs[job_id].update(updates)


def _run_job(job_store: JobStore, job_id: str) -> None:
    job = job_store.get(job_id)
    if job is None:
        return

    payload = job.get("payload", {}) or {}
    file_path = str(payload.get("file_path") or DEFAULT_DATASET_PATH)
    sample_size = payload.get("sample_size")
    output_dir = payload.get("output_dir")

    try:
        job_store.update(job_id, status="running", started_at=time.time())

        out_dir = Path(output_dir).expanduser().resolve() if output_dir else (job_store.output_root / job_id)
        out_dir.mkdir(parents=True, exist_ok=True)

        outcomes = [
            run_mmhc(file_path=file_path, sample_size=sample_size),
            run_h2pc(file_path=file_path, sample_size=sample_size),
            run_arges_like(file_path=file_path, sample_size=sample_size),
        ]

        summary_df = pd.DataFrame([outcome["result"] for outcome in outcomes])
        summary_csv = out_dir / "results_summary.csv"
        summary_df.to_csv(summary_csv, index=False)

        edges_to_frame(outcomes[0]["edges"]).to_csv(out_dir / "mmhc_edges.csv", index=False)
        edges_to_frame(outcomes[1]["edges"]).to_csv(out_dir / "h2pc_edges.csv", index=False)
        edges_to_frame(outcomes[2]["edges"]).to_csv(out_dir / "arges_edges.csv", index=False)

        png_path = out_dir / "head_to_head_results.png"
        render_head_to_head_table(summary_csv=summary_csv, output_png=png_path)

        job_store.update(
            job_id,
            status="completed",
            finished_at=time.time(),
            paths={
                "output_dir": str(out_dir),
                "results_summary_csv": str(summary_csv),
                "head_to_head_png": str(png_path),
                "mmhc_edges_csv": str(out_dir / "mmhc_edges.csv"),
                "h2pc_edges_csv": str(out_dir / "h2pc_edges.csv"),
                "arges_edges_csv": str(out_dir / "arges_edges.csv"),
            },
            summary=summary_df.to_dict(orient="records"),
        )
    except Exception as exc:
        job_store.update(
            job_id,
            status="failed",
            finished_at=time.time(),
            error="".join(
                [
                    f"{type(exc).__name__}: {exc}\n",
                    traceback.format_exc(),
                ]
            ),
        )


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    try:
        length = int(handler.headers.get("Content-Length") or 0)
    except ValueError:
        length = 0
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _send_file(handler: BaseHTTPRequestHandler, path: Path, content_type: str) -> None:
    if not path.exists() or not path.is_file():
        _send_json(handler, HTTPStatus.NOT_FOUND, {"error": "not_found"})
        return
    data = path.read_bytes()
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class Handler(BaseHTTPRequestHandler):
    job_store: JobStore

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep logs minimal/quiet.
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/health":
            _send_json(self, HTTPStatus.OK, {"status": "ok"})
            return

        if path.startswith("/jobs/"):
            parts = path.split("/")
            if len(parts) >= 3:
                job_id = parts[2]
                job = self.job_store.get(job_id)
                if job is None:
                    _send_json(self, HTTPStatus.NOT_FOUND, {"error": "unknown_job"})
                    return

                # /jobs/<id>
                if len(parts) == 3:
                    _send_json(self, HTTPStatus.OK, job)
                    return

                # /jobs/<id>/summary
                if len(parts) == 4 and parts[3] == "summary":
                    _send_json(self, HTTPStatus.OK, {"id": job_id, "summary": job.get("summary")})
                    return

                # /jobs/<id>/head_to_head.png
                if len(parts) == 4 and parts[3] == "head_to_head.png":
                    png = (job.get("paths") or {}).get("head_to_head_png")
                    if not png:
                        _send_json(self, HTTPStatus.NOT_FOUND, {"error": "no_png"})
                        return
                    _send_file(self, Path(png), "image/png")
                    return

                # /jobs/<id>/results_summary.csv
                if len(parts) == 4 and parts[3] == "results_summary.csv":
                    csv = (job.get("paths") or {}).get("results_summary_csv")
                    if not csv:
                        _send_json(self, HTTPStatus.NOT_FOUND, {"error": "no_csv"})
                        return
                    _send_file(self, Path(csv), "text/csv; charset=utf-8")
                    return

        _send_json(self, HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/run":
            payload = _read_json_body(self)

            # Optional query params.
            qs = parse_qs(parsed.query or "")
            sample_size_override = qs.get("sample_size", [None])[0]
            if sample_size_override is not None:
                try:
                    payload["sample_size"] = int(sample_size_override)
                except Exception:
                    pass

            job_id = self.job_store.create(payload)
            self.job_store.update(job_id, status="queued")

            thread = threading.Thread(target=_run_job, args=(self.job_store, job_id), daemon=True)
            thread.start()

            _send_json(
                self,
                HTTPStatus.ACCEPTED,
                {
                    "id": job_id,
                    "status": "queued",
                    "poll": f"/jobs/{job_id}",
                },
            )
            return

        _send_json(self, HTTPStatus.NOT_FOUND, {"error": "not_found"})


def main() -> None:
    parser = argparse.ArgumentParser(description="Local HTTP API for running BBN experiments.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--output-root", default="/tmp/bbn_api_runs")
    args = parser.parse_args()

    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    job_store = JobStore(output_root=output_root)

    Handler.job_store = job_store
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"BBN API listening on http://{args.host}:{args.port}")
    print("POST /run with JSON: {file_path, sample_size, output_dir}")
    server.serve_forever()


if __name__ == "__main__":
    main()

