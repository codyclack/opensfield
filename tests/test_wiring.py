"""Static checks that the wired workflows match their form specs. No ComfyUI, no network."""
import json
import sys
import types
from pathlib import Path

import pytest

from app import runner
from app.registry import ROOT, load_features
from registry.wiring import WIRING

LOADER_FIELD = {"image": ("LoadImage", "image"), "video": ("LoadVideo", "file"), "audio": ("LoadAudio", "audio")}


def graph(fid):
    return json.loads((ROOT / "features" / fid / "workflow_api.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("fid", sorted(WIRING))
def test_every_wired_target_exists(fid):
    g = graph(fid)
    for spec in WIRING[fid]["inputs"]:
        for t in [{"node": spec["node"], "field": spec["field"]}, *spec.get("also", [])]:
            assert t["node"] in g, f"{fid}: node {t['node']} missing"
            assert t["field"] in g[t["node"]]["inputs"], f"{fid}: {t['node']}.{t['field']} missing"
        if spec["kind"] in LOADER_FIELD:
            cls, field = LOADER_FIELD[spec["kind"]]
            assert g[spec["node"]]["class_type"] == cls and spec["field"] == field
        if spec["kind"] == "seed":
            assert "seed" in spec["field"]
    for node in WIRING[fid]["outputs"]:
        assert g[node]["class_type"].startswith("Save"), f"{fid}: output {node} is not a Save node"


@pytest.mark.parametrize("fid", sorted(WIRING))
def test_manifest_matches_wiring_and_verification_is_backed_by_files(fid):
    m = json.loads((ROOT / "features" / fid / "manifest.json").read_text(encoding="utf-8"))
    assert m["workflow"]["inputs"] == json.loads(json.dumps(WIRING[fid]["inputs"])), "run scripts/build_registry.py"
    if WIRING[fid].get("verified_via"):  # "tested" is only allowed with a real example output on disk
        assert m["status"] == "tested" and m["workflow"]["verified"] is True
        assert WIRING[fid]["examples"] and all((ROOT / p).exists() for p in WIRING[fid]["examples"])
    else:
        assert m["status"] == "built" and m["workflow"]["verified"] is False


@pytest.mark.parametrize("fid", sorted(WIRING))
def test_ui_and_api_files_exist_and_no_unconverted_nodes(fid):
    d = ROOT / "features" / fid
    assert (d / "workflow_ui.json").exists()
    assert not any(n["class_type"] in ("Note", "MarkdownNote", "PrimitiveNode") for n in graph(fid).values())


class FakeWF:
    def __init__(self, g):
        self.json = g

    def set_input(self, node, field, value):
        self.json[node]["inputs"][field] = value


class FakeResult:
    def __init__(self, asked):
        self.asked = asked

    def get_outputs(self, node):
        self.asked.append(node)
        return []


def run_with_stub(monkeypatch, fid, inputs):
    seen = {"asked": []}

    class FakeComfy:
        def __init__(self, api_key=None):
            self.workflows = types.SimpleNamespace(from_file=lambda p: seen.setdefault("wf", FakeWF(json.loads(Path(p).read_text(encoding="utf-8")))))
            self.assets = types.SimpleNamespace(from_file=lambda p: ("ASSET", Path(p).name))

        def run(self, wf):
            return FakeResult(seen["asked"])

    monkeypatch.setitem(sys.modules, "comfy_sdk", types.SimpleNamespace(Comfy=FakeComfy))
    monkeypatch.setenv("COMFY_API_KEY", "test")
    feature = next(f for f in load_features() if f["id"] == fid)
    runner.run_comfy(feature, {"id": "t1", "inputs": inputs}, lambda **kw: None)
    return seen


def test_motion_control_sets_the_right_nodes(monkeypatch):
    seen = run_with_stub(monkeypatch, "genjutsu.motion-control", {
        "character": "c.png", "driving_video": "d.mp4", "character_prompt": "a robot", "motion_prompt": "dancing", "seed": 0})
    g = seen["wf"].json
    assert g["189"]["inputs"]["image"] == ("ASSET", "c.png") and g["240"]["inputs"]["file"] == ("ASSET", "d.mp4")
    assert g["605"]["inputs"]["value"] == "a robot" and g["604"]["inputs"]["value"] == "dancing"
    assert g["261:19"]["inputs"]["noise_seed"] > 0  # seed 0 means random
    assert seen["asked"] == ["246", "292"]


def test_camera_rig_sets_both_seeds_and_casts_numbers(monkeypatch):
    seen = run_with_stub(monkeypatch, "cinema.camera-rig", {"start_image": "s.png", "prompt": "dolly in", "duration": 7.0, "seed": 123,
                                                            "aspect": "9:16 (Portrait Widescreen)"})
    g = seen["wf"].json
    assert g["398:338"]["inputs"]["noise_seed"] == g["398:339"]["inputs"]["noise_seed"] == 123
    assert g["398:362"]["inputs"]["value"] == 7 and isinstance(g["398:362"]["inputs"]["value"], int)
    assert g["403"]["inputs"]["aspect_ratio"] == "9:16 (Portrait Widescreen)"


def test_blank_optional_values_keep_template_defaults(monkeypatch):
    before = graph("soul.t2i")["57:13"]["inputs"]["width"]
    seen = run_with_stub(monkeypatch, "soul.t2i", {"prompt": "sneaker", "width": "", "height": None})
    assert seen["wf"].json["57:13"]["inputs"]["width"] == before
