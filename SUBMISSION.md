# Submission checklist: #OpenSourceHiggsfield

Deadline: **Oct 30, 2026, 9am PT.** Target: everything done by the evening of **Oct 29**.
Entry form: https://form.typeform.com/to/V1dSQrkS (sign-up form: https://form.typeform.com/to/Ayn9Cwfj).
One main category + one provider bonus per entry. Declared entry: **Open Weights Only + LTX VFX bonus**.

Publishing, hosting and posting are public actions: do each one deliberately.

## Before the four links
- [ ] Signed up on the sign-up form (first 200 get credits)
- [ ] Open Weights eligibility question asked: does an optional `partner/` pack in the repo matter? If unclear, keep it out of the public repo
- [ ] No unlicensed IP or likenesses in example outputs or driving clips; everything SFW
- [ ] Example outputs are real renders (not mock placeholders) and sit in the repo or README

## 1. GitHub repo URL (required)
Must be public, with an open-source license and setup instructions.
- [ ] `gh auth login` done (not signed in as of Oct 21)
- [ ] LICENSE present (MIT) and listed on the repo page
- [ ] README: what it is, install, run locally, how to point at ComfyUI (`COMFY_BASE_URL`), model download steps, mock mode vs comfy mode
- [ ] Workflow files + manifests committed; `COVERAGE.md` regenerated and honest about what was tested
- [ ] Clean-clone test passed (fresh venv, install, download models, run 3 modules)
- [ ] No keys, `.env`, outputs or model weights committed
- [ ] Repo made public, URL pasted: ______________________

## 2. Demo video URL (required, under 2 minutes)
Show the build in action and how it was built. Host it (YouTube unlisted, X, etc.) and test the link logged out.
Outline (about 110 s):
| Time | Beat |
|---|---|
| 0:00-0:10 | Hook: "Higgsfield said open source. We built it." One-line pitch + the open-weights claim |
| 0:10-0:30 | The app: studio list, search across all features, one form per feature |
| 0:30-1:05 | Live runs, real renders: Genjutsu motion transfer, a Cinema Studio shot, a Viral effect. Show timing honestly |
| 1:05-1:30 | How it was built: manifest per feature, ~18 base workflows, generated presets, `comfy-sdk` calling local ComfyUI |
| 1:30-1:45 | Coverage: the tier numbers from COVERAGE.md (what is tested vs generated) |
| 1:45-1:55 | Why it is innovative (needed for Most Innovative) + repo URL on screen |
- [ ] Recorded at 1080p, under 2:00
- [ ] Link works logged out: ______________________

## 3. Live link to try it (optional, strongly encouraged)
Not shared publicly. Expect 5-10 judge runs, so it needs a real ComfyUI behind it.
- [ ] Decide: Comfy API deployment / rented GPU (Runpod) / skip
- [ ] If yes: deployed, auth sorted, one full run tested end to end
- [ ] Link: ______________________

## 4. Social post link (required)
Post tagged **#OpenSourceHiggsfield** (X, Instagram, Reddit, TikTok, etc.). Your account, your call.
- [ ] Post drafted: short clip or the demo video, repo link, hashtag
- [ ] Posted publicly; URL: ______________________

## Submit
- [ ] All required fields filled, links opened once from a logged-out browser
- [ ] Main category and bonus category chosen to match the declared entry
- [ ] Submitted before Oct 29 evening PT (Oct 30 morning is buffer only)
