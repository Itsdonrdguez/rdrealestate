from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_property_search_rejects_unbounded_page_size() -> None:
    response = client.get("/api/properties", params={"page_size": 101})
    assert response.status_code == 422


def test_property_search_rejects_negative_value_filter() -> None:
    response = client.get("/api/properties", params={"min_assessed_value": -1})
    assert response.status_code == 422
