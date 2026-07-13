#!/usr/bin/env python3
"""Small auditable Batch API client used by the APRE fresh phases."""

from __future__ import annotations

import json
import mimetypes
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE = "https://api.openai.com/v1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_json(api_key: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        return json.loads(response.read().decode("utf-8"))


def upload_batch_file(api_key: str, path: Path) -> dict[str, Any]:
    boundary = "----apre" + uuid.uuid4().hex
    filename = path.name
    content_type = mimetypes.guess_type(filename)[0] or "application/jsonl"
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nbatch\r\n".encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n".encode(),
        path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    request = urllib.request.Request(
        BASE + "/files", data=b"".join(parts), method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(api_key: str, file_id: str, destination: Path) -> None:
    request = urllib.request.Request(
        BASE + f"/files/{file_id}/content", method="GET",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        payload = response.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def submit_and_wait(
    *, api_key: str, input_path: Path, run_dir: Path, endpoint: str = "/v1/responses",
    metadata: dict[str, str] | None = None, poll_seconds: int = 20,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    submission_path = run_dir / "batch_submission.json"
    if submission_path.exists():
        submission = json.loads(submission_path.read_text(encoding="utf-8"))
        batch_id = submission["batch_id"]
    else:
        uploaded = upload_batch_file(api_key, input_path)
        batch = request_json(api_key, "POST", "/batches", {
            "input_file_id": uploaded["id"],
            "endpoint": endpoint,
            "completion_window": "24h",
            "metadata": metadata or {},
        })
        submission = {
            "submitted_at": now(), "input_file_id": uploaded["id"],
            "batch_id": batch["id"], "endpoint": endpoint,
        }
        submission_path.write_text(json.dumps(submission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        batch_id = batch["id"]

    history_path = run_dir / "batch_status_history.jsonl"
    while True:
        batch = request_json(api_key, "GET", f"/batches/{batch_id}")
        with history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"observed_at": now(), "batch": batch}, sort_keys=True) + "\n")
        status = batch["status"]
        counts = batch.get("request_counts") or {}
        print(f"[batch] {status}: {counts}", flush=True)
        if status == "completed":
            break
        if status in {"failed", "expired", "cancelled", "cancelling"}:
            raise RuntimeError(f"Batch ended with status {status}")
        time.sleep(poll_seconds)
    output_path = run_dir / "batch_output.jsonl"
    download_file(api_key, batch["output_file_id"], output_path)
    if batch.get("error_file_id"):
        download_file(api_key, batch["error_file_id"], run_dir / "batch_errors.jsonl")
    (run_dir / "batch_final.json").write_text(json.dumps(batch, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return batch

