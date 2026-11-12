# Local Startup & Operator Guide

## Prerequisites & Zero-State Assumptions
This guide assumes you are starting from a blank workstation without pre-existing project virtual environments or configured daemons. 

### Supported Environments
1. **Host-Based Execution (Linux, macOS, Windows WSL/PowerShell)**:
   - Python 3.12 (`python --version` >= 3.12.0)
   - Git (`git --version`)
   - GNU Make (or plain Bash for script execution)
   - `curl` for endpoint testing
2. **Containerized Execution**:
   - Docker Engine 24.0+ or Podman 4.0+

---

## Configuration Matrix
All runtime variables are loaded strictly from the environment with documented fallback defaults:

| Variable | Type | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `PORT` | Integer | `8080` | Port for the HTTP listener. Rejects invalid non-numeric or out-of-range values on startup. |
| `HOST` | String | `127.0.0.1` | Network interface binding. Set to `0.0.0.0` inside container environments. |
| `DEPENDENCY_PATH` | Path | `data/dependency.ok` | Relative or absolute path probed on every readiness check. |
| `APP_VERSION` | String | `v1.0.0` | Semantic version string returned in JSON telemetry and dashboard. |
| `LOG_LEVEL` | String | `INFO` | Standard logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## Path A: Native Host / Non-Docker Execution (Recommended)

### Step 1: Clone and Enter the Directory
```bash
git clone <repository_url> CS_cloud-computing-devops_Venkatesh_v1
cd CS_cloud-computing-devops_Venkatesh_v1
```

### Step 2: Establish an Isolated Python 3.12 Virtual Environment
```bash
python -m venv .venv
# On Linux / macOS / Git Bash:
source .venv/bin/activate
# On Windows PowerShell:
# .venv\Scripts\Activate.ps1
```

### Step 3: Install Exact Pinned Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Initialize Dependency State File
```bash
mkdir -p data
touch data/dependency.ok
```

### Step 5: Launch the Service
```bash
export PORT=8080
export HOST=127.0.0.1
export DEPENDENCY_PATH=data/dependency.ok
export APP_VERSION=v1.0.0
python -m app.main
```

### Step 6: Verify Endpoints (In another terminal)
```bash
# 1. Verify Health (Liveness)
curl -i http://127.0.0.1:8080/health

# 2. Verify Readiness (Dependency Accessible)
curl -i http://127.0.0.1:8080/ready

# 3. Simulate Dependency Outage
rm data/dependency.ok
curl -i http://127.0.0.1:8080/ready   # Returns 503
curl -i http://127.0.0.1:8080/health  # Returns 200

# 4. Restore Dependency
touch data/dependency.ok
curl -i http://127.0.0.1:8080/ready   # Returns 200

# 5. View Operator Dashboard
open http://127.0.0.1:8080/  # Or visit in web browser
```

---

## Path B: Automated Makefile Execution

```bash
# Build dependencies
make build

# Run unit and integration tests
make test

# Launch service
make run

# Execute automated clean-start verification sequence
make clean-start
```

---

## Path C: Multi-Stage Docker Execution

### Step 1: Build Image with Exact Pinned Base Tag
```bash
docker build --no-cache -t cs-status-service:v1.0.0 .
```

### Step 2: Run Non-Root Container
```bash
docker run -d \
  --name status-service \
  -p 8080:8080 \
  -e PORT=8080 \
  -e HOST=0.0.0.0 \
  -e APP_VERSION=v1.0.0 \
  cs-status-service:v1.0.0
```

### Step 3: Test Health and Readiness
```bash
curl -i http://127.0.0.1:8080/health
curl -i http://127.0.0.1:8080/ready
```

### Step 4: Simulate Failure Inside Container
```bash
docker exec -it status-service rm -f /app/data/dependency.ok
curl -i http://127.0.0.1:8080/ready   # Returns 503
curl -i http://127.0.0.1:8080/health  # Returns 200
docker exec -it status-service touch /app/data/dependency.ok
curl -i http://127.0.0.1:8080/ready   # Recovers to 200
```
