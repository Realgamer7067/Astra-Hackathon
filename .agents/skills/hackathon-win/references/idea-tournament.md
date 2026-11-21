# Idea Tournament

Use after generating candidates and before committing meaningful build time.

## Stage 1: fatal gates

Reject or radically narrow an idea if any answer is unacceptable:

- Can judges understand it in seconds?
- Is there a believable user and visible value?
- Can the central claim be made real within the time limit?
- Can the best capability be demonstrated live?
- Can claims be verified or defended?
- Can the demo survive an external-service failure?
- Is it eligible under event rules and the selected or mandatory track rules? Missing an optional sponsor prize removes that prize, not the whole idea.
- Is it more than a generic wrapper or common submission?

Do not average away a fatal flaw with good visual-potential scores.

## Stage 2: weighted ranking

Score 0-10 using explicit evidence:

- rubric fit: `+2.0`
- demo impact: `+2.0`
- feasibility: `+1.5`
- originality: `+1.0`
- visual potential: `+1.0`
- story strength: `+1.0`
- technical depth: `+1.0`
- sponsor fit: `+1.0`
- usefulness: `+1.0`
- time-to-MVP: `+1.0`
- differentiation: `+1.0`
- failure risk: `-1.0`
- complexity cost: `-1.0`
- dependency risk: `-1.0`

Adjust weights to the official rubric; record changes. Run `scripts/score-ideas.py --help` for reproducible ranking.

## Stage 3: compare finalists

For the top three, produce:

- Golden Path and exact wow second;
- timeboxed proof spike for the riskiest assumption: roughly 15-60 minutes for a 24-hour event, shorter under pressure; extend only for a high-value core risk with an explicit stop time;
- P0 build estimate by team member;
- fallback for every risky dependency;
- "why us / why now / why this event" explanation;
- strongest skeptical-judge objection and response.

Prefer pairwise comparison over arguing from raw totals. Ask which candidate is more likely to be finished, understood, believed, and remembered.

## Stage 4: lock with a kill condition

Choose one idea and record:

- decision rationale;
- central claim;
- Golden Path;
- wow moment;
- proof spike deadline;
- kill/narrow condition if the core risk does not resolve.

Do not reopen ideation because implementation becomes uncomfortable. Reopen only when eligibility changes, the central claim proves infeasible, or new evidence materially changes expected score.
