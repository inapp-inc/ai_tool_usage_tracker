# PHP Coding Skills Reference

**Source:** PHP Coding Guidelines v1.0 (20-Feb-2024)
**Owner:** InApp TMO | **Authors:** Niranjana Anil, Tinu Sam | **Reviewer:** Nittu Joseph

---

## 1. Project Setup & Structure

- Use XAMPP, WAMP, or a standalone Apache/PHP/MySQL stack for local development.
- Organise code into a modular folder structure; place public-facing files in `/public`.
- Keep folder nesting shallow; use consistent, descriptive names for files and folders.
- Store environment-specific configuration in config files or environment variables — never in source code.

---

## 2. Component Structure Architecture

- Apply the **Model-View-Controller (MVC)** pattern to separate concerns:
  - **Model** — data and business logic
  - **View** — presentation layer
  - **Controller** — orchestrates requests and responses
- Follow **PHP-FIG PSR-1, PSR-2** standards for coding style and naming.
- Use **dependency injection** to manage component dependencies; avoid global service locators.
- Every class or function must have a **single, well-defined responsibility** (SRP).
- Promote reuse through classes, traits, and namespaces.

---

## 3. Coding Guidelines

### Tags & Structure
- Always use the long `<?php ?>` tags — never the shorthand `<? ?>`.
- Omit the closing `?>` tag at the end of PHP-only files.
- One statement per line; no trailing whitespace.
- Indent with **4 spaces** (no tabs).

### Naming Conventions
| Element | Convention | Example |
|---|---|---|
| Classes | UpperCamelCase | `UserController`, `ProductService` |
| Abstract classes | UpperCamelCase + `Abstract` suffix | `BaseRepositoryAbstract` |
| Interfaces | UpperCamelCase + `Interface` suffix | `PaymentGatewayInterface` |
| Variables | lowerCamelCase | `$userName`, `$productList` |
| Private/Protected vars | lowerCamelCase with `_` prefix | `$_secretKey` |
| Functions/Methods | lowerCamelCase, no underscores | `getUserData()`, `calculateTotal()` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| PHP keywords | lowercase | `true`, `false`, `null` |

- Use single quotes for literal strings; double quotes only when embedding variables.
- Avoid abbreviations in function names; use present-tense action words.

### Control Structures
- One space after the control keyword: `if (`, `for (`, `while (`.
- No space after the opening parenthesis or before the closing parenthesis.
- One space between `)` and `{`.
- Always enclose structure bodies in braces, even for single-line bodies.
- Use `elseif` (not `else if`).
- Every `switch` must have a `default` case; mark intentional fall-through with `// no break`.

### Comments & Documentation
- Use PHPDoc DocComments for all classes, methods, and properties.
- Single-line: `/** This is a comment. */`
- Multi-line: `/** \n * Description\n */`
- Remove dead/commented-out code and debug `print`/`var_dump` statements before committing.

---

## 4. Database Access

- Define a single, centralised method for database connections using **PDO** or MySQLi.
- Store connection details in environment variables or config files — never inline.
- **Always use parameterised queries / prepared statements** — no string concatenation for SQL.
- Sanitise and validate all user input before it reaches the database.
- Use ORM frameworks (Eloquent/Laravel, Doctrine) for complex data access.
- Implement connection pooling for efficient connection reuse.
- Use database transactions to maintain data integrity.
- Index database columns appropriately for query performance.
- Use lazy loading; avoid N+1 queries.

---

## 5. Dependency Management (Composer)

- Use **Composer** for all PHP dependency management.
- Define dependencies in `composer.json`; commit both `composer.json` and `composer.lock`.
- Separate `require` (production) from `require-dev` (development-only) dependencies.
- Add a `.gitignore` entry for the `vendor/` directory.
- Pin PHP version constraints in `composer.json`.
- Favour well-maintained, widely adopted packages with clear licensing.
- Use `--dev` flag for development-only packages.
- Regularly run `composer update` and audit for vulnerabilities.

### Recommended Libraries
| Library | Purpose |
|---|---|
| Doctrine ORM | Object-Relational Mapping |
| PHPUnit | Unit testing |
| Guzzle | HTTP client / API calls |
| Carbon | Date/time manipulation |
| PHPMailer | Email sending |
| PHPSpreadsheet | Spreadsheet (XLSX/CSV) handling |
| Parsedown | Markdown to HTML |

---

## 6. Security Considerations

- Protect against **SQL injection**: parameterised queries always.
- Protect against **XSS**: escape all output via `htmlspecialchars()`.
- Protect against **CSRF**: use token validation on form submissions.
- Encrypt sensitive data at rest and in transit (HTTPS + field-level encryption).
- Implement rate limiting to protect against DDoS and brute-force attacks.
- Keep PHP and all dependencies up to date; patch known CVEs promptly.
- Implement role-based access control (RBAC).

---

## 7. Performance Optimisation

- Cache frequently accessed, rarely changed data (Redis, Memcached, file cache).
- Minimise database queries; use eager loading where appropriate.
- Optimise slow queries with EXPLAIN and proper indexing.
- Use lazy loading for related data to avoid unnecessary fetches.

---

## 8. Testing

- Write **unit tests** (PHPUnit) for all service and model logic.
- Write **integration tests** for controllers and database interactions.
- Run tests automatically in CI before merging.
- Test on multiple browsers/devices for front-end compatibility.

---

## 9. Laravel-Specific Guidelines

- Follow Laravel MVC conventions: routes → controllers → services → models.
- Use Eloquent ORM for database interactions.
- Leverage Laravel's built-in authentication, middleware, and validation.
- Store app configuration in `.env` and access via `config()` helpers.
- Implement localisation support using Laravel's `lang/` directory.

---

## Quick Checklist

- [ ] Long `<?php` tags used; no closing `?>` at end of pure PHP files
- [ ] Indentation is 4 spaces, no tabs
- [ ] MVC pattern applied
- [ ] All DB queries use parameterised statements
- [ ] Composer used for dependencies; `composer.lock` committed
- [ ] PHPDoc comments on all public classes and methods
- [ ] No hardcoded credentials or config values
- [ ] Dead code and debug prints removed before commit
- [ ] XSS, CSRF, and SQL injection protections in place
- [ ] PHPUnit tests written and passing
