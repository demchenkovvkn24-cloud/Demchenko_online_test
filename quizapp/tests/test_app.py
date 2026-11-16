from app import create_app
from config import TestConfig


def test_index_page():
    client = create_app(TestConfig).test_client()
    response = client.get("/")
    assert response.status_code == 200
