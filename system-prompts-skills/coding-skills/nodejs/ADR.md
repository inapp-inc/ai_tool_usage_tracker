# Architectural Decision Records — Node.js

**Project:** InApp TMO Node.js Development
**Document Version:** 1.0 | **Date:** 24-Aug-2023
**Author:** Soumya Lakshmi V | **Reviewer:** Harilal K M

---

## ADR-NODE-001: Adopt a Four-Layer Architecture (Controller / Service / Model / Middleware)

**Status:** Accepted

**Context:**
Flat, monolithic Node.js applications mix HTTP handling, business rules, and database access in a single file or module, making them hard to test, maintain, and scale.

**Decision:**
All Node.js applications must be structured into four explicit layers:
1. **Controller** — handles HTTP request/response
2. **Service** — contains business logic; no direct DB calls
3. **Model / Data Access** — all database interactions abstracted here
4. **Middleware** — handles cross-cutting concerns (auth, logging, validation)

**Consequences:**
- Clear separation of concerns improves testability: services can be unit-tested without an HTTP server.
- Controllers remain thin and easy to reason about.
- New team members can orient themselves quickly.
- Requires discipline to prevent business logic creeping into controllers.

---

## ADR-NODE-002: Manage Configuration via Environment Variables (dotenv)

**Status:** Accepted

**Context:**
Hardcoding database URLs, API keys, and other environment-specific configuration values in source code makes secrets visible in version control and forces code changes for environment switches.

**Decision:**
All environment-specific configuration must be managed through environment variables loaded via `dotenv`. A `.env.example` file (containing keys but no real values) must be committed; the actual `.env` file must be in `.gitignore`.

**Consequences:**
- Secrets are never committed to version control.
- Applications can be deployed across environments by swapping `.env` values.
- Developers must copy `.env.example` to `.env` on initial setup — this must be documented in `README.md`.

---

## ADR-NODE-003: Enforce Pre-commit Quality Gates with Husky

**Status:** Accepted

**Context:**
Code quality degradation often occurs incrementally when developers skip linting or tests before committing. Relying on manual discipline is insufficient for a team environment.

**Decision:**
**Husky** must be configured to run `npm run lint && npm test` as a mandatory pre-commit hook. Commits that fail either check are rejected.

**Consequences:**
- Code quality floor is maintained automatically.
- Slightly slower commits (test run time), mitigated by running only fast unit tests in the pre-commit hook.
- All developers must install Husky on project setup (handled automatically via `prepare` npm script).

---

## ADR-NODE-004: Prefer async/await Over Raw Promises and Callbacks

**Status:** Accepted

**Context:**
Callback-based asynchronous code ("callback hell") is difficult to read and error-prone. Raw Promise chains are an improvement but can still obscure control flow. `async/await` provides synchronous-looking code over asynchronous operations.

**Decision:**
All new asynchronous code must use `async/await`. Existing callback-based code should be wrapped or migrated. All `async` functions must use `try/catch` for error handling.

**Consequences:**
- Code is easier to read, debug, and maintain.
- Stack traces in `async/await` code are more informative than in Promise chains.
- Developers must be familiar with `async/await` semantics (e.g., `await` only works inside `async` functions).

---

## ADR-NODE-005: Use Custom Error Classes for Domain-Specific Errors

**Status:** Accepted

**Context:**
Throwing generic `Error` objects across the application makes it difficult for calling code to distinguish between different failure modes and respond appropriately.

**Decision:**
Domain-specific error conditions must be represented as custom classes extending `Error`. These classes must set a descriptive `name` and optionally include additional context properties.

```js
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
  }
}
```

**Consequences:**
- Error handling logic can use `instanceof` checks to branch cleanly.
- API responses can return consistent, meaningful error payloads.
- Error types must be documented as part of service contracts.

---

## ADR-NODE-006: Commit Lock Files and Pin Dependency Versions

**Status:** Accepted

**Context:**
Non-deterministic dependency resolution (where minor/patch version ranges silently resolve to different versions) can introduce breaking changes between environments or developer machines.

**Decision:**
The `package-lock.json` (npm) or `yarn.lock` (yarn) file must always be committed to version control. Production dependencies should use exact or tilde (`~`) versions rather than caret (`^`) ranges for critical packages.

**Consequences:**
- All environments resolve identical dependency trees.
- Security patches still require explicit version bumps (not automatic), which enforces intentional updates.
- Lock file merge conflicts must be resolved carefully by re-running the install command.

---

## ADR-NODE-007: Keep Services Independent of HTTP/Transport Layer

**Status:** Accepted

**Context:**
When service functions directly access `req`/`res` Express objects, they become tightly coupled to the HTTP transport layer, making them impossible to test without spinning up an HTTP server.

**Decision:**
Service functions must accept plain data arguments (not `req`/`res`) and return plain data or throw errors. Controllers are solely responsible for extracting data from requests and formatting HTTP responses.

**Consequences:**
- Services are fully unit-testable in isolation.
- Services can be reused from CLI scripts, message queue consumers, or other non-HTTP entry points.
- Controllers remain thin adapters — easier to review and change.
