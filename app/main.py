import json
import logging
import os
import sys
import time
import uuid
from flask import Flask, Response, jsonify, render_template_string, request


def validate_port(port_str):
    try:
        val = int(port_str)
        if 1 <= val <= 65535:
            return val
        raise ValueError
    except (ValueError, TypeError):
        raise ValueError(f"Invalid PORT: {port_str}. Must be an integer between 1 and 65535.")


def get_env_config():
    raw_port = os.getenv("PORT", "8080")
    port = validate_port(raw_port)
    host = os.getenv("HOST", "127.0.0.1")
    dep_path = os.getenv("DEPENDENCY_PATH") or os.getenv("DEPENDENCY_FILE", "data/dependency.ok")
    version = os.getenv("APP_VERSION", "v1.0.0")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    return {
        "PORT": port,
        "HOST": host,
        "DEPENDENCY_PATH": dep_path,
        "APP_VERSION": version,
        "LOG_LEVEL": log_level,
    }


def check_readiness(dep_path):
    start = time.perf_counter()
    ready = False
    try:
        if os.path.exists(dep_path) and os.path.isfile(dep_path) and os.access(dep_path, os.R_OK):
            ready = True
    except (OSError, PermissionError):
        ready = False
    duration_ms = round((time.perf_counter() - start) * 1000, 3)
    return ready, duration_ms


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CareerSwami Service Status</title>
<style>
:root {
  --deep-violet: #2E0A52;
  --royal-purple: #6A1BB5;
  --lavender: #F5F0FF;
  --teal: #00C2A8;
  --ink: #1B1030;
  --success: #1FA971;
  --failure: #E5484D;
}
body {
  margin: 0;
  padding: 40px 20px;
  background-color: var(--lavender);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  display: flex;
  justify-content: center;
}
.card {
  background: #FFFFFF;
  border-radius: 12px;
  max-width: 640px;
  width: 100%;
  padding: 32px;
  box-shadow: 0 10px 25px rgba(46, 10, 82, 0.08);
  border-top: 6px solid var(--royal-purple);
}
h1 {
  color: var(--deep-violet);
  margin-top: 0;
  font-size: 24px;
}
.subtitle {
  color: var(--royal-purple);
  font-weight: 600;
  margin-bottom: 24px;
}
.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}
.metric-box {
  background: var(--lavender);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid rgba(106, 27, 181, 0.15);
}
.metric-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--royal-purple);
  margin-bottom: 8px;
}
.badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 14px;
  color: #FFFFFF;
}
.badge-success {
  background-color: var(--success);
}
.badge-failure {
  background-color: var(--failure);
}
.badge-info {
  background-color: var(--teal);
  color: var(--ink);
}
.details {
  border-top: 1px solid rgba(46, 10, 82, 0.1);
  padding-top: 16px;
  font-size: 14px;
}
.details-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
}
.footer {
  margin-top: 24px;
  font-size: 12px;
  color: var(--royal-purple);
  text-align: center;
}
</style>
</head>
<body>
<div class="card">
  <h1>CareerSwami Service Monitor</h1>
  <div class="subtitle">Tiny Service Status &amp; Readiness Dashboard</div>
  <div class="status-grid">
    <div class="metric-box">
      <div class="metric-label">Process Health</div>
      <span class="badge badge-success">OK (200)</span>
    </div>
    <div class="metric-box">
      <div class="metric-label">Dependency Readiness</div>
      {% if ready %}
      <span class="badge badge-success">READY (200)</span>
      {% else %}
      <span class="badge badge-failure">DEGRADED (503)</span>
      {% endif %}
    </div>
  </div>
  <div class="details">
    <div class="details-row">
      <strong>Service Version</strong>
      <span>{{ version }}</span>
    </div>
    <div class="details-row">
      <strong>Dependency State</strong>
      <span>{{ dependency_state }}</span>
    </div>
    <div class="details-row">
      <strong>Probe Latency</strong>
      <span>{{ duration_ms }} ms</span>
    </div>
    <div class="details-row">
      <strong>Request Identifier</strong>
      <span style="font-family: monospace;">{{ request_id }}</span>
    </div>
  </div>
  <div class="footer">
    Portfolio Grade DevOps Deliverable &bull; Clean-Start Reproducibility Standard
  </div>
</div>
</body>
</html>
"""


def create_app(config=None):
    app = Flask(__name__)
    app_config = get_env_config()
    if config:
        app_config.update(config)

    log_level_name = app_config.get("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, log_level_name, logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    logger = logging.getLogger("service")
    logger.setLevel(numeric_level)

    @app.before_request
    def set_request_context():
        req_id = request.headers.get("X-Request-ID")
        if not req_id:
            req_id = str(uuid.uuid4())
        request.request_id = req_id

    @app.after_request
    def add_headers(response):
        if hasattr(request, "request_id"):
            response.headers["X-Request-ID"] = request.request_id
        return response

    @app.route("/health", methods=["GET"])
    def health():
        version = app_config.get("APP_VERSION", "v1.0.0")
        return jsonify({"status": "ok", "version": version}), 200

    @app.route("/ready", methods=["GET"])
    def ready():
        dep_path = app_config.get("DEPENDENCY_PATH", "data/dependency.ok")
        is_ready, duration_ms = check_readiness(dep_path)
        outcome = "ok" if is_ready else "unreachable"
        status_code = 200 if is_ready else 503
        req_id = getattr(request, "request_id", "unknown")
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": "INFO" if is_ready else "WARNING",
            "event": "readiness_probe",
            "outcome": outcome,
            "duration_ms": duration_ms,
            "request_id": req_id,
        }
        logger.info(json.dumps(log_entry))
        return jsonify({"ready": is_ready, "dependency": outcome}), status_code

    @app.route("/", methods=["GET"])
    def index():
        dep_path = app_config.get("DEPENDENCY_PATH", "data/dependency.ok")
        is_ready, duration_ms = check_readiness(dep_path)
        dep_state = "ok" if is_ready else "unreachable"
        req_id = getattr(request, "request_id", "local")
        rendered = render_template_string(
            HTML_TEMPLATE,
            version=app_config.get("APP_VERSION", "v1.0.0"),
            ready=is_ready,
            dependency_state=dep_state,
            duration_ms=duration_ms,
            request_id=req_id,
        )
        status_code = 200 if is_ready else 503
        return Response(rendered, status=status_code, mimetype="text/html")

    return app


application = create_app()

if __name__ == "__main__":
    cfg = get_env_config()
    application.run(host=cfg["HOST"], port=cfg["PORT"])
