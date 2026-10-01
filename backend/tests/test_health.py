import pytest

pytestmark = pytest.mark.django_db


def test_health_reports_ready_database(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_reports_unavailable_database(client, monkeypatch):
    monkeypatch.setattr("core.api.database_ready", lambda: False)
    response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json() == {"status": "database-unavailable"}


def test_api_docs_are_hidden_in_production(client):
    assert client.get("/api/docs").status_code == 404
