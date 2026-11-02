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
    assert c["mode"] == "mock" and c["partner_enabled"] is True


def test_partner_model_tools_listed_and_run_in_mock():
    feats = {f["id"]: f for f in client.get("/api/features").json()}
    models = [f for f in feats.values() if f["id"].startswith("model.")]
    assert len(models) >= 40 and "soul.t2i" in feats
    assert all(f["runnable"] and f.get("group") for f in models)
    r = client.post("/api/jobs", json={"feature_id": "model.bfl-flux3-t2i", "inputs": {"prompt": "a red fox"}})
    assert r.status_code == 202 and wait(r.json()["id"])["status"] == "done"


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


def test_uploads_take_media_only_and_always_download():
    for name, mime in (("x.html", "text/html"), ("x.svg", "image/svg+xml")):
        assert client.post("/api/uploads", files={"file": (name, b"<script>alert(1)</script>", mime)}).status_code == 415
    up = client.post("/api/uploads", files={"file": ("x.png", b"\x89PNG", "image/png")})
    assert up.status_code == 200
    r = client.get(up.json()["url"])
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["content-disposition"] == "attachment"
    j = wait(client.post("/api/jobs", json={"feature_id": "soul.t2i", "inputs": {"prompt": "x"}}).json()["id"])
    out = client.get(j["outputs"][0]["url"])  # job outputs (mock .svg, website pages) still render in place
    assert out.status_code == 200 and "content-disposition" not in out.headers


def test_upload_rejects_control_characters_in_the_extension():
    # a bare LF survives multipart parsing into the filename: "x.\nevil" -> extension ".\nevil"
    body = b'--b\r\nContent-Disposition: form-data; name="file"; filename="x.\nevil"\r\nContent-Type: image/png\r\n\r\n\x89PNG\r\n--b--\r\n'
    r = client.post("/api/uploads", content=body, headers={"Content-Type": "multipart/form-data; boundary=b"})
    assert r.status_code == 415


def test_upload_size_cap_leaves_no_partial_file(monkeypatch):
    from app import runner
    monkeypatch.setenv("OPENSFIELD_MAX_UPLOAD_MB", "1")
    before = set(runner.UPLOADS.iterdir())
    r = client.post("/api/uploads", files={"file": ("big.png", b"\0" * ((1 << 20) + 1), "image/png")})
    assert r.status_code == 413 and set(runner.UPLOADS.iterdir()) == before
    ok = client.post("/api/uploads", files={"file": ("fits.png", b"\0" * (1 << 20), "image/png")})
    assert ok.status_code == 200 and (runner.UPLOADS / ok.json()["id"]).stat().st_size == 1 << 20


def test_upload_id_cannot_be_a_path():
    r = client.post("/api/jobs", json={"feature_id": "image.bg-remove", "inputs": {"image": "../../etc/passwd"}})
    assert r.status_code == 422


def test_examples_are_exposed_and_served():
    f = client.get("/api/features/genjutsu.motion-control").json()
    assert f["examples"] and "workflow" not in f
    for url in f["examples"]:
        assert client.get("/" + url).status_code == 200


def test_access_key_gate(monkeypatch):
    monkeypatch.setenv("OPENSFIELD_ACCESS_KEY", "s3cret")
    c = TestClient(app)
    assert c.get("/api/config").status_code == 401
    assert c.get("/api/config?key=wrong").status_code == 401
    ok = c.get("/api/config?key=s3cret")
    assert ok.status_code == 200 and "osf" in ok.cookies
    assert c.get("/api/config").status_code == 200  # cookie now carries it


def _startup_output(**env) -> str:
    import subprocess
    import sys
    from pathlib import Path
    env = {k: v for k, v in os.environ.items() if k != "OPENSFIELD_ACCESS_KEY"} | env
    return subprocess.run([sys.executable, "-c", "import app.main"], env=env, cwd=Path(__file__).parents[1],
                          capture_output=True, text=True, timeout=60).stdout


def test_startup_warns_when_the_gate_is_off():
    assert "WARNING: OPENSFIELD_ACCESS_KEY is not set" in _startup_output()


def test_job_cap(monkeypatch):
    monkeypatch.setenv("OPENSFIELD_MAX_JOBS", "1")
    r = client.post("/api/jobs", json={"feature_id": "soul.t2i", "inputs": {"prompt": "x"}})
    assert r.status_code == 429


def test_text_only_feature_runs():
    r = client.post("/api/jobs", json={"feature_id": "soul.t2i", "inputs": {"prompt": "a sneaker"}})
    assert wait(r.json()["id"])["status"] == "done"


def test_jobs_persist_and_delete():
    from app import main
    r = client.post("/api/jobs", json={"feature_id": "model.bfl-flux3-t2i", "inputs": {"prompt": "a fox"}})
    jid = r.json()["id"]
    assert wait(jid)["status"] == "done"
    saved = main._load_jobs()
    assert jid in saved and saved[jid]["kind"] == "image" and "outputs" not in str(main.JOBS_FILE).split("osf_jobs_")[0][-3:]
    assert client.delete(f"/api/jobs/{jid}").status_code == 204
    assert jid not in main._load_jobs()


def test_favorites_and_projects():
    p = client.post("/api/projects", json={"name": "Short film"}).json()
    assert any(x["id"] == p["id"] for x in client.get("/api/projects").json())
    r = client.post("/api/jobs", json={"feature_id": "model.bfl-flux3-t2i", "inputs": {"prompt": "a fox", "_studio": "cinema"}, "project": p["id"]})
    jid = r.json()["id"]
    assert wait(jid)["project"] == p["id"]
    assert client.patch(f"/api/jobs/{jid}", json={"fav": True}).json()["fav"] is True
    assert client.delete(f"/api/projects/{p['id']}").status_code == 204
    assert client.get(f"/api/jobs/{jid}").json()["project"] is None


def test_blog_lists_and_renders_posts():
    posts = client.get("/api/blog").json()
    assert len(posts) >= 5 and all(p["title"] and p["category"] and p["slug"] for p in posts)
    post = client.get(f"/api/blog/{posts[0]['slug']}").json()
    assert post["body"].strip() and post["meta"]["minutes"] >= 1
    assert client.get("/api/blog/..%2Fapp%2Fmain").status_code == 404


def test_apps_catalog_points_at_runnable_tools():
    data = client.get("/api/apps").json()
    feats = {f["id"]: f for f in client.get("/api/features").json()}
    assert len(data["apps"]) >= 80 and len(data["categories"]) == 8
    assert all(a["feature"] in feats and feats[a["feature"]]["runnable"] for a in data["apps"])
    assert not any(a["slug"] == "skibidi" for a in data["apps"])  # left out: built on someone else's IP
