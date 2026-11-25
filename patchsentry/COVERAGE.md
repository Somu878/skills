# What was read, and what a skill can and cannot carry

Read at upstream commit e5d82d4 (0.25.0) via a git clone: README, AGENTS.md, the official skill, scripts/validate-skill.mjs, docs (cli, config, graph, scanners, for-agents, privacy, telemetry), core/lenses (49), core/src/brief-staged.ts (finder and verifier prompts and schemas), brief.ts severity rules, finalize.ts floors, review/src/stages.ts, units.ts, evidence-check.ts, agents/claude.ts and codex.ts.

NOT read line by line: the code-graph extractors and resolvers (~60k lines), scanner adapters, installer/init internals, hook.ts, push-gate.ts, render/html.ts, the benchmark. Their behaviour is taken from the docs.

Portable as instructions: the method (inventory, units, two finder passes, quote-evidenced candidates, independent verifier, floors and tiers, coverage receipt), the 49 lenses, the severity scale, the answer shapes, manual graph questions.

Needs the OpenQodex CLI/runtime: the scanners and their pinned downloads, snapshotting and secret redaction, a separate read-only Claude Code/Codex reviewer, script validation of quotes/shape/coverage, the code graph and MCP server, report files, push-gate hooks, the GitHub Action.

Note: the full OpenQodex CLI sends anonymous usage telemetry by default (see upstream docs/telemetry.md; off with OPENQODEX_TELEMETRY=0 or DO_NOT_TRACK=1). Patchsentry itself runs nothing.

Install: copy the folder into your agent's skills directory (check your agent's docs), or `npx skills add Somu878/skills --skill patchsentry -g`. The skills CLI install is not verified here.
