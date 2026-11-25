# Asking "what does this change reach?" without the graph (from docs/graph.md)
The real tool builds a local code graph (TS/TSX/JS, Python, Go, Ruby, Java; no model) and puts a "What this change reaches" block in the brief. By hand, for each touched/removed symbol collect:
- Touched, removed or moved symbols (a move under another name: same body).
- Public names the change removed or rebound, with every place that used them and what each binds now.
- Callers, one and two hops out. Mark each: certain (import names it, same scope, receiver type proven), likely (a stated convention picks the target), possible (interface/base-type dispatch, function used as a value, name match only). A name match alone is never certain.
- Uses as a value or type; implementers/overrides; what the touched code calls; files that import a changed file; tests that cover it.
- Unknowns: external, no-receiver-type, untyped receiver, not exported, dynamic (`handlers[key]()`), ambiguous, dynamic base classes, unreadable manifests. State them. A caller list with such gaps is a floor: zero callers never means unused.
With the CLI present instead run `openqodex graph callers|callees|implementers|references|routes|tests|path|impact|importers|outline|cycles|changes|unknowns|explain` (see upstream docs/graph.md and docs/cli.md at https://github.com/openqodex/openqodex/tree/e5d82d473b3f93640ddf2cee244126288a5ae737/docs).
