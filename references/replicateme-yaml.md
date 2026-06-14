# openLifeOS YAML

`replicateme.yml` is the setup manifest generated before building a digital-avatar repo. It stores permission intent and access boundaries, not secrets.

Generate it from prompts:

```bash
python scripts/tui_avatar_config.py --output replicateme.yml
```

Apply it:

```bash
python scripts/apply_avatar_config.py replicateme.yml
```

If the YAML requests GitHub remotes or a memory wiki repo:

```bash
python scripts/apply_avatar_config.py replicateme.yml --install-tools
gh auth login
python scripts/apply_avatar_config.py replicateme.yml --create-remotes
```

## Fields

| Field | Meaning |
| --- | --- |
| `repo_path` | Local target path for the avatar repo. Relative paths resolve from the YAML file location. Factory default: `output/meta/<repo_name>`. |
| `repo_name` | Target repo name, usually `<Name>.LifeOS` or a user-defined anonymous repo name. |
| `identity_mode` | `named` or `anonymous`. Anonymous mode uses labels and a PSP pseudonym instead of requiring a real-world name. |
| `owner_name` | Person, team, organization, or local owner label represented by the LifeOS. Anonymous mode may use a non-real label. |
| `display_name` | Human-facing LifeOS label. |
| `psp_display_name` | Name used inside `identity/psp/<person_id>/PSP.md`; anonymous mode should use a pseudonym. |
| `person_id` | Stable slug for `identity/psp/<person_id>/`. |
| `language` | `zh-CN` by default; `en-US` when requested. |
| `process_log_language` | Process/status log language. Defaults to `language`, but can be set independently when the user's UI/process language differs from artifact language. |
| `visibility` | `local-only`, `private`, or `public`. |
| `public_summary` | Owner-approved one-line public summary; may stay TODO until confirmed. |
| `public_material_policy` | `public-only`, `approved-extracts`, or `private-by-default`. |
| `raw_material_policy` | Usually `never-commit`. |
| `github_owner` | GitHub user/org for avatar and memory repos. |
| `github_account_type` | `user`, `org`, or `unknown`. |
| `github_auth_method` | `gh-oauth`, `fine-grained-token-env`, `manual`, or `skip`. |
| `github_permissions` | Comma-separated GitHub permissions/scopes, such as `metadata:read, contents:write`. |
| `github_require_gh` | Whether `apply_avatar_config.py` should require GitHub CLI. |
| `github_auth_required` | Whether `gh auth status` must pass. Usually true only when creating remotes. |
| `github_create_avatar_repo` | Whether `--create-remotes` should create the avatar repo. |
| `github_create_memory_repo` | Whether `--create-remotes` should create the memory wiki repo. |
| `github_token_policy` | Must be a no-store policy; use `gh auth` or environment variables. |
| `memory_repo_name` | GitHub repo name for the user's long-term wiki. |
| `memory_repo_visibility` | Usually `private`. |
| `memory_repo_path` | Local path or submodule slot under `identity/memories/`. |
| `memory_source_policy` | `github-private-wiki`, `external-private-wiki`, `server-rsync`, or `manual-approved-extracts`. |
| `memory_access_policy` | Usually `private-by-default`; governs the default publication posture for memory-derived material. |
| `memory_public_mirror` | `none`, `index-only`, or `approved-derived`. Default: `index-only`. |
| `memory_collaboration_policy` | How trusted collaborators and agents update memory. Default: `private-pr-or-owner-approved-extract`. |
| `memory_raw_material_policy` | Usually `never-copy-raw-private-bodies`. |
| `memory_allowed_public_exports` | Comma-separated derived export classes, usually `approved-facts, redacted-summaries, abstracted-patterns`. |
| `wiki_authoritative_source` | `github`, `server-rsync`, or `local-only`. If `server-rsync`, the server is the single source of truth. |
| `wiki_sync_modes` | Comma-separated sync surfaces, such as `github, rsync`. |
| `wiki_rsync_enabled` | Whether an internal rsync flow should be configured. |
| `wiki_rsync_target` | Optional non-secret rsync target label/path. Do not store passwords or SSH keys. |
| `feishu_configure` | Whether Feishu/Lark integration should be configured. |
| `feishu_tenant_name` | Workspace/tenant label; not a secret. |
| `feishu_app_id` | Optional non-secret app id. Do not store app secret. |
| `feishu_app_type` | `self-built-app`, `user-oauth-app`, `manual-export`, or `unknown`. |
| `feishu_auth_method` | `env-only`, `manual-export`, `oauth`, or `skip`. |
| `feishu_permissions` | Comma-separated permissions such as `docs:read, wiki:read`. |
| `feishu_source_usage` | Allowed usage: Wenxin self-discovery, public positioning, PSP distillation, memory index, etc. |
| `feishu_token_policy` | Must avoid repo storage; normally `env-only` or `manual-export`. |
| `hermes_configure` | Whether Hermes self-evolution sync should be configured. |
| `hermes_update_cadence` | `on-new-evidence`, `daily`, `weekly`, or `manual`. |
| `hermes_source_usage` | Allowed Hermes inputs, such as `github-events`, `feishu-export`, `wiki-diff`, `manual-approved-material`. |
| `hermes_targets` | Artifacts Hermes may update: Wenxin, PSP, skill recommendations, memory index, root routing, GitHub PRs. |
| `hermes_token_policy` | Must avoid repo storage; normally `env-only` or managed platform secrets. |
| `wenxin_goals` | Comma-separated goals for self-discovery: self-understanding, public positioning, field map, gap analysis, future paths, candidate Skill recommendations. |
| `recommended_skill_domains` | Comma-separated domains used to seed `identity/wenxin/skill-recommendations.yml`. |
| `skill_recommendations_source` | Usually `identity/wenxin/`; update after public positioning is generated. |
