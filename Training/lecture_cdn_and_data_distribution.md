# Data Distribution, Versioning, and Multi-Source Architecture

*A lecture based on the JRB Industries trivia ecosystem build-out, April 2026*

## The Problem We Were Solving

One dataset (~300 trivia questions), multiple consumers in different languages (Python, C++, JavaScript), and the original copy was trapped on a laptop behind a local HTTP server that only the developer's machine could reach. The question: how do you let many programs share one source of truth for data that updates occasionally?

This turns out to be a surprisingly deep topic that touches on CDNs, versioning, caching, graceful degradation, and a philosophical distinction between *what you intended* and *what actually happened*.

---

## Content Delivery Networks (CDNs)

### The cookbook analogy

Imagine you wrote a cookbook. The only copy sits in your kitchen in Boulder. Every time someone in Tokyo wants a recipe, they fly to Boulder, photocopy the page, and fly home. Slow. And if a thousand people want recipes at once, there's a line out your door.

A CDN is like photocopying your cookbook and stashing copies in libraries around the world — Tokyo, London, São Paulo, Sydney. When someone in Tokyo wants a recipe, they walk to their local library instead.

- **Origin** = the original file in your kitchen (the canonical source).
- **Edge servers** (or edge nodes) = the libraries around the world.

### Caching and TTLs

Edge servers don't have every file in advance. When someone in Tokyo asks for a file the edge hasn't seen, the edge fetches it from the origin, hands it to the user, *and keeps a copy* for the next person. That's **caching**.

Each cached copy has a **TTL** (time-to-live) — basically an expiration date. After the TTL expires, the edge throws out its copy and re-fetches from origin next time it's asked.

### Cache invalidation

If you update the origin file, edges can still serve the *old* cached copy until their TTL expires — or you explicitly tell them "throw out your copies." That telling is called a **purge** or **invalidation**, and it's famously one of the hardest problems in computer science. (The old joke: "There are only two hard problems in computer science: cache invalidation and naming things.")

### You're already using a CDN

Vercel's whole pitch is "we put your site on a global edge network." That's why your deployed apps load fast from anywhere — they're not served out of one data center, they're served from an edge close to the user.

---

## jsDelivr: A Free CDN for GitHub

**jsDelivr** is a free public CDN that mirrors public GitHub repos and npm packages. No signup, no API key, no dashboard. You just construct a URL:

```
https://cdn.jsdelivr.net/gh/USER/REPO@VERSION/PATH/TO/FILE
```

Breaking that down:
- `cdn.jsdelivr.net/gh/` — "I want a file from GitHub"
- `USER/REPO` — which repo
- `@VERSION` — a branch, tag, or commit hash (the pinning knob)
- `/PATH/TO/FILE` — path inside the repo

The `@VERSION` part is the interesting one:
- `@main` — latest on the main branch. Cached for about 12 hours.
- `@v1.2.0` — a specific git tag. Cached essentially forever, since tags don't move.
- `@abc123def` — a specific commit hash. Also cached forever.

This is why **tags matter so much**: they're the stable handle that pinning relies on. Branches move, commits are opaque, tags are the human-readable "this is release X" marker.

jsDelivr is funded by sponsors and serves a huge chunk of open-source frontend code. As long as your repo is public, you're a valid user.

---

## Git Tags and Releases

### Tags are the load-bearing thing

A **git tag** is a named pointer to a specific commit. `git tag v0.1.0 && git push --tags` is enough to make jsDelivr able to serve `@v0.1.0`. The tag *is* the version, independent of whether anything else (PyPI, npm, etc.) knows about it.

### GitHub Releases are optional polish

A **GitHub Release** is a layer on top of a tag. It adds a title, release notes, optional binary artifacts, and a pretty page under the repo's "Releases" tab. Functionally, nothing changes — the tag is still the same commit pointer. Releases are documentation and distribution, not versioning.

For a private factory/customer setup between repos you control: tags are enough, skip the Release UI. For a public package like promptukit on PyPI, auto-generated Releases via GitHub Actions are basically free and worth having.

### The immutability rule

Once `v0.1.0` exists and a downstream consumer has pinned to it, **never rewrite that tag**. If you find a typo after tagging, fix it and tag `v0.1.1`. Rewriting a tag means cached copies on jsDelivr are now lying about what they contain, and the whole pinning model breaks.

---

## One Writer, Many Readers: The Factory/Customer Pattern

The clean architecture for "one dataset, many consumers":

1. **One repo is the source of truth.** It defines the schema *and* ships the canonical data.
2. **Consumers pin to specific versions.** Each consumer's code references `@v0.1.550` (or whatever), not `@main`. This makes consumers time capsules — they keep working exactly the same way until *they* choose to upgrade.
3. **Upgrades are explicit.** Bump one version string, rebuild, ship.

This is the same pattern as npm, pip, cargo, Maven — package managers are all doing "pinned dependencies" for code. Here we're doing it for data.

### The sportscar racing analogy

A "factory team" develops the chassis and runs official entries. "Customer teams" (privateers) buy the same chassis and run their own entries under shared technical regulations. The chassis is the schema. The factory team is the canonical repo (promptukit). Customer teams are downstream repos (like CVEN5393) that produce data in the same format on their own schedule.

Each team tags releases independently. The shared schema is what keeps them all compatible.

### What goes wrong if you don't version

Without pinning, consumers get "whatever's on main right now" every time they load. That means:
- You edit a file, and suddenly a deployed game breaks because a new required field appeared.
- You can't reproduce a bug report because you don't know what version the user actually had.
- Two consumers might be running against different versions and you can't tell.

Pinning turns all three of those into non-problems.

---

## Graceful Degradation and Fallback Chains

### The pattern

Don't trust the network. Even a great CDN can be down. A good loader tries sources in order, from best to worst:

1. Try the pinned CDN URL.
2. If that fails, fall back to a locally bundled copy (shipped with the app, always available offline).
3. If *that* fails (corrupted build, etc.), fall back to a hardcoded last-resort.

This is the same pattern as your phone falling back from LTE to 3G to EDGE. "Graceful degradation" means the app gets *worse* but doesn't *break* when conditions deteriorate.

### Fallback as snapshot, not mirror

A bundled fallback is a **snapshot** pinned to some known-good version — possibly older than the CDN version. Resist the temptation to update the fallback on every release. That would recreate the two-sources-of-truth problem in miniature. The whole point of the fallback is that it's a stable floor; update it only when the schema changes in a way the old file can't satisfy.

### Failure isolation with multiple sources

If you have N banks from N repos, one failed CDN fetch shouldn't kill the whole load. The JavaScript primitive that gets this right is `Promise.all` with try/catch *inside each branch* — so each fetch either resolves to data or resolves to a "this one failed, skip it" sentinel. The alternative (`Promise.all` with throws inside) kills all successful fetches the moment one fails, which is exactly backwards.

---

## Declared Intent vs. Observed Reality

One of the most generalizable ideas from the day. Config files say what you *want*; runtime variables say what you *got*. Merging them into one thing feels simpler until the day they disagree — at which point conflation hides the bug.

Concrete example from the trivia game: the bank-selection button initially read the version from the `PROMPTUKIT_VERSION` constant, so it always showed `v0.1.550` regardless of whether the CDN fetch succeeded. Aspirational, not factual. The fix was to track a separate `loadedVersion` field set at each branch of the load (CDN success / local fallback / embedded fallback). Now the button reports what's actually in memory, not what was supposed to be there.

This distinction shows up *everywhere*:
- Browsers show the URL you typed momentarily before switching to the URL after redirects.
- Git distinguishes staged / committed / pushed state.
- Kubernetes has "desired replicas" and "ready replicas" as separate fields.
- Monitoring dashboards separate "expected" from "observed" metrics.

Once you see the pattern, you see it everywhere. It's a foundational concept in building systems that are honest about their own state.

---

## URL as State

When an app can configure itself from the URL — `?bank=cven5393` picks a specific question bank on load — you've entered the land of URLs-as-state.

The promise: if you copy-paste the URL to someone else, they land exactly where you landed. Google Maps encodes lat/lon/zoom this way. YouTube encodes `?t=120` for timestamps. GitHub encodes repo/branch/file/line.

### Query params vs. hash fragments

- `?bank=cven5393` — query param. Sent to the server in HTTP requests.
- `#bank=cven5393` — hash fragment. Stays client-side; the server never sees it.

For a static site where the bank selection is purely a frontend concern, the hash fragment is more honest. Query params are more conventional and show up in analytics, which might be useful.

### Two-way binding

The clean version is bidirectional: URL changes update app state, *and* user actions update the URL. `history.replaceState` updates the URL without reloading or adding a history entry — appropriate for actions where you don't want the back button to fill with noise. `pushState` adds history entries, appropriate if back-navigation should step through states.

### Unknown-value handling

If a URL contains `?bank=oldname` and the app no longer has a bank by that name, fall back to the default rather than showing an empty state. Same principle as the CDN fallback chain: declared intent (URL) vs. observed reality (current bank list) can disagree, and the app has to handle it honestly.

---

## Yak Shaving

A software-culture term: the phenomenon of starting a task, but first needing to do a subtask, which requires a sub-subtask, and six layers deep you realize you've spent three hours on infrastructure that's only tangentially related to what you set out to do.

It's usually said self-deprecatingly. The yak is well-shaved; the original task remains unstarted.

Shaving isn't always wasteful. Infrastructure built during a shave often pays off for years. The honest framing is: notice when you're doing it, decide whether the detour is worth it, and don't kid yourself about what you accomplished.

---

## Reusable Tooling via Shared Schemas

The final insight of the day: if two repos produce data in the same format, tooling that operates on that format works on both unchanged. Moving the `add_questions` skill from one repo to another required zero modification because both repos speak the same schema.

### The shipping container analogy

Standardized shipping containers changed global trade not because the containers themselves are interesting, but because every crane, every ship, every truck, and every port in the world knows how to handle one without custom rigging. The schema is the container. Tooling is the crane. A new repo with the same schema is a new port that already has compatible equipment.

### Keeping tools schema-shaped, not content-shaped

The discipline: resist hardcoding content-specific logic into tools. If a particular bank has content rules, put them in a config file the tool *reads*, rather than baking them into the tool itself. This keeps the crane general-purpose.

---

## Concepts Worth Following Up On

Things worth poking at when curious:

- **GitHub Actions for automated PyPI + tag releases.** Push a tag, Action builds and publishes, tag exists automatically. Keeps PyPI version, git tag, and jsDelivr URL in sync with one push.
- **Subresource Integrity (SRI).** Browser mechanism to verify a fetched file's hash matches an expected value. Overkill for small projects, but the same family of ideas as pinning.
- **Schema versioning within data files.** For multi-source setups, embedding a `schema_version` field inside each data file lets loaders detect incompatibilities at load time, not at bug-report time.
- **Semantic versioning (semver).** The conventional three-number scheme (`major.minor.patch`) where each number has specific meaning about compatibility. Worth knowing even if you don't strictly follow it.

---

## Quick Glossary

- **CDN** (Content Delivery Network): A network of edge servers that cache content geographically close to users.
- **Origin**: The canonical source of a file, usually a single server or repo.
- **Edge server** / **edge node**: A CDN server close to end users that holds cached copies.
- **TTL** (Time-to-Live): How long a cached copy is considered valid before being refreshed.
- **Purge / Invalidation**: Explicitly telling a CDN to drop cached copies of a file.
- **Pinning**: Referencing a specific version (tag, hash, or release) rather than a moving target (branch).
- **Git tag**: A named pointer to a specific commit. Immutable by convention.
- **GitHub Release**: Optional UI layer on top of a tag with notes and artifacts.
- **jsDelivr**: Free public CDN that mirrors GitHub repos and npm packages.
- **Graceful degradation**: System design where failure modes produce reduced but working functionality rather than a crash.
- **Fallback chain**: An ordered list of sources, tried in sequence until one succeeds.
- **Declared vs. observed state**: The distinction between what the app is *supposed to have* and what it *actually has* at runtime.
- **URL as state**: Design pattern where the URL encodes app state so links are shareable and bookmarkable.
- **Yak shaving**: Recursive detour through prerequisite tasks, away from the original goal.
