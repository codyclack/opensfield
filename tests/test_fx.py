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
