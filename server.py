#!/usr/bin/env python3
"""
Servidor mínimo de lastfm_scrobbles: no tiene web.

- POST /api/jobs/run {"job": "lastfm-scrobbles-daily"} lanza extraer_scrobbles.py y espera.
- Con SYNC_EVERY_HOURS > 0 lo lanza también al arrancar y cada esas horas.
- GET /health.
"""
import os
import signal
import subprocess
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).parent
app = Flask(__name__)

# Si un programador externo (cron, Ofelia) lanza extraer_scrobbles.py, que use este mismo comando.
JOBS = [
    {"id": "lastfm-scrobbles-daily", "label": "Extraer scrobbles (Last.fm + ListenBrainz)",
     "cmd": ["python3", "extraer_scrobbles.py"], "timeout": 1800},
]


@app.route("/health")
def health():
    return jsonify({"ok": True})


def _run_job_cmd(cmd, cwd, timeout):
    """subprocess.run(timeout=...) solo mata al hijo directo -- sus propios
    hijos quedan huérfanos y siguen corriendo (confirmado en producción con
    dieta-sonora-stats). start_new_session=True + os.killpg mata el grupo
    entero al hacer timeout."""
    proc = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, start_new_session=True,
    )
    try:
        stdout, _ = proc.communicate(timeout=timeout)
        return proc.returncode, stdout
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait()
        raise


@app.route("/api/jobs/run", methods=["POST"])
def api_jobs_run():
    job_id = (request.get_json(silent=True) or {}).get("job")
    job = next((j for j in JOBS if j["id"] == job_id), None)
    if not job:
        return jsonify({"error": "Job desconocido"}), 404
    try:
        returncode, output = _run_job_cmd(job["cmd"], str(BASE_DIR), job["timeout"])
        if returncode != 0:
            return jsonify({"error": (output or "")[-2000:] or "Error ejecutando el job"}), 500
        return jsonify({"ok": True, "message": f"{job['label']} completado"})
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Tardó más de {job['timeout']}s (proceso terminado)"}), 500


def _periodic(hours):
    """Sin un programador externo (cron, Ofelia): sincroniza al arrancar y cada `hours` horas."""
    job = JOBS[0]
    while True:
        try:
            code, out = _run_job_cmd(job["cmd"], str(BASE_DIR), job["timeout"])
            print(f"[sync] {job['label']}: código {code}\n{(out or '')[-1500:]}", flush=True)
        except subprocess.TimeoutExpired:
            print(f"[sync] {job['label']}: tardó más de {job['timeout']}s", flush=True)
        time.sleep(hours * 3600)


if __name__ == "__main__":
    every = float(os.environ.get("SYNC_EVERY_HOURS") or 0)
    if every > 0:
        threading.Thread(target=_periodic, args=(every,), daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
