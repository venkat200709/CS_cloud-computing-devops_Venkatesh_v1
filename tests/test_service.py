import os
import pytest
from app.main import create_app, validate_port


@pytest.fixture
def temp_dep_file(tmp_path):
    f = tmp_path / "dependency.ok"
    f.write_text("ok")
    return str(f)


@pytest.fixture
def app_with_dep(temp_dep_file):
    app = create_app({"DEPENDENCY_PATH": temp_dep_file, "APP_VERSION": "v1.0.0"})
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app_with_dep):
    return app_with_dep.test_client()


def test_health_returns_200_and_version(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "version": "v1.0.0"}


def test_ready_returns_200_when_dependency_present(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json() == {"ready": True, "dependency": "ok"}


def test_ready_returns_503_when_dependency_removed(client, temp_dep_file):
    os.remove(temp_dep_file)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.get_json() == {"ready": False, "dependency": "unreachable"}


def test_ready_recovers_when_dependency_restored(client, temp_dep_file):
    if os.path.exists(temp_dep_file):
        os.remove(temp_dep_file)
    response_fail = client.get("/ready")
    assert response_fail.status_code == 503
    with open(temp_dep_file, "w") as f:
        f.write("restored")
    response_ok = client.get("/ready")
    assert response_ok.status_code == 200
    assert response_ok.get_json() == {"ready": True, "dependency": "ok"}


def test_health_remains_200_when_ready_fails(client, temp_dep_file):
    if os.path.exists(temp_dep_file):
        os.remove(temp_dep_file)
    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 503
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.get_json()["status"] == "ok"


def test_ready_fails_when_path_is_directory(tmp_path):
    dir_path = tmp_path / "sub_dir"
    dir_path.mkdir()
    app = create_app({"DEPENDENCY_PATH": str(dir_path)})
    client = app.test_client()
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.get_json() == {"ready": False, "dependency": "unreachable"}


def test_root_status_page_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "CareerSwami Service Monitor" in response.get_data(as_text=True)
    assert "READY (200)" in response.get_data(as_text=True)


def test_invalid_port_validation():
    with pytest.raises(ValueError):
        validate_port("invalid_port")
    with pytest.raises(ValueError):
        validate_port("0")
    with pytest.raises(ValueError):
        validate_port("70000")
    assert validate_port("8080") == 8080


def test_request_id_header(client):
    response = client.get("/health", headers={"X-Request-ID": "custom-uuid-1234"})
    assert response.headers.get("X-Request-ID") == "custom-uuid-1234"
    auto_response = client.get("/health")
    assert auto_response.headers.get("X-Request-ID") is not None
