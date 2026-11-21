# Quality and judging gates

**The product must be complete and reliable, not merely impressive-looking.** Apply every relevant check; tools cannot automatically judge all visual and usability qualities.

## Machine-enforced after stack choice

Before adding application source, the main agent must create `project-checks.json` with runnable argv arrays for:

1. `format`: consistent formatting
2. `lint`: code style and static defects
3. `typecheck`: type/syntax checks or equivalent
4. `unit`: tests of individual units
5. `integration`: cross-component/contract tests
6. `security`: known vulnerabilities, static checks and/or secrets scan
7. `build`: production build

If a category does not apply to the chosen stack, document a **real equivalent check** in its place, not `echo passed`. Add `accessibility` and `e2e` commands where supported. CI must fail if application directories exist without a real check configuration.

## Human and reviewer checks (mandatory where relevant)

- **Functionality:** Real end-to-end happy path, failure path, no demo-only hardcoded success.
- **UI quality:** Clear hierarchy, clean spacing, typography and colors, readable contrast, consistent components, excellent mobile layout.
- **Accessibility:** Keyboard navigation, focus states, labels, semantic controls, meaningful status/error messages, contrast.
- **Originality:** Solves the hackathon's actual problem, distinct value, measurable user benefit.
- **Engineering:** Understandable code, tight scope, healthy architecture, clear contracts, no duplicated magic constants.
- **Performance:** Responsiveness, loading indicators, degraded service behavior, avoid wasteful API calls.
- **Security/privacy:** Secrets excluded, least privilege, validated user input, safe error messages, no unsafe dependencies.
- **Demo:** Deployable, predictable, polished story, graceful backup if Wi-Fi/API fails.

## PR severity

- **Blocker:** Exposed secrets, broken build, major security defect, false test claims, breaking contract, invalid/missing core functionality, serious data loss risk.
- **Major:** Important bug, unreliable integration, inaccessible primary flow, substantial regression or missing agreed tests.
- **Minor:** Non-blocking polish, isolated refactor, optional optimization (prefer follow-up when time is short).

Reviewers must cite concrete files/lines and reproduction steps for blockers/majors. Treat visual quality as a separate manual review, not a pass/fail that lint alone can supply.

