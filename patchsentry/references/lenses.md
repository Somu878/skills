# Pattern lenses (from OpenQodex packages/core/lenses, commit e5d82d4, Apache-2.0)
A lens is a known bug pattern. Use one only when its trigger fits the changed hunk (file type and the hunk regex). Each lens has a confidence floor: a finding citing it counts toward the verdict only at or above that floor; between 0.5 and the floor it is a Possible issue. `security: true` marks security lenses. Follow each lens's Flag / Suppress lists.

## a11y-icon-only-button-no-aria-label
- What: Icon-only button / clickable that relies on `title` for description without an aria-label
- Files: *.astro, *.jsx, *.svelte, *.tsx, *.vue
- Hunk regex: ``
- Floor: 0.75; security: false

A clickable element renders only an icon (an `<svg>`, an emoji, a
single character from a font-icon set, an `<img>` whose `alt` is
empty or omitted) and depends on `title` to convey what it does.
`title` is hover-only and is NOT reliably announced by screen
readers, so the control is opaque to assistive-tech users: they
hear "button" with no context.

Flag when an interactive element added in this diff:
- has no readable text node as a child (only `<svg>`, an icon
  component like `<ChevronIcon />`, `<img alt="">`, a single
  glyph, or pure children-of-children that are themselves icons),
- has no `aria-label`, `aria-labelledby`, OR a visually-hidden
  text label (`<span class="sr-only">…</span>`, `<VisuallyHidden>`,
  Tailwind's `sr-only` utility), AND
- the element is `<button>`, `<a>`, `[role="button"]`, or has an
  `onClick`/`onPointerDown`/`onKeyDown` handler.

The `title` attribute alone is NOT a fix; flag those too.

Suppress when:
- the button already has `aria-label`, `aria-labelledby`, or a
  visually-hidden text child (`sr-only`, `visually-hidden`,
  `<VisuallyHidden>`, `screen-reader-text`),
- the icon itself carries a label (`<svg aria-label="…">` or an
  icon component whose own implementation injects an aria-label),
- the project already has a wrapping component like `<IconButton
  label="…" />` that injects the aria-label,
- the element has visible text alongside the icon.

Severity: `minor` by default. Bump to `major` for primary CTAs
(submit / save / delete) where the missing label blocks the user's
intent, not just degrades it.

## array-iteration-missing-key-prop
- What: .map() rendering JSX without a stable key prop (or using index as key for mutable lists)
- Files: *.jsx, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

JSX rendered inside `.map(...)` either has no `key` prop or uses
the array index as a key. Without a stable key React can't reorder
children correctly: form inputs lose their internal state on
re-order, animations replay, and components mounted in the loop
double-fire effects when items shift positions.

Flag when:
- the `.map((item) => <Component .../>)` returns JSX with no `key`
- the `key` is `index` (or any expression that depends only on the
  loop index) AND the underlying list can reorder / insert / remove

Suppress when:
- a stable id field is used (`key={item.id}` / `key={item.uuid}`)
- the list is provably static for the component's lifetime
  (read-only constants, sorted-once display lists)
- the index IS the natural key (immutable, append-only)
- the rendered children are stateless / sideeffect-free and won't
  notice a reorder

## async-await-in-loop-n-plus-one
- What: await inside a for / map / forEach, N round-trips per row
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

A `for` loop / `for-of` / `.map(async ...)` / `.forEach(async ...)`
body contains an `await` against a network or database client.
Sequential awaits multiply latency by row count (100 rows × 30ms
= 3s) and turn a list view, batch import, or N-of-M lookup into a
classic N+1.

Flag when:
- the loop iterates over a list of identifiers / records and the
  body awaits a fetch / db query / API call **per iteration**
- the result is collected into an array (a `Promise.all` over the
  iterable would parallelize cleanly)

Suppress when:
- ordering matters AND the next iteration's input depends on the
  previous iteration's result (rate-limited APIs, paged cursors,
  workflows that build on prior steps)
- there's an explicit per-iteration delay / rate-limit
- the loop iterates a known-small fixed set (≤ 3) where
  parallelization wouldn't change anything material
- a `.map(async ...)` is followed by `await Promise.all(...)`;
  that IS the parallel pattern

## async-click-double-fire-race
- What: Async onClick handler with no in-flight guard / disabled toggle, double-clicks fire duplicate requests
- Files: *.jsx, *.svelte, *.tsx, *.vue
- Hunk regex: ``
- Floor: 0.75; security: false

A button / link / clickable triggers an async operation
(`fetch`, `mutate`, an awaited handler) without any guard against
re-firing while the first request is still in flight. A rapid
second click queues a duplicate request: a duplicate insert, a
double-charge, an interleaved state update where the late response
clobbers the early one. Touchpad users and slow networks hit this
constantly.

Flag when a handler added in this diff:
- is `async` OR returns a Promise / calls `await ...` / calls
  `fetch(...)` / calls a project-specific async helper (mutate,
  a fetch wrapper, etc.),
- AND has no `isLoading` / `inFlight` / `pending` boolean checked
  at the top (early return when true),
- AND has no `disabled={isLoading}` (or equivalent class swap) on
  the bound element,
- AND has no library-level dedup (TanStack Query's `mutate` with
  the same key is OK; React Query's `useMutation` running through
  its own queue is OK; a hand-rolled `setX([...])` is NOT).

Examples that should fire:
- `onClick={async () => { const r = await fetch(...); setState(r); }}`
  with no disabled / loading guard
- an expand/collapse toggle that calls `fetchTeamMembers(id)`
  but doesn't track `loadingTeams.has(id)`
- `<button onClick={async () => { await save(); navigate(...) }}>`
  where save can take seconds

Suppress when:
- the handler is wrapped by `useMutation` / `useAction` /
  `useTransition` / similar library primitive that owns the
  in-flight tracking,
- the bound element has `disabled={isLoading}` /
  `aria-disabled={isLoading}` / a CSS class swap that prevents
  pointer events,
- the handler is genuinely idempotent (PATCH against a known
  resource state, GET-only, etc.); call out the idempotency
  guarantee when you suppress.

Severity: `minor` for read-only / idempotent paths, `major` for
writes / mutations / billable actions (the duplicate insert and
the double-charge cases).

## async-floating-promise
- What: An async function is called without await / .catch, silent rejection
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

An async function is invoked from synchronous code (or from another
async fn) without `await`, without `.then(...).catch(...)`, and
without `void`. The returned promise floats: a rejection becomes an
unhandled rejection (process warning, eventual crash on newer Node
versions, swallowed entirely in browsers) and the caller has no
ordering guarantee with subsequent statements.

Flag a call to an `async fn` (or a fn that demonstrably returns a
promise: `.then` chains, fetch wrappers, db client calls) whose
return value is **discarded**: not assigned, not returned, not
awaited, not chained with `.catch`, and not preceded by the explicit
`void` keyword.

Suppress when:
- the call is intentionally fire-and-forget AND prefixed with `void`
  (the documented "I know" marker)
- the outer scope wraps in `Promise.all([...])` / `Promise.allSettled`
- the call is on a logger / telemetry / metrics method where dropped
  rejections are explicitly acceptable

## async-promise-all-swallows-errors
- What: Promise.all over fire-and-forget side effects loses partial failures
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

`Promise.all([...])` rejects on the FIRST rejection and silently
discards the results of every later promise, even ones that
succeeded after rejection. When the array members are independent
side-effects (insert N rows, fire N webhooks, send N emails), the
caller only sees one error but several side-effects may have run
and several may have silently not run. Recovery / retry becomes
impossible because the caller can't tell which ones happened.

Flag a `Promise.all([...])` where each item is an INDEPENDENT
side-effect (call to db/insert, http POST, message publish, file
write) and the caller doesn't:
- use `Promise.allSettled` to inspect each result, OR
- wrap each item in `.catch` to translate rejections into per-item
  status

Suppress when:
- the items are reads (the all-or-nothing semantic matches "I need
  every value to proceed")
- the wrapper IS `Promise.allSettled`
- the items are wrapped individually with `.catch` so the all sees
  only fulfilled promises

## async-unhandled-rejection-in-handler
- What: Express / Hono / Fastify handler is async but has no try/catch and no errorHandler middleware
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

An HTTP route handler is declared `async` but its body contains an
`await` that can throw, no `try/catch`, and the framework in use is
NOT auto-promoting promise rejections to error middleware. Express 4
silently hangs the request; Express 5 + Hono + Fastify auto-handle,
but a misconfigured app or an older Express still drops these on the
floor: the client sees a request that times out at the LB while
the server logs a `UnhandledPromiseRejectionWarning` somewhere.

Flag when:
- handler is `async (req, res) => { ... await ... }`
- framework is Express 4 (check imports) OR the project has no
  registered error-handling middleware visible

Suppress when:
- the handler is wrapped in an `asyncHandler` / `expressAsyncHandler`
  / `tryCatch` helper that translates rejection → next(err)
- framework is Hono / Fastify / Express 5 with the default error
  surface (rejections become 500s automatically)
- the body has a top-level `try/catch` that ends in `res.status(...)`
- the handler is `next` style with the rejection threaded into
  `.catch(next)`

## auth-missing-on-state-change-route
- What: POST / PUT / PATCH / DELETE route registered without an auth middleware in sight
- Files: *.cjs, *.go, *.java, *.js, *.jsx, *.kt, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: true

A new route handler for a state-changing verb (POST / PUT / PATCH /
DELETE) is registered with no auth middleware chained on the route,
no `@auth` / `requireAuth` decorator, and no `req.user` /
`session.user` guard inside the body. Anyone with the URL can mutate
state. Particularly dangerous when the route is added under an
existing prefix where the dev assumed auth was inherited but the
prefix isn't actually protected.

Flag when the diff adds a state-changing route AND the body doesn't
reference an authenticated principal, AND no auth middleware appears
on the same route registration.

Suppress when:
- the route is explicitly public (signup, login, password-reset
  request, public webhook with HMAC validation)
- a middleware chain on the router/app applies auth globally (look
  for `app.use(authMiddleware)` / `router.use(...)` earlier in the
  file)
- the framework auto-applies auth via a base controller / module
  decorator (read the surrounding file before raising; the auth
  may live one level up)
- the route reads/validates a signed token (webhook with HMAC,
  short-lived signed URL)

In Java and Kotlin the same shape is `@PostMapping` / `@PutMapping` /
`@PatchMapping` / `@DeleteMapping` (or `@RequestMapping` with a method)
on a controller method with no `@PreAuthorize`, no `@Secured`, and no
rule in the security configuration covering the path.

## auth-role-from-user-input
- What: Role / permission / isAdmin value taken from request body or query
- Files: *.cjs, *.go, *.js, *.jsx, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: true

A role / permission / `isAdmin` / tier / plan value is being read
from request input (`req.body`, `req.query`, form data, JSON
payload) and used for an authorization check OR written to a
persistent record. This is the classic privilege-escalation bug:
the attacker passes `{"role": "admin"}` in the POST and the system
trusts it.

Flag when:
- a string/bool from request input is assigned to a `role` /
  `permission` / `isAdmin` column on an `INSERT` / `UPDATE`
- a check like `if (req.body.role === 'admin')` gates an action
- a JWT / session is created with a `role` claim copied from input

Suppress when:
- the role assignment is explicitly gated by an admin-only
  authorization check earlier in the function (look for
  `requireRole('admin')` / `ctx.user.isAdmin`)
- the input goes through an allow-list AND the user is already an
  admin (e.g. an admin promoting another user)
- the value is being compared to derive a STRING used for routing /
  filtering (not for an authorization decision)

## auth-timing-attack-password-compare
- What: Password / token / secret compared with == / === instead of a constant-time check
- Files: *.cjs, *.cs, *.go, *.java, *.js, *.jsx, *.kt, *.mjs, *.php, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

A password / token / signature / HMAC / API key is being compared
with `==`, `===`, `!=`, `!==`, `.equals()`, or `strcmp`, all of
which short-circuit on the first byte mismatch and leak timing
information. An attacker can recover the secret byte-by-byte by
measuring response latency, especially against repeatedly-callable
endpoints.

Flag when:
- the comparison's left or right operand is named or sourced from
  the request as a `password|secret|token|hmac|signature|apiKey`
- the operator is a default `==` / `===` / `!==` / `equals`

Suppress when:
- the call is `crypto.timingSafeEqual` /
  `hmac.compare_digest` (Python) /
  `subtle.ConstantTimeCompare` (Go) /
  `MessageDigest.isEqual` (Java)
- the comparison is on the OUTPUT of a verified KDF (bcrypt /
  scrypt / argon2 `compare`); the KDF wrapper is already
  constant-time and that's the recommended API
- the comparison is against a literal "empty"/"missing" sentinel
  (`token === undefined`); that's an existence check, not a value
  match

## cookie-missing-secure-httponly
- What: Auth / session cookie set without HttpOnly + Secure + SameSite
- Files: *.cjs, *.go, *.js, *.jsx, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

A `Set-Cookie` for a session / auth / refresh / CSRF cookie is
emitted without `HttpOnly` (JS-readable, stealable via XSS),
without `Secure` (sent over plain HTTP), or without a `SameSite`
attribute (allows CSRF via cross-site form submits in older
browsers / strict-mode-off contexts).

Flag when a cookie name containing `session|sid|auth|token|refresh`
is set with options that omit `httpOnly: true`, `secure: true`, or
`sameSite: 'strict'|'lax'`.

Suppress when:
- the cookie is intentionally JS-readable (e.g. a CSRF token cookie
  paired with a header-based defense pattern), but check that
  `secure + sameSite` are still set
- the environment is dev/test and the env-gated config explicitly
  disables `secure` for local HTTP only
- a wrapper / framework default applies these attributes globally
  (look for the wrapper's defaults before raising)

## cors-wildcard-with-credentials
- What: CORS allows '*' origin while also setting credentials: true
- Files: *.cjs, *.go, *.js, *.jsx, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: true

CORS is configured with `Access-Control-Allow-Origin: *` (or a
reflective `origin: true` that echoes the request's `Origin`)
together with `Access-Control-Allow-Credentials: true`. Browsers
reject wildcard + credentials together, but reflective Origin +
credentials lets any origin run authenticated requests against the
API: CSRF and cookie theft become trivial.

Flag when:
- `origin: '*'` is set with `credentials: true`
- `origin: true` (reflective) is set with `credentials: true` AND
  there's no allow-list checked first

Suppress when:
- the origin is a concrete allow-list (`['https://app.example.com', ...]`)
  or matched against one before being echoed
- `credentials: false` (the wildcard is safe without cookies)
- the API is genuinely public read-only and never reads / accepts
  cookies / Authorization headers (defense in depth: still
  recommend a concrete allow-list)

## crypto-jwt-verify-without-algo-allowlist
- What: jwt.verify called without an explicit algorithms allowlist
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: true

A JWT is verified without passing an explicit `algorithms` option.
The `jsonwebtoken` library historically accepted whatever the token
header declared, which lets an attacker switch to `alg: "none"`
(no signature) or downgrade an RSA-signed token to an HMAC verify
where the public key gets reused as the HMAC secret. Recent
versions tightened defaults but the attack returns the moment the
project pins an older version or uses an alternate library with
permissive defaults.

Flag when `jwt.verify(token, secret)` is called without `{
algorithms: ['HS256'|'RS256'|...] }` in the third argument.

Suppress when:
- `algorithms: [...]` is passed (with a concrete allow-list, not
  e.g. `['none', ...]`)
- the library is `jose` and the call form already enforces alg via
  the key object's `alg` field
- the verify is inside a wrapper that lints algorithms internally
  (look for the wrapper definition before raising)

## crypto-math-random-for-tokens
- What: Math.random() used to generate tokens, IDs, or secrets
- Files: *.cjs, *.java, *.js, *.jsx, *.kt, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: true

`Math.random()` is a non-cryptographic PRNG. Its state is small,
its output is predictable from observed values, and modern V8 has
been shown to allow practical state-recovery attacks. Any token /
ID / nonce / one-time code generated with `Math.random()` and
used for a security purpose can be guessed.

Flag when `Math.random()` is used to build:
- session / password-reset / verify-email / magic-link tokens
- API keys, invite codes, OTP codes
- CSRF tokens or nonces
- request IDs that gate access (e.g. order-pickup codes)

Suppress when used for:
- jitter / backoff timing
- A/B test bucketing
- animation / UI randomness
- non-security IDs (telemetry trace fragments where collision is
  the only concern)
- in tests, where determinism (`seedrandom`) or non-crypto values
  are the point

Recommend `crypto.randomUUID()` / `crypto.randomBytes(n)` /
`crypto.getRandomValues(...)` per platform.

In Java and Kotlin the same bug is `new Random()`, `java.util.Random()`
or Kotlin's `Random()` where `SecureRandom` is required. `SecureRandom`
itself is the fix, not the bug.

## crypto-md5-sha1-for-secrets
- What: MD5 / SHA-1 used for passwords, tokens, or signatures
- Files: *.cjs, *.cs, *.go, *.java, *.js, *.jsx, *.kt, *.mjs, *.php, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

MD5 and SHA-1 are broken hashes for any security-bearing use:
collision attacks are practical on both, and pre-image attacks
on MD5 are within reach. Using them to hash passwords, derive
keys, or sign / verify integrity is a real bug, not a stylistic
preference.

Flag when MD5 / SHA-1 is used to:
- hash a password / passphrase (use bcrypt / scrypt / argon2)
- derive a key from a secret (use HKDF / PBKDF2)
- sign or verify a token / payload (use HMAC-SHA256 or better)

Suppress when:
- used for a NON-security purpose: ETag generation, cache key,
  content addressing, deterministic identifier (the hash's
  cryptographic weakness doesn't matter for cache invalidation)
- used to verify an integrity tag returned by an external system
  that itself uses MD5 / SHA-1 (S3 ETag, legacy webhook contract)
- the call is to a `crypto.createHmac('sha1', ...)` and the spec
  the code implements (e.g. AWS Signature V1, older OAuth flows)
  mandates SHA-1

In Java and Kotlin this is `MessageDigest.getInstance("MD5")` or
`getInstance("SHA-1")`. The fix is BCrypt or Argon2 for passwords and
SHA-256 or better for signatures.

## env-vars-read-at-module-top
- What: process.env read at module-evaluate time, undefined before loadEnvFile
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: false

A module reads `process.env.X` at module-evaluate time (top-level
`const X = process.env.X` or in a default-export object). ESM
evaluates all imports BEFORE the entry's body, so any env var set
by `dotenv` / `process.loadEnvFile()` / a manual setup at the
entry point is undefined when this module loads.

Symptom: the value is `undefined` in dev despite the variable
existing in `.env`; client init silently uses defaults; integration
breaks in a way that's hard to root-cause from a stack trace.

Flag when a module's top-level body (NOT inside a function) reads
`process.env.X` AND the resulting value is exported / used to
initialize a client / SDK / config object.

Suppress when:
- the read is inside a function the entry point calls AFTER env
  loading (lazy init pattern)
- the module documents that it must be imported AFTER env setup
  with a comment explaining why
- the read is for a build-time constant baked in via the bundler
  (Vite's `import.meta.env`, esbuild's `--define`)

## eval-on-user-input
- What: eval / new Function / vm.runInThisContext over untrusted input, RCE
- Files: *.cjs, *.java, *.js, *.jsx, *.kt, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.85; security: true

`eval(input)`, `new Function(input)`, or `vm.runInThisContext(input)`
called with a value derived from user input is server-side remote
code execution. `child_process.exec(input)` (the unsanitized
shell-string form) is the same thing for OS commands. There is no
"weak" version of this finding; if the input traces back to user
control, it is a critical bug.

Flag with high confidence when any of these calls receive a value
sourced from request body / query / path / form / env / file
contents.

Suppress when:
- the argument is a build-time constant
- the argument is derived from a strictly-typed structured input
  (e.g. an integer parsed from `req.params.id`) embedded into a
  fixed template, but recommend the safer alternative anyway
- `child_process.execFile` / `spawn` with an array of args is used
  instead (no shell parsing)
- the input is run through a parser → AST → restricted-evaluator
  (e.g. a sandboxed expression evaluator like `expr-eval`) rather
  than the JS runtime

In Java and Kotlin the equivalents are `Runtime.getRuntime().exec(...)`,
`ProcessBuilder`, and the `ScriptEngine` family evaluating a script
string that came from a request.

## fetch-without-timeout
- What: Outbound HTTP request without timeout / abort signal, request thread hang
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

A server-side outbound HTTP call (fetch / axios / got / ky / undici)
is made without a timeout or `AbortSignal`. The upstream can take
seconds to minutes to time out at the network layer; meanwhile the
request handler is blocked, downstream callers stack up, and one
slow third party can drag the whole API into cascading latency.

Flag when:
- the call is `fetch(url)` with no `signal:` option
- `axios.get(...)` / `axios.request(...)` with no `timeout:` option
- the call is to a third-party host (not the same service / not
  localhost)

Suppress when:
- `signal: AbortSignal.timeout(N)` is passed
- `timeout: N` is set
- the project-wide HTTP client wrapper applies a default timeout
  (look for the wrapper before raising)
- the call is to a local sidecar / same-pod service where timeouts
  are explicitly managed at the platform layer (rare in app code)

## id-enumeration-sequential
- What: Sequential / integer IDs used as URL parameters for access-controlled resources
- Files: *.cjs, *.go, *.js, *.jsx, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

A handler accepts a sequential integer ID from the URL
(`/orders/:id`, `/users/:id`) and looks up the row by primary key
without verifying that the authenticated principal OWNS that row.
This is IDOR (Insecure Direct Object Reference): an attacker just
increments / decrements the ID to enumerate other users' data.

Even when the ID type is opaque (UUID), the missing-authz check is
still a bug; the attacker may have obtained a leaked link.

Flag when:
- the handler resolves a record by `id` from the URL
- the subsequent query has no `where: { ownerId: ctx.user.id }`
  (or equivalent) clause
- there's no permission check / policy call between the lookup and
  the response

Suppress when:
- the row IS scoped to the authenticated user in the query
- a policy / RBAC / row-level-security check runs explicitly
- the resource is public by design (a blog post, a published
  document) and the handler is the public endpoint

## interactive-state-decoupled-from-output
- What: New user-mutable state is introduced but an output that should depend on it reads a static or duplicate source instead
- Files: *.jsx, *.svelte, *.tsx, *.vue
- Hunk regex: ``
- Floor: 0.72; security: false

This diff adds a piece of user-mutable state (a `useState` /
`useReducer` / store `writable` / `ref` / a `toggle*` handler that
flips a Set or boolean) AND there is an output in the same component
whose meaning DEPENDS on that state but which is computed from a
different, static, or duplicate source, so toggling the control in
the UI has no effect on the output it appears to govern.

The classic shape: a user can star/unstar, select/deselect, enable/
disable, or filter items, but a derived view (an alert banner, a
count, a summary, a "what matches" list, a submit payload) is built
from a constant default list, an unrelated prop, or a separately
hardcoded copy of the same data, not from the live state the user
just changed. Each line reads correctly on its own; the bug is the
MISSING wire between the state and the consumer.

Flag when, in this diff:
- new interactive state `S` is introduced (and a handler mutates it),
  AND
- there is a rendered output or computed value `O` whose
  semantics clearly should reflect `S` (it is "about" the same thing
  the user is toggling), BUT
- `O` is derived from a static constant, a duplicated literal, or a
  different source, never reading `S`.

Trace it: find every place the new state SHOULD be read (the outputs
that semantically depend on it) and check each actually reads it. An
output that reads a static/duplicate source instead of `S` is the
finding. This also surfaces nearby dead code: a status/variant value
that no branch ever produces, or the same metric rendered from two
different sources that can disagree.

Suppress when:
- the static source is intentional and documented (e.g. the default
  list is the seed and the toggle layers on top, and the output
  correctly merges both),
- the output genuinely should not depend on the state (the
  resemblance is coincidental),
- the state is purely presentational (drives only its own control's
  appearance, like a star's fill) and no other output is expected to
  track it.

Severity: `major` when the decoupling makes a user-facing control a
no-op for the thing it implies it controls (e.g. unwatching a
category in the UI but the alert still fires for it); `minor` for
cosmetic-only mismatches.

Example: a "watched categories" toggle drove only
the star icon while the threshold-breach alert banner was computed
from a separate static `DEFAULT_WATCHES` constant, so starring /
unstarring had no effect on which categories tripped the alert.

## json-parse-no-try-catch
- What: JSON.parse over untrusted input without try/catch, crashes the request
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

`JSON.parse(input)` throws on invalid input. When the input is a
request body, query string, cookie, or external API response, an
attacker can crash the handler by sending non-JSON. In Express 4
this surfaces as a 500 + log spam; in async handlers without an
async error boundary it can become an unhandled rejection.

Flag when `JSON.parse(...)` is called on a value sourced from
`req.body|req.query|req.cookies|req.headers|response|fetch result|
file read|process.argv` and the call is NOT inside a `try { ... }
catch` (or wrapped by a parser like `Zod.safeParse(JSON.parse(...))`
that itself doesn't catch the parse phase).

Suppress when:
- a `try/catch` surrounds the call and returns a sensible response
- the body parser of the framework already runs `JSON.parse` and
  surfaces a typed error (`express.json()`, Hono's `await c.req.json()`
  inside an error-handling app)
- the value is provably valid JSON from a controlled internal
  source (a value the SAME service wrote moments ago and the parse
  is the reverse trip)

## missing-rate-limit-on-auth
- What: Login / password-reset / OTP / signup endpoint without rate limiting visible
- Files: *.cjs, *.go, *.js, *.jsx, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

A login / signup / password-reset / OTP-verify / magic-link
endpoint is registered without a rate-limit middleware visible.
Without one: credential stuffing trivially scales, password-reset
email pumps spam any address, OTP-verify allows brute force, and
signup bots burn through plan limits.

Flag when:
- the new route handles auth-flow input (password, OTP code, email
  send) and the diff doesn't show a rate-limiter on the route OR
  a `rateLimit` / `limiter.consume` call inside the body

Suppress when:
- a `limiter` / `rateLimit` middleware is chained on the route
- the framework / platform applies per-IP throttling at the edge
  (Vercel, Cloudflare, AWS WAF) and that's documented in the
  repo (CLAUDE.md, README, infra notes)
- the endpoint is a webhook with HMAC signature (different threat
  model: bot calls are rejected by signature check)
- the project explicitly uses a 3rd party (Clerk / Auth0 / WorkOS
  / Supabase Auth) that owns auth flows; the route is a thin
  pass-through and the provider rate-limits

## oauth-scope-wider-than-use
- What: Connector requests an OAuth scope no code path in it actually uses
- Files: *.go, *.java, *.js, *.json, *.kt, *.mjs, *.py, *.rb, *.ts, *.tsx, *.yaml, *.yml
- Hunk regex: ``
- Floor: 0.75; security: true

A connector asks the provider for a scope, and nothing in the connector
ever calls an endpoint that needs it. The declaration is usually one
string in an authorize URL, a client constructor, or a manifest, written
once when the integration was built and never narrowed as the feature
shrank. The cost is real: the token the user grants can do more than
the product does, so a leaked token, a compromised server, or a bug in
the connector reaches data and writes the product never intended to
touch. A `full` scope on a connector that only reads one record is the
shape.

How to check, before you flag anything:

- Find the scope declaration. Read the whole line and the call it sits
  in, so you can quote it and say which scopes are requested.
- Enumerate every provider call the connector makes. Search the
  connector's own directory for the provider's base URL, its client
  class, or the SDK method prefix (search for callers of the client,
  then for the base URL) and list the endpoints you found.
- Map each requested scope to the calls that need it, using the
  provider's own scope documentation as the connector states it, not a
  guess about naming.
- Report every scope with no call behind it. One finding per unused
  scope, not one per connector.

What to cite:

- The scope declaration line, with file and line, quoted whole.
- The provider calls you found, each as a supporting quote with its file
  and line. This is what makes the finding checkable: without the list,
  "no call needs this" is an assertion, not evidence.

Suppress when:

- the provider only grants the scope as part of a bundle (some providers
  have no finer grain than `read`), and the connector says so
- the scope is used on a path behind a feature flag or an unreleased
  code path that is still in the tree
- a sibling connector or a shared client in the same repository uses the
  same credential, so the calls live outside this directory; widen the
  search before flagging
- the connector is a thin proxy whose callers make the provider calls

Severity: medium by default. High when the unused scope grants write,
delete, or admin access, since the blast radius of the extra grant is
then the user's data rather than a wider read.

## object-spread-clobber
- What: { ...existing, ...incoming } overwrites server-controlled fields with user input
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

`{ ...existing, ...input }` spreads a user-supplied object over a
server-controlled one. Any field name in `input` that overlaps
`existing` wins, including fields the caller wasn't supposed to
write (`id`, `userId`, `role`, `tier`, `isAdmin`, `createdAt`,
`stripeCustomerId`).

Mass-assignment is the classic Rails / Express / Hono shape:
`db.update({ where, data: { ...req.body } })`.

Flag when:
- the spread merges a request-sourced object into a DB write
  payload / state object
- there's no explicit allow-list pick (`pick(input, [...])` /
  `{ name: input.name, email: input.email }`) before the spread
- the model has any field that an authenticated user shouldn't be
  able to set (role, owner, billing)

Suppress when:
- the spread is preceded by an allow-list pick / Zod parse with a
  strict schema (`schema.parse(input)` rejecting unknown keys)
- the spread is between two server-controlled objects only
- the destination is a transient payload (not persisted), and the
  extra fields are deliberately allowed

## open-redirect-from-untrusted-host
- What: HTTP redirect using a URL/host taken from query / body without allow-list
- Files: *.cjs, *.go, *.java, *.js, *.jsx, *.kt, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

A redirect target is constructed from request input (`?next=...`,
`?returnTo=...`, form field, JSON body) without validating that the
host belongs to a known allow-list. Phishing attacks chain
`/login?next=https://attacker.example/fake-login` so the trusted
host is the first thing the user sees in the URL bar.

Flag when a `redirect(url)` / `res.redirect(url)` / `Location:`
header is built from a request-derived URL string that isn't
validated against a list of allowed hosts or constrained to a
relative path.

Suppress when:
- the redirect target is constrained to a same-origin pathname
  (starts with `/`, no scheme / host)
- the URL is parsed and checked against an allow-list of hosts
  before redirect
- the value is the OUTPUT of a server-controlled flow (OAuth state
  recovered from session, post-payment URL from a payment provider
  the project controls)

In Java and Kotlin the idiom is `response.sendRedirect(target)`, a
Spring `RedirectView`, or a controller returning the string
`"redirect:"` with a request value appended.

## orm-drizzle-on-conflict-clobber
- What: Drizzle / Kysely onConflictDoUpdate that updates every column, clobbers downstream writes
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

A Drizzle `onConflictDoUpdate({ set: { ... } })` (or Kysely
`onConflict(...).doUpdateSet`) with a `set:` block that updates
**every column** the insert tried to write overwrites columns the
caller didn't mean to touch. Webhook replays, idempotent retries,
and "create or update" code paths regress columns that downstream
handlers have already advanced (status, tier, role, lastSeenAt,
updatedAt).

Closely related to the existing `upsert-state-column` lens, but
focused on the Drizzle / Kysely shape where the `set:` block is
copied directly from the insert values without a deliberate column
filter.

Flag when the `set:` block contains the same columns as the insert
AND any of those columns are state-bearing (status, stage, role,
plan, tier, version, updatedAt) or are commonly written by other
code paths (preferences, profile fields).

Suppress when:
- the `set:` block explicitly OMITS state-bearing columns
- the conflict clause uses `target: ...` with `setWhere` /
  `where: ...` that constrains the update to rows in a known state
- `onConflictDoNothing` (no clobber)
- the conflict target is a uniqueness column whose only path to
  conflict is a literal duplicate of the same write (idempotent
  semantic is the actual goal)

## path-traversal-in-fs-access
- What: File system read / write using a path built from user input
- Files: *.cjs, *.go, *.java, *.js, *.jsx, *.kt, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

A filesystem call (`fs.readFile`, `fs.writeFile`, `open`, etc.)
uses a path built by joining a base directory with a value sourced
from request input. `../../../etc/passwd` and absolute-path
substitution bypass the base. Reads leak arbitrary files; writes
let an attacker plant malicious content where the server will
serve / execute it.

Flag when the path argument is a join of:
- a server-controlled prefix (`./uploads/`, `path.join(BASE, ...)`)
- AND a value from `req.body`, `req.query`, `req.params`, form
  upload, parsed JSON, command-line args, or env

Suppress when:
- the user input is run through a sanitizer that strips `..` /
  `/` / null bytes
- the final path is `path.resolve`d and then verified to live
  beneath the base directory (`resolved.startsWith(base + sep)`)
- the input is a whitelisted enum / UUID lookup that the path
  derives from an internal mapping (not used as the filename
  directly)
- the file is served via a CDN / object store with its own access
  control (no FS at all)

In Java and Kotlin the idiom is `new File(base + userInput)` (Kotlin
drops the `new`),
`Paths.get(...)` or `Files.readAllBytes(...)` on a path segment taken
from a request parameter or a multipart upload's filename.

## pii-in-url-or-log
- What: PII (email, phone, SSN, full name) in URLs or unredacted log statements
- Files: *.cjs, *.go, *.js, *.jsx, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

A PII field (email, phone, SSN, full name, address, DOB) is
embedded in a URL query string OR logged unredacted. URL params
land in CDN logs, browser history, referrer headers to third
parties, and analytics services. Logs land in aggregators that
many engineers + vendors can read.

Flag when:
- a PII field is concatenated into a URL string for a redirect /
  fetch / external API
- a log call passes a record / object that contains a PII field
  without going through a redaction layer

Suppress when:
- the PII goes in the request BODY (POST/PUT) rather than the URL
- the log call explicitly uses a redactor / pino's `redact` /
  custom `scrubPii` helper
- the value being logged is an internal ID / hash of the PII, not
  the PII itself
- the URL is internal-only (no proxy / CDN / referrer leak) AND
  there's a documented reason (still recommend moving it to the body)

## race-check-then-act
- What: Check-then-act on a database row without a transaction / unique constraint
- Files: *.cjs, *.go, *.js, *.jsx, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

A handler reads a row to decide whether to insert / update / delete
(check-then-act), but the read and the write are NOT in the same
transaction AND the table has no unique constraint backing the
invariant. Concurrent requests both pass the check and both
proceed: two users get the same username, two orders against the
same inventory unit, two emails for "first signup" bonus.

Flag when:
- a `findOne` / `findFirst` / `count` / `exists` is followed by an
  `insert` / `update` / `delete` keyed on the same predicate
- the two operations are NOT wrapped in a single `transaction(...)`
  / `db.tx(...)`
- the predicate column is NOT a primary key / unique index

Suppress when:
- the operations run inside a single transaction with an explicit
  isolation level that prevents the race (serializable, or
  `SELECT ... FOR UPDATE`)
- the write uses an idempotent shape that survives the race
  (`INSERT ... ON CONFLICT DO NOTHING`, `UPDATE ... WHERE col = old`)
- a unique constraint / partial index on the table guarantees the
  invariant at the DB layer regardless of the app-level check

## react-dangerously-set-inner-html
- What: dangerouslySetInnerHTML fed by untrusted / unsanitized input
- Files: *.jsx, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

`dangerouslySetInnerHTML` bypasses React's HTML escaping. Any value
that traces back to user input, a network response, or
markdown/HTML rendered without sanitization is a stored or reflected
XSS sink.

Flag when the `__html` value's provenance is unsanitized: a prop or
state variable that came from `fetch`, `URLSearchParams`, `params`,
form input, comment / post / message content, or any markdown
rendered without an escaping pipeline.

Suppress when:
- the value is run through `DOMPurify.sanitize` /
  `sanitize-html` / equivalent immediately before the assignment
- the value is a literal string from the component itself (build-time
  constant, not user-derived)
- the value is the output of a markdown library configured with
  HTML disabled (`marked` with `sanitize: true`, `remark-html` with
  `sanitize` plugin, `markdown-it` without `html: true`)

## react-fetch-in-effect-without-abort
- What: useEffect fires a fetch but doesn't abort it on cleanup / dep change
- Files: *.jsx, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

A `useEffect` issues a `fetch` (or axios / ky / undici) but doesn't
hand the request an `AbortSignal` whose controller is aborted in the
cleanup. When the component unmounts before the response arrives,
or the deps change and the effect re-runs, the in-flight response
still resolves and calls `setState` on an unmounted component (or
clobbers fresher state with stale data from the previous request).

Flag when the fetch is started inside a `useEffect` and the cleanup
returned from the effect doesn't call `controller.abort()` (or the
fetch isn't passed a `signal` at all).

Suppress when:
- the body uses `react-query` / `swr` / TanStack Query (those
  handle abort + race themselves)
- the cleanup uses an `ignore` boolean flag inside the
  `.then(data => { if (!ignore) setState(data) })` pattern (slightly
  worse than abort but still correct)
- the request is fire-and-forget with no `setState` in the chain

## react-stale-closure-in-callback
- What: Event handler / timer closure captures a stale state value
- Files: *.jsx, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: false

A callback registered inside a render (event listener, `setTimeout`,
`setInterval`, subscription, or memoized handler) reads `useState`
values from the enclosing scope. Once registered, the closure keeps
the **initial** state forever; later re-renders don't refresh it.
The user sees "I clicked the new value but got the old one."

Flag when the callback's body reads a useState variable AND the
callback is registered outside an effect with that variable in its
dependency list.

Suppress when:
- the value is accessed via a `useRef.current` indirection
- the callback is re-registered each render via a `useEffect` with the
  stateful deps listed (so the closure refreshes)
- the value is provably immutable (initialized once, never reset)

## react-state-set-in-render
- What: useState setter called during render body, infinite loop
- Files: *.jsx, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: false

A `useState` setter called from the top-level render body (not inside
an event handler, effect, or callback) triggers a re-render, which
calls the component again, which calls the setter again: an infinite
re-render. React 18+ throws "Too many re-renders" but only at runtime,
and only when the path is actually hit; conditional set-in-render
escapes static analysis.

Flag a `setX(...)` call placed:
- at the top level of a functional component body
- inside an `if` / ternary / short-circuit that has a chance of
  evaluating to true on first render

Suppress when the call is inside:
- a `useEffect` / `useLayoutEffect` body
- a handler returned from JSX (`onClick={() => setX(...)}`)
- a `useState` initial-value function (`useState(() => ...)`)
- the conditional `if (cond) { setX(prev => ...) }` "derive state from
  props" pattern, where `cond` compares the prop to existing state
  and is provably guarded (this is the React-docs-blessed escape
  hatch; raise only if the guard looks broken)

## react-use-effect-missing-cleanup
- What: useEffect subscribes / starts a timer / opens a socket without returning a cleanup
- Files: *.jsx, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

A `useEffect` registers a subscription, timer, observer, or event
listener but never returns a cleanup function. When the component
unmounts (or the effect re-runs because a dep changed) the
side-effect keeps running against a stale component: a memory leak in
the cheap case, double-fire in state-mutating handlers in the bad
case, "can't update unmounted component" warnings either way.

Flag when the effect body contains `addEventListener`, `setInterval`,
`setTimeout`, a `.subscribe(`, `new WebSocket`, `new EventSource`, or
a `MutationObserver` / `IntersectionObserver` / `ResizeObserver`
without a matching `return () => { ... }` that removes / clears /
unsubscribes / disconnects it.

Suppress when the side-effect is intentionally one-shot and the
target lives at most as long as the component (e.g. a `setTimeout`
whose handler navigates away unconditionally).

## react-use-effect-missing-deps
- What: useEffect / useMemo / useCallback with an incomplete dependency array
- Files: *.jsx, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: false

A `useEffect` / `useMemo` / `useCallback` hook reads a value from
component scope (state, props, derived variable, function) but omits
it from the dependency array. On re-render the closure captures the
stale value and the effect either runs against outdated data, never
re-runs when it should, or memoizes incorrectly.

Flag when the hook's body references an identifier that is **not** in
its second-argument array and is **not** stable across renders
(`useRef.current`, module-level constant, dispatch from `useReducer`,
setter returned by `useState`).

Suppress when:
- the deps array is omitted entirely (then it runs every render, a
  different bug, but separate finding)
- the referenced identifier is a setter / ref / constant
- a lint comment explicitly disables `react-hooks/exhaustive-deps`
  with a justification on the line above

## regexp-from-user-input
- What: new RegExp(...) built from user input, ReDoS / injection
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

`new RegExp(input)` is called with a value derived from request
input. Two problems:
1. **ReDoS**: a crafted input like `(a+)+$` chained with a long
   string of `a`'s freezes the V8 regex engine, hanging the request
   thread (a single attacker can take down the API with one call).
2. **Regex injection**: the input redefines the search semantics:
   `.*` instead of the literal dot the dev expected.

Flag when the first argument to `new RegExp(...)` is a value
sourced from `req.body|req.query|req.params|form input|env`.

Suppress when:
- the input has been run through `escapeRegExp` (treats it as a
  literal pattern)
- the regex compile is bounded by a length check (`if (input.length
  > 64) return 400`) and a complexity-aware runtime (`re2` library,
  which is linear-time)
- the input is matched against an allow-list before compile
- the regex is for a non-blocking single-shot search against a
  bounded short string (still recommend escapeRegExp, but the DoS
  window is closed)

## replaced-line-drops-behavior
- What: A replacement drops an effect the old line had and the change does not restore it
- Files: *.C, *.R, *.S, *.asm, *.awk, *.bash, *.c, *.cbl, *.cc, *.cjs, *.clj, *.cljc, *.cljs, *.cob, *.coffee, *.cpp, *.cs, *.cts, *.cxx, *.d, *.dart, *.el, *.elm, *.erl, *.ex, *.exs, *.f, *.f90, *.f95, *.for, *.fs, *.fsx, *.go, *.gradle, *.groovy, *.h, *.hh, *.hpp, *.hrl, *.hs, *.hxx, *.java, *.jl, *.js, *.jsx, *.kt, *.kts, *.lisp, *.lsp, *.lua, *.m, *.mjs, *.ml, *.mli, *.mm, *.mts, *.nim, *.p, *.pas, *.php, *.pl, *.pm, *.ps1, *.psm1, *.py, *.pyi, *.r, *.raku, *.rb, *.rkt, *.rs, *.s, *.sc, *.scala, *.scm, *.sh, *.sql, *.ss, *.svelte, *.swift, *.tcl, *.ts, *.tsx, *.v, *.vb, *.vhd, *.vhdl, *.vue, *.zig, *.zsh
- Hunk regex: ``
- Floor: 0.7; security: false

For each removed line beside a replacement, name the old line's effects.
These include conditions, calls, resource releases and error handling.
Also check slices, initial values, retries, statuses and parser keys.
Compare those effects with the new code.
Include surrounding control flow and callers.

Flag a dropped effect only when this change never restores it.
Show the resulting failure from the code.
Name the lost effect.
Identify the input or path that needs it.
State the consequence.
Cite the replacement line.
A missing effect alone does not prove a defect.
Check whether the change intentionally removes the behavior.
Verify that the code supports that reason.

This lens triggers on replacements in files with these extensions:

- `.c`, `.cc`, `.cpp`, `.cxx`, `.C`, `.h`, `.hh`, `.hpp`, `.hxx`, `.rs`, `.cs`, `.php`
- `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.mts`, `.cts`, `.py`, `.pyi`, `.go`, `.rb`
- `.java`, `.kt`, `.kts`, `.swift`, `.m`, `.mm`, `.scala`, `.sc`, `.sh`, `.bash`, `.zsh`, `.sql`
- `.lua`, `.pl`, `.pm`, `.r`, `.R`, `.dart`, `.ex`, `.exs`, `.erl`, `.hrl`, `.hs`, `.clj`
- `.cljs`, `.cljc`, `.vue`, `.svelte`, `.vb`, `.fs`, `.fsx`, `.ps1`, `.psm1`, `.groovy`, `.gradle`, `.asm`
- `.s`, `.S`, `.zig`, `.jl`, `.ml`, `.mli`, `.nim`, `.v`, `.vhd`, `.vhdl`, `.f`, `.f90`
- `.f95`, `.for`, `.cob`, `.cbl`, `.coffee`, `.elm`, `.el`, `.lisp`, `.lsp`, `.scm`, `.ss`, `.rkt`
- `.d`, `.pas`, `.p`, `.raku`, `.tcl`, `.awk`

Suppress when:
- a renamed call has the same effect,
- the old line moved elsewhere in the same change and still runs on the
  paths that need it,
- another condition, call or cleanup preserves the old effect,
- the change explains why the behavior is no longer needed and the code
  supports that explanation,
- the edit only adds lines, or changes formatting or comments without
  changing behavior.

Example: `return ptr ? *ptr : 0;` becomes `return *ptr;`. The old line
handled a null pointer. If callers can still pass null, check for another null guard.
Without one, the replacement dereferences null instead of returning zero.
Flag the lost check. If the same change guards null before this line, raise nothing.

Severity follows the demonstrated consequence. Raise a bug, not a
request for tests, a style preference, or speculative hardening.

## return-shape-contract-break
- What: A function/endpoint that returns a structured object drops or renames a key/column its callers read
- Files: *.js, *.jsx, *.sql, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

A function, RPC, or endpoint that returns a structured payload (a
`jsonb_build_object` / `json_agg` in SQL, a returned object literal,
a `res.json(...)` / `c.json(...)` / `NextResponse.json(...)` body, a
`RETURNS TABLE`/composite shape) has the SET OF KEYS it returns
CHANGED by this diff: a key or column present on the `-` side is gone
or renamed on the `+` side. Removing or renaming a field from a
payload something already consumes is a silent breaking change: every
reader that referenced the old key now gets `undefined` / `NULL`, and
nothing in the producing file errors, so the diff reads clean in
isolation.

This is the highest-recall way to miss a real bug on an otherwise
tidy refactor. The evidence is the SHAPE of the returned document
across the diff, not the logic inside it: compare the keys emitted on
the `-` side against the `+` side, key by key.

Flag when this diff:
- removes a key from a `jsonb_build_object` / object literal /
  response body that the previous version emitted, OR
- renames such a key (old name vanishes, new name appears), OR
- drops a column from a `RETURNS TABLE` / view / `SELECT *`-feeding
  shape,

AND you cannot see, within the diff, that every consumer of the old
key was also removed. Trace the consumer when you can (search for the
key name, the RPC/function name, or the endpoint path); a removed key
that is still read downstream is a `major` breaking change. When the
consumer is out of the diff and you cannot confirm it was updated,
still raise it; default to "this breaks a contract" rather than
assuming the caller was migrated.

A strong corroborating signal: the diff also DELETES a comment or
doc that asserted the contract (e.g. a comment promising keys are
"additive" / "kept for back-compat" / "stable"). When a PR removes
language that promised stability and the code then breaks it, that is
a high-confidence flag; read the removed comments, not just the
removed code.

Suppress when:
- the diff also removes (or the change description states it
  removes) every consumer of the dropped key; a coordinated removal is not a
  break,
- the key is renamed AND the diff updates the readers in the same
  change,
- the payload is brand-new in this change (no prior `-` side), so there
  is no existing contract to break,
- the field is internal/never-serialized (e.g. a temp variable in a
  CTE that was never part of the returned object).

Severity: `major` when a removed/renamed key is consumed by code
outside the diff (real break); `minor` when the consumer is unclear
but the field plausibly mattered.

## secrets-logged-in-error-path
- What: Error / catch path logs an object that includes secrets, tokens, or request headers
- Files: *.cjs, *.go, *.java, *.js, *.jsx, *.kt, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: true

An error / catch handler logs an object that includes credentials,
authorization headers, API keys, request bodies (which may include
passwords), or full HTTP request/response payloads. These show up
in log aggregators (Datadog, Sentry, CloudWatch) where engineers,
support, or third-party integrations can read them: a compliance
issue at minimum, a credential-leak vector at worst.

Flag when a log call inside a catch / error path passes:
- a full `req` / `request` / `ctx.request` object
- a full `error` whose properties include request headers /
  response bodies (look for axios / fetch error shapes: `err.config.headers`,
  `err.response.config.headers`)
- a literal `password` / `token` / `secret` / `api_key` / `apiKey`
  variable
- environment-derived secrets

Suppress when:
- the log payload is the explicit error message string only
- the object is passed through a redaction layer (`pino` with
  `redact`, `winston` with format filter, custom `scrubSecrets`
  helper), visible on the same call or in the logger setup
- the only fields included are explicitly safe ones (status code,
  method, path, user id)

In Java and Kotlin the idiom is `e.printStackTrace()` or
`logger.error(message, e)` where the exception, or an object logged
beside it, carries the request headers, an `Authorization` value or a
provider token.

## sql-migration-references-later-object
- What: A migration references a column/table/function created by a later-timestamped migration (fails on fresh apply)
- Files: migrations/*.sql
- Hunk regex: ``
- Floor: 0.75; security: false

Migrations apply in timestamp (filename) order. Code that runs fine
against an already-migrated database can still break a fresh apply
(`supabase db reset`, a clean prod deploy, CI) if a migration references
a schema object (a column, table, type, function, policy) that is only
created by a migration with a LATER timestamp. The bug is invisible
locally because the object already exists; it only surfaces on a
from-scratch run.

This is especially easy to introduce with `@include`-style migrations: a
migration that `@include`s a function file inherits every object that
function selects/joins. If that function references a column added in a
later migration, this migration fails first.

Flag when a migration in this diff (or a function/file it `@include`s)
references an object whose creating/altering statement lives in a
migration timestamped AFTER this one. To check: identify the referenced
columns/tables/functions, then search the migrations directory for where
each is created (`ADD COLUMN`, `CREATE TABLE/FUNCTION/TYPE`) and compare
filename timestamps. Use your tools; this needs reading files outside
the diff.

Suppress when:
- every referenced object is created in an earlier or same-timestamp
  migration,
- the object is a Postgres built-in, an extension object, or created
  outside the migrations dir (e.g. a baseline/squash schema that always
  applies first),
- the reference is inside a string/comment, not executed SQL.

Severity: `major`: a deterministic fresh-apply / CI failure, not a
runtime edge case.

## sql-string-concatenation
- What: SQL built via string concatenation / template-string interpolation of unsanitized input
- Files: *.cjs, *.cs, *.go, *.java, *.js, *.jsx, *.kt, *.mjs, *.php, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: true

A raw SQL string is built by concatenating / interpolating a
variable into the query. If the variable's value traces back to a
user input, request parameter, environment variable, or any
external source, this is SQL injection. The diff often hides this
behind innocuous helpers (`buildWhere(...)`, `paramFilter(...)`).

Flag when:
- `SELECT|INSERT|UPDATE|DELETE|WHERE` literal appears in a string
  built with `+ var`, `${var}`, `format(...)`, `.format(...)`,
  `f"..."`, or `sprintf` against a variable whose provenance is not
  a hardcoded constant
- the variable comes from `req.body|req.query|req.params|args|
  argv|env|input`

Suppress when:
- the query uses parameter placeholders (`$1`, `?`, `:name`) with
  bound values
- the ORM call is the parameterized path (Drizzle's `eq`/`and`,
  Kysely's `.where(col, '=', val)`, Prisma's `where: {col: val}`)
- the interpolated value is an IDENTIFIER (table/column) and the
  identifier is sourced from an allow-list / enum check earlier in
  the function (still raise if you can't see the check)

In Java and Kotlin the idiom is `createStatement()` plus
`executeQuery("... " + value)`, or a JPA `createQuery` /
`createNativeQuery` string glued together, where `prepareStatement`
with bind parameters is the fix.

## ssrf-server-side-fetch
- What: Server-side HTTP request whose host or URL comes from user input
- Files: *.go, *.java, *.js, *.kt, *.mjs, *.py, *.rb, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.75; security: true

The server makes an HTTP request, and the host or the whole URL comes
from a request field, a header, or a value a user stored earlier
(a webhook target, an avatar URL, an "import from URL" box, a
provider's base URL held in a settings row). The attacker then chooses
where your server connects. Inside a cloud network that reaches the
instance metadata endpoint (`169.254.169.254`), internal admin services
on private ranges, and anything listening on localhost, none of which
is reachable from the internet, which is exactly why they are
unauthenticated.

What to check before flagging:

- Where the host comes from. Trace the value back: a request body or
  query field, a header, or a stored row a user controls all count. A
  constant base URL with only a path segment from input does not.
- Whether the host is allow-listed against an explicit set, and whether
  the check runs on the URL that is finally fetched rather than on a
  copy parsed earlier.
- Whether the scheme is pinned to http or https, so `file://`,
  `gopher://` and friends are refused.
- Whether private, loopback and link-local ranges are refused after DNS
  resolution, not just by a string check on the hostname.
- Whether redirects are followed. An allow-listed host that answers 302
  to `http://169.254.169.254/` defeats a host check done once up front.

What to cite: the line making the request, quoted whole with file and
line, and, as supporting quotes, the line the untrusted host arrives on
and any validation you did find, so the finding shows what guard is
missing rather than asserting there is none.

Suppress when:

- the base URL is a constant or comes from configuration and only a path
  or query value comes from input
- the value is checked against an allow-list of hosts, or resolved and
  checked against blocked ranges, before the request
- the request goes through a proxy or fetch helper in the repository
  that does those checks (find it and read it before deciding)

A request with a trusted host and no timeout is a different problem:
that is the `fetch-without-timeout` lens, not this one.

## supabase-comment-on-function-unqualified
- What: COMMENT ON FUNCTION uses an unqualified name while the function is created schema-qualified
- Files: *.sql
- Hunk regex: ``
- Floor: 0.75; security: false

`COMMENT ON FUNCTION <name>(<args>)` resolves `<name>` against the
applying session's `search_path` at migration time. When the function
is created schema-qualified (`CREATE ... FUNCTION public.foo(...)`) but
the comment names it unqualified (`COMMENT ON FUNCTION foo(...)`), the
statement fails with `function ... does not exist` on any session whose
`search_path` doesn't include that schema, and it's inconsistent with
the qualified `CREATE`. A function-body `SET search_path = public,
pg_temp` does NOT help: that governs the function's own runtime, not the
session running the `COMMENT`.

Flag when, in this diff, a `COMMENT ON FUNCTION` names a function
unqualified while the corresponding `CREATE [OR REPLACE] FUNCTION` (in
the same file or the migration it includes) is schema-qualified, OR when
it diverges from the repo's prevailing convention (search sibling
`COMMENT ON FUNCTION` statements; most will use `public.`).

Suppress when:
- the comment is already schema-qualified to match the CREATE,
- the function is genuinely created unqualified and the repo convention
  is unqualified comments throughout,
- the migration explicitly `SET search_path` for the statement scope.

Severity: `minor` (apply-time failure is gated on the runner's
search_path, which in Supabase's standard runner is usually `public`, so
it often won't fire in practice, but it's a real consistency/robustness
defect).

## supabase-function-default-public-execute
- What: A new/replaced Postgres function exposed via PostgREST is left with the default PUBLIC EXECUTE grant
- Files: *.sql
- Hunk regex: ``
- Floor: 0.7; security: false

Postgres grants `EXECUTE` to `PUBLIC` by default on every new function.
In Supabase, PostgREST exposes any function in an exposed schema
(usually `public`) as an RPC endpoint (`POST /rest/v1/rpc/<fn>`)
callable by the `anon` and `authenticated` roles. So a `CREATE [OR
REPLACE] FUNCTION public.<fn>` that returns privileged data or performs
a privileged action, with no accompanying grant management, is callable
by anyone holding an anon/JWT key, even if the only intended caller is
an admin-gated Edge Function using `service_role`.

Flag when this diff adds or replaces a function in an exposed schema AND
does NOT also `REVOKE EXECUTE ... FROM PUBLIC` (and grant EXECUTE only
to the intended role, e.g. `service_role` / `authenticated`). The risk
is highest when:
- the name or comment signals admin/internal scope (`admin_*`,
  `internal_*`, "admin-only", "backend"), or
- the body reads instance-wide / cross-tenant tables (users, teams,
  billing, activity, metrics) rather than the caller's own rows.

`SECURITY INVOKER` (the default) reduces but does not remove the risk:
RLS on the base tables only helps if RLS is actually enabled on every
table the function touches, and the RPC endpoint is still reachable.
Treat a missing `REVOKE PUBLIC` on a privileged function as a finding;
recommend `REVOKE EXECUTE ON FUNCTION public.<fn>(...) FROM PUBLIC;`
plus an explicit `GRANT` to the intended role.

Suppress when:
- the diff (or the same migration) already revokes PUBLIC and grants the
  intended role,
- the function returns only public, non-sensitive data and is meant to
  be world-callable,
- the repo has an established global migration / convention that revokes
  PUBLIC EXECUTE on all functions (verify it exists before staying
  silent),
- the change is purely cosmetic (renamed param, comment) on a function
  whose grants were already managed.

Severity: `major` when an admin/privileged function is left
PUBLIC-callable; `minor` for defense-in-depth hardening on a
non-sensitive one.

## supabase-security-definer-no-search-path
- What: A SECURITY DEFINER function omits a pinned SET search_path, allowing search_path hijack / privilege escalation
- Files: *.sql
- Hunk regex: ``
- Floor: 0.7; security: false

A `SECURITY DEFINER` function runs with the privileges of its owner, not
the caller. If it does not pin its `search_path`, a caller can set their
own `search_path` so that unqualified object references inside the
function resolve to attacker-controlled objects (a shadowing table,
function, or operator) in a schema the caller can write, executed with
the owner's elevated rights. This is the Postgres privilege-escalation
footgun that Supabase's own linter flags as
`function_search_path_mutable`.

Flag a `CREATE [OR REPLACE] FUNCTION ... SECURITY DEFINER` added or
modified in this diff that does NOT include a fixed
`SET search_path = ...` (e.g. `SET search_path = pg_catalog, public` or
`= ''` with fully-qualified references). Also flag when `search_path` is
set to something a caller can still influence.

Suppress when:
- the function pins `SET search_path` to a fixed value, OR
- every object reference in the body is already fully schema-qualified
  AND `search_path` is set, OR
- the function is `SECURITY INVOKER` (the default); invoker functions
  run as the caller, so this escalation doesn't apply.

Severity: `major` (privilege escalation on a definer function).

## supabase-single-500-on-no-match
- What: Supabase `.single()` on a query that can legitimately return zero rows, throws PGRST116 and bubbles up as a 500
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.8; security: false

A Supabase query chain ends in `.single()` against a row that may
not exist (lookup by `id` from a request param, `.eq("user_id",
…)` where the caller may pass an unknown id, etc.). `.single()`
throws PostgREST error `PGRST116` ("Cannot coerce the result to
a single JSON object") when the row count is anything other than
exactly 1. In an edge function, that error bubbles into a 500
when the correct response is a 404, and the caller can't distinguish
"the thing you asked for doesn't exist" from "the server broke."

Flag when this diff adds (or modifies into) a Supabase query that:
- ends in `.single()`,
- selects / updates / deletes by an identifier (`eq("id", …)`,
  `eq("user_id", …)`, `match({...})`),
- where the identifier traces back to a request parameter
  (`req.params`, `req.query`, `req.body`, `req.url`, the parsed
  payload of an edge function),
- AND the surrounding code does NOT catch `PGRST116` / does NOT
  check `error.code === "PGRST116"` to map to a 404.

Examples that should fire:
- `await supabase.from("activities").update({...}).eq("id", id).single()`
  with no PGRST116 → 404 handling
- `await supabase.from("users").select("*").eq("email", req.body.email).single()`
- `await supabase.from("teams").delete().eq("id", req.params.teamId).single()`

Suggested fix in the description:
- Swap `.single()` for `.maybeSingle()` (returns `{data: null,
  error: null}` on zero rows) and have the handler return 404
  when `data === null`, OR
- Keep `.single()` and catch `error.code === "PGRST116"`
  explicitly, mapping to a 404 response.

Suppress when:
- the query is filtered by a column with a unique constraint AND
  the caller has already proven the row exists earlier in the
  request (e.g. an auth middleware fetched the user row by id),
- the surrounding code already handles `PGRST116` (look for the
  literal `"PGRST116"` string in the catch or in an
  `error.code ===` check),
- the function uses `.maybeSingle()` instead.

Severity: `major`: a 500 on a missing row is a real user-facing
bug (looks like an outage) and a real auditing problem (alerts
fire on 5xx, not on 404).

## upsert-state-column
- What: Upsert / on-conflict writes that clobber workflow-state columns
- Files: *.cjs, *.cs, *.go, *.java, *.js, *.jsx, *.kt, *.mjs, *.php, *.py, *.rb, *.sql, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

An upsert / on-conflict insert that writes a literal value to a
state-bearing column (stage, status, state, tier, role, phase, plan)
will overwrite that column on every matching row, including rows that
have already advanced past that state. On CRM, billing, fulfillment,
and auth flows this silently regresses the workflow on the next
webhook or replay.

Flag as a bug **unless** the write is explicitly guarded:

- `ignoreDuplicates: true` / `ON CONFLICT DO NOTHING`
- an `updateColumns` (drizzle / kysely / supabase) or `DO UPDATE SET`
  list that **omits** the state column
- a `WHERE` / `.eq()` predicate on the upsert that constrains by the
  current value of the state column

Confidence rule still applies: if you cannot tell from the diff
whether such a guard exists upstream (helper wrapping the upsert,
trigger on the table, generated-column default), read the surrounding
code before raising. Drop the finding when the guard
is plausible and you can't disprove it.

## url-not-encoded-for-user-id
- What: URL string built by concatenating a user-supplied identifier without encodeURIComponent
- Files: *.cjs, *.js, *.jsx, *.mjs, *.ts, *.tsx
- Hunk regex: ``
- Floor: 0.8; security: true

A URL is built by string concatenation or template-string
interpolation of an identifier (uuid, slug, user id, email,
search query, encoded token) without `encodeURIComponent`. When
the substituted value contains a reserved character (`#`, `?`,
`&`, `/`, `=`, `+`, space) the URL silently breaks: the trailing
path becomes a fragment, query params merge into the previous one,
or the slash splits the route. Worst case it's a one-character
SSRF if the substituted value can contain `@` (rewrites the host)
or a `..` segment that escapes the intended subdirectory.

Flag when a URL string in this diff:
- is built with `+ var`, `${var}`, or `concat(var)` where `var` is
  named like an identifier (`id`, `userId`, `slug`, `email`,
  `token`, `name`, `query`, `searchTerm`, `*_id`, `*_uuid`),
- AND the substitution happens in a path segment or query value
  position,
- AND there is no `encodeURIComponent(var)` / `encodeURI(var)` /
  `new URL(...).searchParams.set(...)` / equivalent encode call
  on the way in,
- AND `var` is not a hardcoded constant from earlier in the
  function.

Examples that should fire:
- `` `${baseUrl}/users/${userId}` `` where userId can hold `+`
- `` `https://analytics.example.com/people/${authUserId}` ``
- `fetch("/api/teams/" + slug + "/members")`
- `` `?q=${searchTerm}` ``

Suppress when:
- the substitution is wrapped in `encodeURIComponent(...)`,
- the URL is built with `url.searchParams.set(name, value)`;
  the URLSearchParams encoder handles reserved chars (including
  `/`, `=`, `&`) in the value,
- the value is encoded per-segment first and only then assembled
  into a pathname (e.g. `url.pathname = "/users/" +
  encodeURIComponent(userId)`),
- the substituted value is a literal / module-level constant /
  enum member (compile-time-known safe),
- the substituted value is already known to be opaque-encoded
  upstream (e.g. JWT, base64url); note the encoding source if
  the diff makes that visible.

DO NOT suppress on `new URL(...)` alone. The URL constructor
parses; it does NOT encode reserved characters inside a
pre-assembled path. Likewise `url.pathname = "/users/" + userId`
does NOT encode `/` (or other reserved chars) within the path
segment: if the substituted `userId` contains a `/`, the route
still splits exactly as the lens is meant to catch. The
URL-class suppression only applies when the encoding happens at
the per-segment / per-param boundary, not at pathname assignment
time.

Severity: `minor` for display URLs that just break visually,
`major` when the unencoded value reaches the network layer and
could redirect a request to a different host or path (the `..`
and `@` escape cases).

## use-state-default-not-functional
- What: useState initialized with an expensive computation that re-runs every render
- Files: *.jsx, *.tsx
- Hunk regex: ``
- Floor: 0.7; security: false

`useState(expensiveCompute())` invokes `expensiveCompute()` on
EVERY render: React only uses the result on the first render but
the call still happens. For pure functions this is wasted CPU; for
calls with side effects (analytics fire, localStorage read,
expensive parse) it's a real bug.

Flag when `useState(expr)` initializer is:
- a function call that's NOT a cheap literal / variable read
- a `JSON.parse` / `localStorage.getItem` / `sessionStorage.getItem`
  / a sync filesystem call / a heavy array build

Suppress when:
- the initializer is the lazy form `useState(() => expensiveCompute())`
  (React only calls the function on mount)
- the initializer is a literal, a stable variable, or a cheap
  primitive lookup
- the function is memoized externally and cheap on subsequent calls
