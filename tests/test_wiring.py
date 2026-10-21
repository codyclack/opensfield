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
    src = WIRING[fid].get("files_from", fid) if fid in WIRING else fid
    return json.loads((ROOT / "features" / src / "workflow_api.json").read_text(encoding="utf-8"))


GRAPHED = sorted(f for f in WIRING if not WIRING[f].get("local"))  # local CPU effects have no workflow files


@pytest.mark.parametrize("fid", GRAPHED)
def test_every_wired_target_exists(fid):
    g = graph(fid)
    for spec in WIRING[fid]["inputs"]:
        if "node" not in spec:  # preset choices have no node; they write into apply_to
            assert spec["apply_to"] in {s["name"] for s in WIRING[fid]["inputs"] if "node" in s}
            assert set(spec["options"]) == set(spec["presets"]) and spec["default"] in spec["presets"]
            continue
        for t in [{"node": spec["node"], "field": spec["field"]}, *spec.get("also", [])]:
            assert t["node"] in g, f"{fid}: node {t['node']} missing"
            assert t["field"] in g[t["node"]]["inputs"], f"{fid}: {t['node']}.{t['field']} missing"
        if spec["kind"] in LOADER_FIELD:
            cls, field = LOADER_FIELD[spec["kind"]]
            assert g[spec["node"]]["class_type"] == cls and spec["field"] == field
        if spec["kind"] == "seed":
            assert "seed" in spec["field"] or spec["field"] == "value"  # ACE-Step's seed is a PrimitiveInt
    for node in WIRING[fid]["outputs"]:
        cls = g[node]["class_type"]
        assert cls.startswith("Save") or "Preview" in cls, f"{fid}: output {node} ({cls}) is not a Save/Preview node"


@pytest.mark.parametrize("fid", sorted(WIRING))
def test_manifest_matches_wiring_and_verification_is_backed_by_files(fid):
    m = json.loads((ROOT / "features" / fid / "manifest.json").read_text(encoding="utf-8"))
    assert m["workflow"]["inputs"] == json.loads(json.dumps(WIRING[fid]["inputs"])), "run scripts/build_registry.py"
    if WIRING[fid].get("verified_via"):  # "tested" is only allowed with a real example output on disk
        assert m["status"] == "tested" and m["workflow"]["verified"] is True
        assert WIRING[fid]["examples"] and all((ROOT / p).exists() for p in WIRING[fid]["examples"])
    else:
        assert m["status"] == "built" and m["workflow"]["verified"] is False


@pytest.mark.parametrize("fid", GRAPHED)
def test_ui_and_api_files_exist_and_no_unconverted_nodes(fid):
    d = ROOT / "features" / WIRING[fid].get("files_from", fid)
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


def test_preset_text_is_composed_and_sent_to_the_reused_workflow(monkeypatch):
    seen = run_with_stub(monkeypatch, "viral.effects", {"start_image": "s.png", "effect": "Vanish", "prompt": "a runner in red", "duration": 5})
    text = seen["wf"].json["398:376"]["inputs"]["value"]
    assert text.startswith("Use the provided start image as the first frame. ")
    assert "empty clothes to collapse" in text and text.endswith("a runner in red")
    assert seen["wf"].json["395"]["inputs"]["image"] == ("ASSET", "s.png")


def test_character_sheet_reuses_the_single_image_edit_workflow(monkeypatch):
    seen = run_with_stub(monkeypatch, "soul.character-sheet", {"image": "p.png", "prompt": ""})
    g = seen["wf"].json
    assert g["41"]["inputs"]["image"] == ("ASSET", "p.png")
    assert g["170:151"]["inputs"]["prompt"].startswith("Turn this into a character reference sheet")


def test_two_reference_module_feeds_both_loaders(monkeypatch):
    seen = run_with_stub(monkeypatch, "soul.cast", {"image": "a.png", "image_b": "b.png", "prompt": "Put both together"})
    g = seen["wf"].json
    assert g["470"]["inputs"]["image"] == ("ASSET", "a.png") and g["475"]["inputs"]["image"] == ("ASSET", "b.png")


def test_blank_optional_values_keep_template_defaults(monkeypatch):
    before = graph("soul.t2i")["57:13"]["inputs"]["width"]
    seen = run_with_stub(monkeypatch, "soul.t2i", {"prompt": "sneaker", "width": "", "height": None})
    assert seen["wf"].json["57:13"]["inputs"]["width"] == before
