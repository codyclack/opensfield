"""Convert features/<id>/workflow_ui.json -> workflow_api.json (what comfy-sdk needs).

comfy-sdk only accepts API-format graphs, but the official templates are UI-format
and use subgraphs, so conversion needs the node catalog (/object_info) of the server
that will run them. Read-only: it only GETs /object_info, it never queues a job.

    uv run --with comfy-cli scripts/export_api.py                     # all features that have a workflow_ui.json
    uv run --with comfy-cli scripts/export_api.py cinema.camera-rig   # one feature
    ... --base https://cloud.comfy.org --key $COMFY_API_KEY           # convert against Comfy Cloud's catalog
    ... --object-info object_info.json                                # offline, from a saved catalog
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

from comfy_cli.workflow_to_api import WorkflowConversionError, convert_ui_to_api

ROOT = Path(__file__).resolve().parent.parent
MEDIA_LOADERS = {"LoadImage": "image", "LoadVideo": "video", "LoadAudio": "audio"}


def fetch_object_info(base: str, key: str | None) -> dict:
    req = urllib.request.Request(base.rstrip("/") + "/object_info", headers={"X-API-Key": key} if key else {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def summarize(api: dict) -> dict:
    loaders = {nid: MEDIA_LOADERS[n["class_type"]] for nid, n in api.items() if n["class_type"] in MEDIA_LOADERS}
    texts = {nid: [k for k, v in n["inputs"].items() if isinstance(v, str) and len(v) > 20 and k in ("text", "value", "prompt")]
             for nid, n in api.items()}
    return {"nodes": len(api), "loaders": loaders, "text_inputs": {k: v for k, v in texts.items() if v},
            "outputs": [nid for nid, n in api.items() if n["class_type"].startswith("Save")]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("features", nargs="*")
    ap.add_argument("--base", default=os.environ.get("COMFY_BASE_URL", "http://127.0.0.1:8188"))
    ap.add_argument("--key", default=os.environ.get("COMFY_API_KEY"))
    ap.add_argument("--object-info", type=Path)
    args = ap.parse_args()

    info = json.loads(args.object_info.read_text(encoding="utf-8")) if args.object_info else fetch_object_info(args.base, args.key)
    ids = args.features or sorted(p.parent.name for p in (ROOT / "features").glob("*/workflow_ui.json"))
    failed = 0
    for fid in ids:
        src = ROOT / "features" / fid / "workflow_ui.json"
        try:
            api = convert_ui_to_api(json.loads(src.read_text(encoding="utf-8")), info)
        except WorkflowConversionError as e:
            print(f"{fid}: FAILED {e}")
            failed += 1
            continue
        (src.parent / "workflow_api.json").write_text(json.dumps(api, indent=1), encoding="utf-8")
        print(f"{fid}: {json.dumps(summarize(api))}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
