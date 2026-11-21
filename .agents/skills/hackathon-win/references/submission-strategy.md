# Submission Strategy

Use when submission fields become known; begin before final polish.

## Submission safety

Create `SUBMISSION.md` and verify deadline/timezone, late-edit behavior, required fields, repository visibility, deployed URL, video, images, track selections, sponsor declarations, team members, licenses/credits, and submission status.

Submit a minimally valid version before the last minutes when the platform allows edits. Keep evidence of successful submission. Do not assume a saved draft is submitted.

Run `scripts/submission-audit.py --help` for local artifact and placeholder checks, then inspect the actual submission platform.

Internal planning documents are not automatically submission requirements. Pass event-required files with `--require`; missing internal documents are advisory. A passing local audit cannot prove acceptance. Record portal confirmation/ID and time; if a submit action times out, inspect portal state before retrying to avoid duplicate entries. Do not assume drafts, late edits, or organizer recovery are accepted. Remove genuinely inapplicable template rows or mark them `N/A — <official reason>`; never mark a required asset N/A merely to clear the audit.

## README as a judging surface

Lead with understanding, not installation:

1. project banner or strongest screenshot;
2. short name and one-sentence memory hook;
3. demo and video links;
4. problem and solution;
5. key Golden Path and wow feature;
6. screenshots;
7. architecture and actual technical contribution;
8. technology and sponsor integrations;
9. what was built during the event;
10. concise setup;
11. team, credits, limitations, and future work.

Avoid long setup walls before the product explanation, raw architecture dumps, unverified metrics, and hidden mock disclosures.

## Screenshots

Capture at least the landing/product reveal, main workflow, primary result, and wow moment. Add dashboard/mobile views only when useful.

Before capture ensure:

- realistic and coherent data;
- no broken images, console errors, debug panels, placeholders, secrets, personal data, or embarrassing seed content;
- useful viewport and projector-friendly contrast;
- deployed URL rather than localhost when practical;
- stable state and intentional cursor/scroll position.

## Demo video

Fit the actual limit. Default two-minute structure:

- `0-10s`: problem and product;
- `10-60s`: Golden Path;
- `60-90s`: wow moment;
- `90-120s`: technical differentiator, result, and close.

Clarity beats cinematic editing. Use readable zoom, clean narration, no dead waiting, and captions when they improve accessibility. Verify the uploaded video from a signed-out/private context if allowed.

## Final platform check

Open every submitted link from the view judges will have. Verify repository permissions, deployment health, video access, image order/crops, selected tracks, sponsor declarations, and team membership. Keep a local demo, screenshots, and video as fallbacks.
