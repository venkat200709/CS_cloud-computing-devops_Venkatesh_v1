# Operations & Rollback Runbook

## Scope & Objective
This runbook defines the concrete operational standard for incident mitigation, root-cause diagnosis, and rapid rollback execution for the CareerSwami Status Service.

Every platform deployment is a two-way door only when deterministic rollback steps are documented, tested, and rehearsed before production release.

---

## Triage & Incident Classification Matrix

| Alert / Symptom | Detection Signal | Immediate Impact | Mitigating Action |
| :--- | :--- | :--- | :--- |
| **Dependency Unreachable** | `/ready` returns `503 Service Unavailable`, log emits `outcome: unreachable` | Upstream load balancer drops replica from active pool. | Check volume mount or file state at `DEPENDENCY_PATH`. Recreate missing flag if valid. |
| **Process Crash / Panic** | `/health` fails with connection refused, container restarts | Pod enters CrashLoopBackOff. | Check stdout logs for unhandled exception or port conflict. |
| **Invalid Port Config** | Process aborts on startup with `ValueError: Invalid PORT` | Container immediately terminates with exit code 1. | Correct `PORT` variable in deployment manifest or `.env` to valid integer (1-65535). |
| **Bad Release Detected** | Regressions or errors discovered in version `v1.0.1` | Users or services receive degraded responses. | Execute Rollback Procedure to `v1.0.0` immediately. |

---

## Concrete Rollback Procedure (Step-by-Step)

### Context
- **Faulty Target**: Release tagged `v1.0.1` / Image tag `cs-status-service:v1.0.1`.
- **Known Stable Target**: Release tagged `v1.0.0` / Image tag `cs-status-service:v1.0.0`.

### Procedure A: Git Source Rollback
```bash
# 1. Fetch all release tags
git fetch --tags

# 2. Checkout the verified stable release
git checkout v1.0.0

# 3. Re-verify the test suite
pytest -v

# 4. Restart the service process
make run
```

### Procedure B: Containerized Rollback
```bash
# 1. Stop and remove the faulty v1.0.1 container
docker stop status-service
docker rm status-service

# 2. Immediately spin up the previous immutable image v1.0.0
docker run -d \
  --name status-service \
  -p 8080:8080 \
  -e PORT=8080 \
  -e HOST=0.0.0.0 \
  -e APP_VERSION=v1.0.0 \
  cs-status-service:v1.0.0

# 3. Confirm container health status
docker inspect --format='{{json .State.Health.Status}}' status-service
```

### Post-Rollback Verification Checklist
Execute following verification suite after rollback to certify service recovery:
```bash
# 1. Verify version returns v1.0.0
curl -s http://127.0.0.1:8080/health | grep '"version":"v1.0.0"'

# 2. Verify readiness returns 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/ready | grep "200"

# 3. Verify HTML dashboard indicates healthy state
curl -s http://127.0.0.1:8080/ | grep "READY (200)"
```

---

## Rollback Limits & Persistent State Caveat
> [!WARNING]
> **Container vs Storage Decoupling**: Reverting a container image or git tag only rolls back the application binary and memory footprint. It **does not** automatically reverse schema mutations, file deletions, or external storage states.
>
> If an incident involves corrupted or removed persistent dependencies (such as `DEPENDENCY_PATH` being deleted on the host volume), rolling back code from `v1.0.1` to `v1.0.0` will still fail with `503` until the backing dependency file/volume is restored. True operational resilience requires pairing image rollbacks with storage snapshot restorations.
