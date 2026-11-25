# Skills

**A collection of agent skills I built for Claude Code, Cursor, Codex, and other AI coding agents.**

---

## Skills

| Skill | Description | Install |
|-------|-------------|---------|
| [Dot Matrix](dotmatrix/) | Generate ambient dot-matrix scene videos — cozy dioramas, rainy windows, cityscapes, seamless-loop MP4 | `npx skills add Somu878/skills --skill dotmatrix -g` |
| [ReachCraft](reachcraft/) | Reach-first X/Twitter posting skill — hooks, threads, replies, and distribution plans optimized for impressions | `npx skills add Somu878/skills --skill reachcraft -g` |
| [Patchsentry](patchsentry/) | Runtime-free, evidence-checked review of a code change before you push: inventory, finder and verifier passes, confidence floors, 49 bug-pattern lenses. Adapted from OpenQodex | `npx skills add Somu878/skills --skill patchsentry -g` |

---

## Install any skill

```bash
npx skills add Somu878/skills --skill <name> -g
```

Or from the full URL:

```bash
npx skills add https://github.com/Somu878/skills --skill <name> -g
```

---

## License

MIT

The `patchsentry/` folder is an adaptation of [OpenQodex](https://github.com/openqodex/openqodex) (Apache License 2.0). It keeps its own LICENSE and NOTICE.md.
