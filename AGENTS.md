# oriz-screen-watch — agent guide

screener.in fundamentals + Nifty500-Value-50-style value-score tracker. Daily ~8am IST weekdays.

> Self-contained rules. Source of truth: chirag127/workspace/knowledge/. Manual sync.

<!-- CANONICAL-RULES v1 (manual sync — source of truth: chirag127/workspace/knowledge/) -->
<!--
  This block is copied verbatim into every active repo's AGENTS.md so rules
  enforce even when the repo is cloned/opened standalone (outside the workspace
  umbrella). MANUAL SYNC: when a rule changes, edit the source in
  workspace/knowledge/ AND hand-update this block in each repo. The v1 marker
  makes stale copies greppable. Full rule text lives in workspace/knowledge/.
-->

## Fleet rules (canonical — apply on every task)

### Prose + output
- **Caveman/terse.** Drop articles, filler, pleasantries, hedging. Fragments > sentences. Answer in word 1 — no preamble, no restatement. Code/data BEFORE prose. Explanation ≤3 lines trivial, ≤10 complex. Concrete not abstract (file:line, exact command, next action). Same terseness for commit messages, PR/issue bodies, code comments. Full sentences ONLY for irreversible-action confirmations (`rm -rf`, force-push, `DROP TABLE`, prod deploy).
- **Terse GitHub issues.** Bug ≤150 words, feature ≤100, comment ≤50. Use repo's template. No speculation/unverified versions/API names. Shorter = fewer hallucinations.

### Code
- **Minimum everything.** Smallest unit that works. LOC/tool-calls/files/imports = what the task needs, not one more. Zero comments unless the line is non-obvious. Trivial fix ≤3 tool calls, routine ≤10, multi-step ≤30 (else delegate).
- **The ladder** (stop at first rung): does it need to exist? → native platform/OS/browser? → already in codebase (reuse)? → stdlib? → one line? → only then minimal own code. Trace the problem end-to-end before coding.
- **No speculative scaffolding, no defensive code for impossible cases, no premature optimization.** `// shouldn't happen` → delete the code. **Edit > Write** (Write only for new files / full replacement). Reuse existing patterns/style even if suboptimal. Don't re-read unchanged files.
- **MAXIMIZE community packages, MINIMIZE own code.** Reach for a well-kept package before writing logic; every line not written is a line not maintained. Own code only where no package fits. Shared own-code = the atomic `@chirag127/*` set — reuse mechanism, theme each site's OWN look.
- **Build COMPLETE, not MVP.** Full feature set, latest dep versions (beta/alpha ok when newest), unit + integration tests everywhere. Ship same session.

### Code intelligence — codebase-memory-mcp FIRST
- On ANY code question use a **cbm** tool BEFORE Grep/Glob/Read: `search_graph` (find symbol), `trace_path` (callers/callees/blast-radius), `get_code_snippet` (exact source), `get_architecture` (overview), `query_graph` (openCypher), `search_code` (grep over indexed), `detect_changes` (diff impact). If the repo isn't indexed → `index_repository` first. Grep/Read only for non-code files or a file you're about to edit. **Use cbm VERY frequently** — 120× fewer tokens than grep/read; many calls per task is good.

### Git
- **main only.** Direct commit on own repos (`chirag127/*`), push by default, never force-push main. Conventional commits (they ARE the changelog). Branches only for upstream PRs. Identity = chirag127 noreply. Scan for secrets before push (no hardcoded secrets; sops+age vault).

### Web + facts
- **Search the web ≥2× before any non-trivial decision** on tools/pricing/library-status/URLs (two phrasings, cross-check). No memory-only answers on externally-knowable, mutable facts.

### Product + security posture
- **No auth on FREE surfaces** — free features 100% public; auth ONLY gates paid goods. Clerk = shared `*.oriz.in` SSO; `PUBLIC_CLERK_PUBLISHABLE_KEY` client-side, secret key server/deploy only, never `PUBLIC_*_SECRET`.
- **No card-on-file for own tooling** (donations via BMC/GH-Sponsors/UPI); customers may pay any method. Never hit free-tier quotas.
- **Every site its OWN distinct visual identity** — reuse `@chirag127/*` for mechanism/a11y/token-contract; never reuse another site's palette/type/layout/motion/signature. Run the frontend-design process per site.

### Interaction (STT-friendly)
- User uses speech-to-text: infer intent from typos/homophones, pick the most-likely reading, STATE it, proceed. Don't ask the user to re-type. Ask only when truly blocked.

<!-- /CANONICAL-RULES v1 -->

## Project-specific (this repo)

Python scraper repo (git-as-DB, GitHub Actions cron). Own visual identity: "editorial ledger" — warm paper, teal ink, Fraunces serif + IBM Plex Mono. NOT the i2i gold/dark palette.

- **Data source**: screener.in company pages are SSR HTML (VERIFIED 2026-08-14: `GET https://www.screener.in/company/<TICKER>/` → 200, no auth, no browser). Parse `#top-ratios` (`li > .name` / `.value`). httpx + selectolax. **Verify DOM before touching the parser** — fetch the real page, never guess selectors. Screener's top block for NSE names exposes Market Cap, Current Price, High/Low, Stock P/E, Book Value, Dividend Yield, ROCE, ROE, Face Value — but NOT Sales (S/P factor is legitimately absent for most; parser supports it if present). P/B is DERIVED = price / book value.
- **NEVER fabricate** — a ratio absent from the page = `null`. The value score averages over the factors a stock HAS.
- **Value score** = NSE Nifty500 Value 50 replica: E/P, B/P, S/P, DivYld → cross-sectional z-score each, equal-weight mean → `(1+z)` if z>0 else `1/(1−z)`. Alt = BSE-Enhanced 3-factor (no DivYld). `scorer.py` owns the math; deterministic + unit-tested.
- **git-as-DB**: `data/stocks.json` (latest) + `data/history/<date>.json` (daily) + `data/notify-state.json` (dedup). The cron MUST commit `data/` back with `git pull --rebase --autostash origin main` before push — else dedup breaks and alerts repeat.
- **Notifications**: single Telegram bot `oriz127_bot`; `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (GitHub secrets). Fire ONLY when a stock NEWLY enters the top-N value rank (`NOTIFY_TOP_N`, default 10). Degrades gracefully when unset.
- **cron reliability**: `concurrency` queue (cancel-in-progress: false), off-minute cron `17 2 * * 1-5`, rebase-before-push guard, `if: failure()` Telegram alert. GitHub schedule cron is best-effort.
- **Tests**: pytest, HTTP fully MOCKED — the parser golden test reads `tests/fixtures/screener_tcs.html` (real captured page), never hits the network. `py -m pytest -q` on this Windows box (`py` launcher).
- **Config**: everything in `src/screen_watch/config.py`. TICKERS overridable via `data/watchlist.json` > env `SCREEN_WATCH_TICKERS` > default.
- **Dashboard**: static `dashboard/` reads `data/stocks.json`, deployed to GitHub Pages by `deploy.yml`.
