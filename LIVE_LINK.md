# Live link (optional): run the app for judges

Judges will do roughly 5 to 10 real runs, so the app must run in `comfy` mode with a Comfy API key. Keys and credits stay on
your machine; never commit or paste the key anywhere public.

**Heads-up:** the app's own `comfy-sdk` path has been run live for one module (`image.bg-remove`, 2026-10-21) and worked; other modules have not each been run through the app. The example renders went through
Comfy Cloud's template runner. Do step 3 (a local test) before you share anything.

## 1. Create an API key
cloud.comfy.org, signed in as the account with the plan, then Settings and the API keys section (listed under User or Secrets).
Create a key and keep it private.

## 2. Start the app in comfy mode (PowerShell)
```powershell
cd opensfield
$env:COMFY_API_KEY = "<paste your key here>"
$env:OPENSFIELD_MODE = "comfy"
$env:OPENSFIELD_ACCESS_KEY = "<make up a long random string>"   # gate: only people with the link can use it
$env:OPENSFIELD_MAX_JOBS = "60"                                  # hard cap on runs per server start, protects credits
uv run --extra comfy uvicorn app.main:app --port 8765
```
No `COMFY_BASE_URL` means it talks to Comfy Cloud.

## 3. Test locally first
Open `http://127.0.0.1:8765/?key=<your access key>`. Run `soul.t2i` (cheapest: a prompt only), then one video module.
The badge in the corner should say "ComfyUI connected". If a run errors, copy the error text and send it to me; a likely cause is
the converted API workflows needing re-export against Cloud's node catalog (`scripts/export_api.py --base https://cloud.comfy.org --key ...`).

## 4. Make it public with a tunnel (no hosting account)
```powershell
winget install Cloudflare.cloudflared
cloudflared tunnel --url http://127.0.0.1:8765
```
It prints `https://<random>.trycloudflare.com`. Your live link is that address plus `/?key=<your access key>`.

- Keep your computer on, with both windows open, until judging is over (results are announced Nov 6).
- A quick tunnel gets a new address every time you restart it; if you restart, update the form entry.
- Each run costs a few seconds to about a minute of Cloud GPU. The cap above stops runaway use.

## Alternative: a stable URL on a host such as Render
New Web Service from `github.com/codyclack/opensfield`. Build command: `pip install uv && uv sync --extra comfy`.
Start command: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set the four environment variables from step 2 in the
host's secret settings. Free tiers sleep when idle, so open it once before submitting. This needs your hosting account.
