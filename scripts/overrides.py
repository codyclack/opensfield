"""Print the {node: {field: value}} overrides the app would send for a module (same code path as the runner).

    uv run scripts/overrides.py viral.effects '{"start_image": "x.png", "effect": "Vanish", "prompt": "a runner"}'

Media inputs take a file name already present in the target server's input folder. Handy for rendering a module on
Comfy Cloud's template runner with exactly the prompt the app composes.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.registry import load_features  # noqa: E402
from app.runner import resolve_values  # noqa: E402

feature = next(f for f in load_features() if f["id"] == sys.argv[1])
vals = resolve_values(feature, json.loads(sys.argv[2]))
out: dict = {}
for spec in feature["inputs"]:
    v = vals.get(spec["name"])
    if v in ("", None) or "node" not in spec or (spec["kind"] == "seed" and not v):
        continue
    if spec["kind"] == "number":
        v = int(v) if isinstance(spec.get("default"), int) else float(v)
    for t in [{"node": spec["node"], "field": spec["field"]}, *spec.get("also", [])]:
        out.setdefault(t["node"], {})[t["field"]] = v
print(json.dumps(out))
