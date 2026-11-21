# Intelligence and Intake

Use when entering a new hackathon or when the event context has materially changed.

## Gather without interrogating

Research or infer first. Ask the user only for information that is both unavailable and likely to change the next action, such as an unshared private rulebook, team availability, existing idea commitment, or authority to deploy.

Resolve:

- hackathon name, URL, organizer, start, deadline, timezone, and remaining time;
- team size, skills, availability, and ownership;
- challenge statements, themes, tracks, and prizes;
- judging criteria, definitions, weights, and process;
- required technologies, sponsor APIs, allowed frameworks, credits, and restrictions;
- submission platform, repository/deployment requirements, required media, pitch length, and demo length;
- current repository, idea, implementation, deployment, and demo state.

If no repository exists, do not invent a stack before idea selection and team-fit analysis. If a repository exists, inspect it before asking questions the files answer.

## Build `HACKATHON.md`

Copy `templates/HACKATHON.md` only when the project lacks an equivalent. Replace placeholders with facts and leave uncertain fields explicitly labeled. Include source links next to time-sensitive claims.

Keep it strategic, not archival. Summarize:

- event and clock;
- team;
- tracks and sponsor opportunities;
- rules and mandatory technologies;
- rubric and weighting;
- submission and pitch format;
- technical constraints;
- risks and known unknowns;
- decision-changing research findings.

Do not paste entire rulebooks. Quote sparingly; paraphrase and link.

## Build `HACKATHON_STATE.md`

This is the short resumption file. It must answer within one screen:

- What is the time mode?
- What is the current goal?
- What is the Golden Path?
- What exact wow moment is planned?
- What was last verified working, when, and how?
- What blocks P0?
- What are the highest-value P0/P1 tasks and their owners?
- What bugs or external risks can break the demo or submission?
- What is the next checkpoint?

Update state after a verified milestone, a blocker, a deadline change, a handoff, or a strategic cut. Do not log every keystroke.

## Staleness discipline

On resume:

1. Read repository instructions and `HACKATHON_STATE.md`.
2. Check actual Git status and recent history.
3. Inspect open TODOs/issues and changed configuration.
4. Run or smoke-test the relevant path when practical.
5. Recalculate the deadline.
6. Correct stale documentation before using it to prioritize.

Documentation never overrides observable project state or current official rules.
