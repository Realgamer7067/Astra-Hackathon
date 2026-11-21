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

