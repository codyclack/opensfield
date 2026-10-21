import os

os.environ["OPENSFIELD_MOCK_DELAY"] = "0.1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import assets, runner  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_library(tmp_path, monkeypatch):
    monkeypatch.setattr(assets, "LIB", tmp_path / "lib")
    monkeypatch.setattr(assets, "INDEX", tmp_path / "lib" / "index.json")


def test_add_list_use_delete_roundtrip():
    r = client.post("/api/assets", files={"file": ("fox.png", b"\x89PNG", "image/png")}, data={"name": "Fox", "type": "Character"})
    assert r.status_code == 201 and r.json()["kind"] == "image" and r.json()["type"] == "Character"
    aid = r.json()["id"]
    assert [a["id"] for a in client.get("/api/assets").json()["items"]] == [aid]
    used = client.post(f"/api/assets/{aid}/use").json()
    assert (runner.UPLOADS / used["id"]).exists()
    job = client.post("/api/jobs", json={"feature_id": "image.bg-remove", "inputs": {"image": used["id"]}})
    assert job.status_code == 202
    assert client.delete(f"/api/assets/{aid}").status_code == 204
    assert client.get("/api/assets").json()["items"] == []


def test_rejects_unknown_type_and_bad_paths():
    assert client.post("/api/assets", files={"file": ("x.exe", b"x", "application/octet-stream")}).status_code == 415
    assert client.post("/api/assets/save", json={"url": "/outputs/../../etc/passwd"}).status_code in (404, 422)
    assert client.post("/api/assets/save", json={"url": "https://evil.example/x.png"}).status_code == 422


def test_save_example_into_library():
    r = client.post("/api/assets/save", json={"url": "/examples/char_a.png", "name": "Dancer", "type": "Prop"})
    assert r.status_code == 201 and r.json()["type"] == "Prop"
