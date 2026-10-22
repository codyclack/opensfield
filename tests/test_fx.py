"""Local CPU effects. Skipped when the fx extra (numpy, opencv, imageio-ffmpeg) is not installed."""
import pytest

np = pytest.importorskip("numpy")
cv2 = pytest.importorskip("cv2")
pytest.importorskip("imageio_ffmpeg")

from app import fx  # noqa: E402


def frame(h=72, w=128, seed=0):
    rng = np.random.default_rng(seed)
    base = np.linspace(0, 255, w, dtype=np.uint8)[None, :, None].repeat(h, 0).repeat(3, 2)
    return np.clip(base.astype(int) + rng.integers(-20, 20, base.shape), 0, 255).astype(np.uint8)


@pytest.mark.parametrize("mode", sorted(fx.MODES))
def test_every_mode_returns_a_changed_frame_of_the_same_shape(mode):
    f = frame()
    out = fx.MODES[mode](f, 3)
    assert out.shape == f.shape and out.dtype == np.uint8
    assert not np.array_equal(out, f)


@pytest.mark.parametrize("mode", sorted(fx.MODES))
def test_effects_are_deterministic_per_frame_index(mode):
    f = frame()
    assert np.array_equal(fx.MODES[mode](f, 7), fx.MODES[mode](f, 7))


def test_thermal_palettes_differ_and_black_hot_inverts_white_hot():
    f = frame()
    white, black = fx.thermal(f, "white-hot", 1), fx.thermal(f, "black-hot", 1)
    assert abs(float(white.mean()) + float(black.mean()) - 255) < 12  # inverses, up to noise
    assert not np.array_equal(fx.thermal(f, "rainbow", 1), fx.thermal(f, "iron", 1))
    with pytest.raises(ValueError):
        fx.thermal(f, "plaid")


def _make_clip(path, n=8):
    import subprocess
    import imageio_ffmpeg
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "128x72", "-r", "12",
           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(seed=i).tobytes())
    p.stdin.close()
    assert p.wait() == 0


def test_app_runs_a_local_effect_job_for_real(tmp_path):
    import time
    from fastapi.testclient import TestClient
    from app.main import app
    clip = tmp_path / "c.mp4"
    _make_clip(clip)
    c = TestClient(app)
    up = c.post("/api/uploads", files={"file": ("c.mp4", clip.read_bytes(), "video/mp4")}).json()
    job = c.post("/api/jobs", json={"feature_id": "matchcut.thermal", "inputs": {"video": up["id"], "palette": "rainbow"}}).json()
    for _ in range(100):
        j = c.get(f"/api/jobs/{job['id']}").json()
        if j["status"] in ("done", "error"):
            break
        time.sleep(0.1)
    assert j["status"] == "done", j.get("error")
    out = j["outputs"][0]
    assert out["kind"] == "video" and out["mock"] is False and out["name"] == "rainbow.mp4"
    assert c.get(out["url"]).status_code == 200


def test_process_video_round_trip(tmp_path):
    import imageio_ffmpeg
    import subprocess
    src, dst = tmp_path / "in.mp4", tmp_path / "out.mp4"
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "128x72", "-r", "12",
           "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(src)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(12):
        p.stdin.write(frame(seed=i).tobytes())
    p.stdin.close()
    assert p.wait() == 0
    seen = []
    fx.process_video(src, dst, "vhs", progress=seen.append)
    cap = cv2.VideoCapture(str(dst))
    assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) == 12 and int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) == 128
    assert seen and seen[-1] <= 0.99
    with pytest.raises(ValueError):
        fx.process_video(src, dst, "nope")


def _ctx(text="one\ntwo\nthree", n=30):
    return {"text": text, "fps": 24.0, "n": n}


def test_text_looks_draw_and_progress():
    f = frame(h=180, w=320)
    cap_a, cap_b = fx.captions(f, 0, _ctx()), fx.captions(f, 29, _ctx())
    assert not np.array_equal(cap_a, f) and not np.array_equal(cap_a, cap_b)  # a different line later
    t_early, t_late = fx.typewriter(f, 2, _ctx("hello world this is typed", 60)), fx.typewriter(f, 50, _ctx("hello world this is typed", 60))
    green = lambda im: int(((im[..., 1] > 200) & (im[..., 2] < 160) & (im[..., 0] < 170)).sum())  # noqa: E731  (the text colour)
    assert green(t_late) > green(t_early)  # more typed text on screen later
    w_early, w_late = fx.wordstack(f, 0, _ctx("a b c d", 40)), fx.wordstack(f, 39, _ctx("a b c d", 40))
    assert int((w_late != w_early).sum()) > 0


def test_deflicker_reduces_brightness_jitter():
    rng = np.random.default_rng(1)
    base = frame()
    frames = [np.clip(base.astype(np.float32) * rng.uniform(0.7, 1.3), 0, 255).astype(np.uint8) for _ in range(30)]
    means = np.array([float(f.mean()) for f in frames])
    gains = fx._gains_from_means(means)
    out = [fx.deflicker(f, i, {"gains": gains}) for i, f in enumerate(frames)]
    after = np.array([float(o.mean()) for o in out])
    assert np.std(np.diff(after)) < 0.4 * np.std(np.diff(means))


def test_text_looks_refuse_empty_text(tmp_path):
    clip = tmp_path / "c.mp4"
    _make_clip(clip)
    with pytest.raises(ValueError):
        fx.process_video(clip, tmp_path / "o.mp4", "captions", text="  \n ")
    fx.process_video(clip, tmp_path / "o.mp4", "typewriter", text="hi there")
    assert (tmp_path / "o.mp4").exists()

def test_website_builder_writes_a_page(tmp_path):
    from app import fx_tools
    (tmp_path / "up").mkdir()
    made = fx_tools.website({"name": "Puddle <Runners>", "tagline": "Wet nights", "features": "Grip: holds on stone", "style": "Light"},
                            tmp_path / "up", tmp_path / "out", lambda p: None)
    page = (tmp_path / "out" / made[0][0]).read_text(encoding="utf-8")
    assert made == [("site/index.html", "html")] and "Puddle &lt;Runners&gt;" in page and "Grip" in page


def test_subject_box_finds_the_object():
    from app import fx_tools
    img = np.full((200, 120, 3), 240, np.uint8)
    img[60:140, 30:90] = (20, 30, 200)
    x, y, w, h = fx_tools._subject_box(img)
    assert abs(x - 30) < 6 and abs(y - 60) < 6 and abs(w - 60) < 10 and abs(h - 80) < 10
    hx, hy, hw, hh = fx_tools._head(img)
    assert 40 <= hx + hw / 2 <= 80 and hy <= 70
