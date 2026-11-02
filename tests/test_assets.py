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


def test_library_uploads_are_capped(monkeypatch):
    monkeypatch.setenv("OPENSFIELD_MAX_UPLOAD_MB", "1")
    big = b"\0" * ((1 << 20) + 1)
    assert client.post("/api/assets", files={"file": ("big.png", big, "image/png")}).status_code == 413
    assert client.get("/api/assets").json()["items"] == [] and list(assets.LIB.iterdir()) == []
    r = client.post("/api/assets", files={"file": ("maya.png", b"\x89PNG", "image/png")}).json()
    assert client.post(f"/api/assets/{r['id']}/images", files={"file": ("side.png", big, "image/png")}).status_code == 413
    assert len(client.get("/api/assets").json()["items"][0]["images"]) == 1 and len(list(assets.LIB.glob("*.png"))) == 1


def test_save_example_into_library():
    r = client.post("/api/assets/save", json={"url": "/examples/char_a.png", "name": "Dancer", "type": "Prop"})
    assert r.status_code == 201 and r.json()["type"] == "Prop"


def test_elements_hold_several_reference_images():
    r = client.post("/api/assets", files={"file": ("maya.png", b"\x89PNG", "image/png")}, data={"name": "Maya", "type": "Character"}).json()
    r2 = client.post(f"/api/assets/{r['id']}/images", files={"file": ("side.png", b"\x89PNG2", "image/png")}).json()
    assert len(r2["images"]) == 2
    up = client.post(f"/api/assets/{r['id']}/use?image=1").json()
    assert (runner.UPLOADS / up["id"]).read_bytes() == b"\x89PNG2"


def test_concurrent_reference_images_get_distinct_files():
    import threading
    el = client.post("/api/assets", files={"file": ("maya.png", b"\x89PNG", "image/png")}).json()
    threads = [threading.Thread(target=client.post, args=(f"/api/assets/{el['id']}/images",), kwargs={"files": {"file": (f"{i}.png", b"\x89PNG", "image/png")}})
               for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    files = [im["file"] for im in client.get("/api/assets").json()["items"][0]["images"]]
    assert len(files) == len(set(files)) == 3 and all((assets.LIB / f).exists() for f in files)


def test_index_holds_up_under_concurrent_adds_lists_and_uses(tmp_path, monkeypatch):
    import threading
    import time
    monkeypatch.setattr(runner, "UPLOADS", tmp_path / "uploads")
    c = TestClient(app, raise_server_exceptions=False)
    first = c.post("/api/assets", files={"file": ("a.png", b"\x89PNG", "image/png")}).json()["id"]
    stop, bad = time.time() + 3, []

    def adder():
        while time.time() < stop:
            if (s := c.post("/api/assets", files={"file": ("b.png", b"\x89PNG", "image/png")}).status_code) != 201:
                bad.append(("add", s))

    def reader():
        while time.time() < stop:
            r = c.get("/api/assets")
            if r.status_code != 200 or not r.json()["items"]:  # never an error, never an emptied library
                bad.append(("list", r.status_code))
            if (s := c.post(f"/api/assets/{first}/use").status_code) != 200:
                bad.append(("use", s))

    threads = [threading.Thread(target=f) for f in (adder, adder, reader, reader)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert bad == []
