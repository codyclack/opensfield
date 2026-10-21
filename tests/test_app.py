import os
import time

os.environ["OPENSFIELD_MOCK_DELAY"] = "0.1"
os.environ.pop("OPENSFIELD_PARTNER", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def wait(job_id, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        j = client.get(f"/api/jobs/{job_id}").json()
        if j["status"] in ("done", "error"):
            return j
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_config_is_mock():
    c = client.get("/api/config").json()
    assert c["mode"] == "mock" and c["partner_enabled"] is False


def test_partner_hidden_and_blocked():
    ids = {f["id"] for f in client.get("/api/features").json()}
    assert "image.partner-roster" not in ids and "soul.t2i" in ids
    r = client.post("/api/jobs", json={"feature_id": "image.partner-roster", "inputs": {}})
    assert r.status_code == 403


def test_every_feature_has_a_form():
    for f in client.get("/api/features").json():
        assert f["inputs"] or f["tier"] == "C", f["id"]


def test_required_media_validated():
    r = client.post("/api/jobs", json={"feature_id": "genjutsu.motion-control", "inputs": {}})
    assert r.status_code == 422 and "Character image" in r.json()["detail"]


def test_upload_and_mock_job_end_to_end():
    up = client.post("/api/uploads", files={"file": ("a.png", b"\x89PNG", "image/png")}).json()
    r = client.post("/api/jobs", json={"feature_id": "image.bg-remove", "inputs": {"image": up["id"]}})
    assert r.status_code == 202
    j = wait(r.json()["id"])
    assert j["status"] == "done" and j["outputs"][0]["mock"] is True
    assert client.get(j["outputs"][0]["url"]).status_code == 200


def test_upload_id_cannot_be_a_path():
    r = client.post("/api/jobs", json={"feature_id": "image.bg-remove", "inputs": {"image": "../../etc/passwd"}})
    assert r.status_code == 422


def test_text_only_feature_runs():
    r = client.post("/api/jobs", json={"feature_id": "soul.t2i", "inputs": {"prompt": "a sneaker"}})
    assert wait(r.json()["id"])["status"] == "done"
