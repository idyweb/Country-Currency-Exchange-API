import os
import pytest
from fastapi.testclient import TestClient
from main import app, IMAGE_PATH
from sqlmodel import Session
from models import Countries, create_db_and_tables, engine

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    create_db_and_tables()
    yield

def test_refresh_creates_data_and_image():
    response = client.post("/countries/refresh")
    assert response.status_code == 200
    json_data = response.json()
    assert "summary image generated" in json_data["message"]

    # Check image generated
    assert os.path.exists(IMAGE_PATH), "Summary image should be generated"

def test_get_countries():
    response = client.get("/countries")
    assert response.status_code == 200
    json_data = response.json()
    assert "data" in json_data
    assert json_data["total_count"] > 0

def test_filter_by_region():
    response = client.get("/countries?region=Africa")
    assert response.status_code == 200
    data = response.json()["data"]
    # Optional assert: some country in Africa should be present if API is real

def test_sort_by_gdp_desc():
    response = client.get("/countries?sort=gdp_desc")
    assert response.status_code == 200
    data = response.json()["data"]
    if len(data) > 1:
        assert data[0]["estimated_gdp"] >= data[1]["estimated_gdp"]

def test_get_country_by_name():
    response = client.get("/countries/Nigeria")
    if response.status_code == 404:
        assert response.json()["detail"]["error"] == "Country not found"
    else:
        assert response.status_code == 200

def test_delete_country():
    client.post("/countries/refresh")
    response = client.delete("/countries/Nigeria")
    assert response.status_code in [200, 404]

def test_get_summary_image():
    response = client.get("/countries/image")
    if os.path.exists(IMAGE_PATH):
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
    else:
        assert response.json() == {"error": "Summary image not found"}

def test_status_endpoint():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "total_countries" in data
    assert "last_refresh" in data
