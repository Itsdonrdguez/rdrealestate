from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_property_search_rejects_unbounded_page_size() -> None:
    response = client.get("/api/properties", params={"page_size": 101})
    assert response.status_code == 422


def test_property_search_rejects_negative_value_filter() -> None:
    response = client.get("/api/properties", params={"min_assessed_value": -1})
    assert response.status_code == 422


def test_property_detail_rejects_invalid_uuid() -> None:
    response = client.get("/api/properties/not-a-uuid")
    assert response.status_code == 422


def test_property_map_requires_bounding_box() -> None:
    response = client.get("/api/properties/map")
    assert response.status_code == 422


def test_property_map_rejects_reversed_bounding_box() -> None:
    response = client.get(
        "/api/properties/map",
        params={"west": -76, "south": 39, "east": -77, "north": 38},
    )
    assert response.status_code == 422
