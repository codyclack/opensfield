"""The cloud smoke script must be able to build valid inputs for every tested module (no network, no key)."""
import importlib.util
import sys

from app import runner
from app.registry import ROOT, load_features


def load_smoke():
    spec = importlib.util.spec_from_file_location("smoke_cloud", ROOT / "scripts" / "smoke_cloud.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["smoke_cloud"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_smoke_inputs_exist_for_every_tested_cloud_module(tmp_path, monkeypatch):
    smoke = load_smoke()
    monkeypatch.setattr(runner, "UPLOADS", tmp_path)
    n = 0
    for f in load_features():
        if f["status"] != "tested" or f.get("local") or not f.get("runnable"):
            continue
        vals = smoke.inputs_for(f)
        for spec in f["inputs"]:
            if spec.get("required"):
                assert vals.get(spec["name"]), f"{f['id']}: no smoke value for required input {spec['name']}"
            if spec["kind"] in ("image", "video", "audio") and spec["name"] in vals:
                assert (tmp_path / vals[spec["name"]]).exists()
        n += 1
    assert n >= 30
