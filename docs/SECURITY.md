# Security and credentials

- Never commit access keys, `.env`, cloud tokens, passwords, private user data or developer machine configuration.
- Set secrets **inside the provider's private secret store**, not GitHub PR bodies or agent prompts.
- Cloud agents receive **only the repo and minimum account permissions** they need.
- Test untrusted contributor PR code only in a sandbox and never with production credentials.
- Avoid executing unfamiliar curl/bash installers just because an agent recommends them. Use official installers and confirm each installation.
- Do not let a reviewer use `gh pr merge --admin`, modify protection settings, or bypass failed checks.
- Project permissions are not installed by copying this ZIP; configure them in GitHub explicitly.
- For new code: validate input, use parameterized queries, apply least privilege, check dependencies and error paths, review auth and file upload handling.
- Hackathon judging rules take precedence over convenience; verify attribution and whether generated assets/coding agents must be disclosed.


## ASTRA-specific controls

Allowlist official provider hosts; never accept arbitrary upstream URLs. Validate asteroid IDs and time windows. No browser-to-JPL proxy without fixed validated routes. Enforce request, simulation, page, worker and timeout caps in CONTRACTS.md. Restrict CORS to configured origins; keep provider credentials optional and server-side. Do not publicly expose unlimited compute. Cache with provenance and obey provider backoff/refresh policy. Catalog metadata and submitted assumptions are untrusted input.
