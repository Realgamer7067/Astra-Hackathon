# UI/UX Strategy

Use from the first product pass, not only at the end. Visual quality makes technical evidence legible and strongly affects perceived completeness even when it has no explicit rubric row.

## Establish a visual direction early

Define a compact design system tied to the product's users and subject matter:

- 4-6 named colors with hex values and contrast roles;
- one or two typefaces, a deliberate type scale, line lengths, and weights;
- spacing scale, page width, grid, and density;
- border radius, borders, elevation, and card treatment by hierarchy;
- navigation, icon family, motion language, and data-visualization style;
- loading, empty, success, and error states.

Avoid default AI/SaaS aesthetics applied without reason: identical rounded cards, decorative gradients, random particles, generic copy, or the same fade-up animation on every section. Spend visual boldness on one memorable, product-specific element; keep the rest disciplined.

## Screenshot test

For every important screen ask: `Would this screenshot look convincing on the submission page?`

Judge-ready views have a clear subject, strong hierarchy, realistic content, useful density, intentional spacing, clean contrast, and a visible result. Avoid lorem ipsum, `User 1`, blank dashboards, giant empty sections, raw JSON, developer forms, unstyled tables, broken images, debug panels, and browser-default controls where a styled alternative is easy.

Use realistic seeded data that advances the pitch story. The demo input, intermediate state, result, and impact metric should feel like one scenario rather than unrelated samples.

## Landing-page rule

Use a landing page only when it helps the judging path. Optimize the first 10-20 seconds:

`hero -> problem -> product reveal -> interactive preview -> proof/features -> technical credibility -> impact -> demo CTA`

The hero must communicate **what it is, who it helps, and why it differs** without multiple paragraphs. Avoid forcing judges through marketing before the working product.

## Motion

Use motion to explain change or focus attention: a coordinated hero reveal, workflow progress, data transformation, success feedback, chart transition, or page change. User-triggered motion should make cause and effect obvious.

Avoid slow entrances, heavy parallax, ambient effects that compete with content, and anything that can lag on the demo machine. Respect reduced-motion preferences and keep a no-animation fallback when motion is demo-risky.

## Visual review loop

After meaningful UI changes:

1. Run the real application.
2. Navigate the Golden Path at the likely demo resolution.
3. Capture the landing/product view, core action, result, and wow moment.
4. Inspect first impression, hierarchy, spacing, typography, clipping, overflow, contrast, density, controls, responsiveness, loading, errors, and animations.
5. Check console and network failures.
6. Fix the most visible issue, then recapture.

If browser automation or screenshots exist, use them. Prefer reconnaissance before automation: inspect the rendered page, then act on observed selectors and states. Visual snapshot tests are useful for stable critical screens but should not consume the final hours if manual inspection is faster.

If the host cannot run or view the app, give a short manual verification path and ask for screenshots when they would change the next action. Mark visual QA `NOT VERIFIED`; never claim screenshot inspection from reading source alone. For CLI, hardware, API, or accessibility-first entries, polish the actual judge-visible experience instead of forcing a marketing website.

## UX critic mode

Periodically approach the app as a tired first-time judge:

- What is this?
- Who is it for and why should I care?
- Where do I click?
- What is happening now?
- Did the action work, and what changed?
- What should I do next?

If any answer is unclear, improve copy, hierarchy, feedback, or navigation before adding a feature. Use plain user language and consistent action labels.

## Quality levels

- **FUNCTIONAL:** works.
- **DEMO READY:** works repeatedly through the presentation path.
- **JUDGE READY:** works, looks intentional, tells the story, and makes rubric evidence visible.

Raise the few Golden Path screens to JUDGE READY. Secondary surfaces may remain functional or hidden.
