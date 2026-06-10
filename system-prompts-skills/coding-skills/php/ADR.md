# Architectural Decision Records — PHP

**Project:** InApp TMO PHP Development
**Document Version:** 1.0 | **Date:** 20-Feb-2024
**Authors:** Niranjana Anil, Tinu Sam | **Reviewer:** Nittu Joseph

---

## ADR-PHP-001: Adopt MVC Architecture with PSR-1/PSR-2 Standards

**Status:** Accepted

**Context:**
PHP applications without a clear structural pattern tend to mix HTML rendering, business logic, and database queries in the same file, making code impossible to test in isolation and difficult for new developers to navigate.

**Decision:**
All PHP applications must follow the Model-View-Controller (MVC) architectural pattern and adhere to PHP-FIG PSR-1 and PSR-2 coding standards. The preferred framework is **Laravel** (which ships with full MVC support via Eloquent + Blade + Controllers).

**Consequences:**
- Clear separation of concerns: data (Model), display (View), orchestration (Controller).
- Onboarding is faster because the codebase is predictably structured.
- Laravel's ecosystem (Eloquent, Artisan, Middleware) accelerates development.
- Teams must be trained on PSR standards and the chosen framework.

---

## ADR-PHP-002: Use Parameterised Queries / Prepared Statements for All Database Interaction

**Status:** Accepted

**Context:**
Constructing SQL queries via string concatenation with user-supplied input is the leading cause of SQL injection vulnerabilities in PHP applications.

**Decision:**
All database queries must use **PDO prepared statements** or the ORM's parameterised query interface (e.g., Eloquent). Raw string interpolation into SQL is strictly prohibited.

```php
// Required
$stmt = $pdo->prepare("SELECT * FROM users WHERE email = :email");
$stmt->execute([':email' => $userInput]);

// Prohibited
$query = "SELECT * FROM users WHERE email = '$userInput'";
```

**Consequences:**
- SQL injection is prevented at the architectural level.
- Code is marginally more verbose but far safer.
- ORM usage (Eloquent/Doctrine) naturally enforces this pattern.

---

## ADR-PHP-003: Manage All Dependencies via Composer

**Status:** Accepted

**Context:**
Manually copying third-party libraries into the project creates version conflicts, makes updates cumbersome, and obscures the provenance of external code.

**Decision:**
**Composer** is the sole package manager for PHP dependencies. All dependencies must be declared in `composer.json`. Both `composer.json` and `composer.lock` must be committed to version control. The `vendor/` directory must be in `.gitignore`.

**Consequences:**
- Reproducible dependency resolution across all environments.
- Security vulnerabilities in dependencies can be detected with `composer audit`.
- All developers must have Composer installed — document in `README.md`.

---

## ADR-PHP-004: Enforce Strict XSS and CSRF Protections

**Status:** Accepted

**Context:**
PHP applications that render user-supplied content without sanitisation are vulnerable to Cross-Site Scripting (XSS). Forms without token validation are vulnerable to Cross-Site Request Forgery (CSRF).

**Decision:**
- All output containing user-supplied data must be escaped using `htmlspecialchars()` (or the framework's equivalent, e.g., Blade's `{{ }}` auto-escape).
- All state-modifying forms must include and validate a CSRF token (Laravel's `@csrf` directive).
- Security measures are not optional and must be applied by default.

**Consequences:**
- Entire class of XSS and CSRF vulnerabilities is mitigated.
- Developers must use the framework's templating engine (Blade) rather than raw PHP in views to benefit from automatic escaping.

---

## ADR-PHP-005: Use Environment Variables for All Configuration

**Status:** Accepted

**Context:**
Hardcoding database credentials, API keys, and service URLs in PHP source files exposes sensitive data in version control and makes multi-environment deployment error-prone.

**Decision:**
All environment-specific configuration must be stored in `.env` files (managed with Laravel's `vlucas/phpdotenv` or equivalent). Production secrets must be injected as actual environment variables, not from a committed `.env` file. A `.env.example` file with keys but no values must be committed.

**Consequences:**
- Credentials are never exposed in version control.
- Switching between environments (dev/staging/prod) requires only swapping `.env` values.
- Developers must run `cp .env.example .env` on first setup — document in `README.md`.

---

## ADR-PHP-006: Apply Single Responsibility Principle to Classes and Functions

**Status:** Accepted

**Context:**
Large "god classes" or functions that do many things simultaneously are difficult to test, debug, and extend. This has been a common pattern in legacy PHP codebases.

**Decision:**
Every class must have one primary responsibility. Every function or method must do one thing. Business logic must be in service classes, not controllers. Data access must be in models/repositories, not services or controllers.

**Consequences:**
- Classes and functions are individually testable.
- Code reuse is increased — a single service can be called from multiple controllers or queued jobs.
- Requires discipline and code review to prevent regression toward monolithic classes.

---

## ADR-PHP-007: Write PHPUnit Tests for All Business Logic

**Status:** Accepted

**Context:**
PHP applications without automated tests rely on manual QA, which is slow and error-prone, especially as the codebase grows.

**Decision:**
**PHPUnit** is the standard testing framework. Unit tests must be written for all service-layer logic. Integration tests must cover controllers and database interactions. Tests must run automatically in the CI pipeline.

**Consequences:**
- Regressions are caught early in the development cycle.
- Test files must be maintained alongside source code changes.
- Requires CI pipeline configuration to run `composer test` on every push.
