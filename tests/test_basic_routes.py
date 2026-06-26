from fastapi.testclient import TestClient

from app.main import app


def test_core_pages_render():
    with TestClient(app) as client:
        for path in ["/dashboard", "/process-flow", "/equipment", "/alarms", "/reports", "/diagnostics", "/scenarios", "/playback"]:
            response = client.get(path)
            assert response.status_code == 200, path


def test_core_apis_render():
    with TestClient(app) as client:
        for path in ["/api/state", "/api/health", "/api/scenarios", "/api/playback/summary"]:
            response = client.get(path)
            assert response.status_code == 200, path
