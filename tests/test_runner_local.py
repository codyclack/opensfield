"""run_comfyui: a tool run against a self-hosted ComfyUI over its classic HTTP API (faked here, no network)."""
import io
import json

from app import runner
from app.registry import load_features


class FakeComfy:
    def __init__(self):
        self.prompt = None
        self.uploads = []

    def __call__(self, req, timeout=None):
        path = req.full_url.removeprefix("http://gpu:8188")
        if path == "/upload/image":
            self.uploads.append(req.data)
            body = {"name": "start.png", "subfolder": "", "type": "input"}
        elif path == "/prompt":
            self.prompt = json.loads(req.data)["prompt"]
            body = {"prompt_id": "p1"}
        elif path == "/history/p1":
            body = {"p1": {"status": {"status_str": "success", "completed": True, "messages": []},
                           "outputs": {"26": {"images": [{"filename": "clip.mp4", "subfolder": "video", "type": "output"}], "animated": [True]}}}}
        elif path.startswith("/view?"):
            return io.BytesIO(b"MP4")
        else:
            raise AssertionError(path)
        return io.BytesIO(json.dumps(body).encode())


def test_self_hosted_detection():
    assert runner._self_hosted("http://127.0.0.1:8188")
    assert not runner._self_hosted("https://cloud.comfy.org")
    assert not runner._self_hosted("")


def test_run_comfyui_sets_inputs_and_fetches_outputs(monkeypatch, tmp_path):
    feat = next(f for f in load_features() if f["id"] == "app.bullet-time-scene-open")
    monkeypatch.setattr(runner, "OUTPUTS", tmp_path)
    monkeypatch.setattr(runner, "UPLOADS", tmp_path / "uploads")
    (tmp_path / "uploads").mkdir()
    (tmp_path / "uploads" / "me.png").write_bytes(b"PNG")
    fake = FakeComfy()
    monkeypatch.setattr(runner.urllib.request, "urlopen", fake)
    outs = runner.run_comfyui("http://gpu:8188", feat, {"id": "j1", "inputs": {"image": "me.png", "prompt": "snow falls", "seed": 7}}, lambda **kw: None)
    assert fake.prompt["40"]["inputs"]["image"] == "start.png"
    assert fake.prompt["8"]["inputs"]["text"].endswith("snow falls")  # the app's prompt prefix comes first
    assert fake.prompt["18"]["inputs"]["noise_seed"] == 7
    assert outs == [{"url": "/outputs/j1/26_0_clip.mp4", "kind": "video", "name": "26_0_clip.mp4", "mock": False}]
    assert (tmp_path / "j1" / "26_0_clip.mp4").read_bytes() == b"MP4"
