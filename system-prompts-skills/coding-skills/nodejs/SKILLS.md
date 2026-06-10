# Node.js Coding Skills Reference

**Source:** Node JS Coding Guidelines v1.0 (24-Aug-2023)
**Owner:** InApp TMO | **Author:** Soumya Lakshmi V | **Reviewer:** Harilal K M

---

## 1. Project Setup & Structure

### Layered Architecture
Organise every Node.js application into four distinct layers:

| Layer | Folder | Responsibility |
|---|---|---|
| Presentation (Controller) | `controllers/` | HTTP request/response handling, routing |
| Business Logic (Service) | `services/` | Core business rules, CRUD, validation |
| Data Access | `models/` | Database schemas, queries, ORM interaction |
| Middleware | `middleware/` | Auth, logging, validation, cross-cutting concerns |

### Recommended Folder Structure
```
my-nodejs-app/
├── controllers/       # HTTP request handlers
├── models/            # Data models / DB schemas
├── services/          # Business logic
├── routes/            # API route definitions
├── middleware/        # Auth, validation, logging middleware
├── config/            # Database, app config files
├── app.js             # Application entry point
├── package.json
└── README.md
```

### Package Manager
- Initialise with `npm` or `yarn`; commit `package.json` and the lock file (`package-lock.json` or `yarn.lock`).
- Use NPM scripts for all repetitive tasks: linting, testing, starting, and building.

### Environment Variables
- Use `dotenv` to manage environment variables (DB URLs, API keys, tokens).
- Access via `process.env`; never hardcode sensitive values.
- Keep a `.env.example` file in version control; never commit the actual `.env`.

---

## 2. Code Style

### Linting & Formatting
- Use **ESLint** for linting (alternatives: JSLint, JSHint).
- Use **Prettier** for consistent code formatting.
- Configure **Husky** pre-commit hooks to run `lint` and `test` automatically before every commit.

```json
"husky": {
  "hooks": {
    "pre-commit": "npm run lint && npm test"
  }
}
```

### Style Guides
- Follow the [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html) or [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) for conventions not covered locally.

### Naming Conventions
| Element | Convention | Example |
|---|---|---|
| Variables & functions | camelCase | `getUserData()`, `productList` |
| Constants | UPPER_SNAKE_CASE | `MAX_LENGTH`, `API_KEY` |
| Classes | PascalCase | `UserService`, `ProductController` |
| Boolean functions | prefix `is`/`has`/`can` | `isEmpty()`, `hasPermission()` |

- Use **nouns** for variables and class names; **verbs** for function names.
- Add JSDoc comments (`@param`, `@returns`, `@throws`) for all public functions.

---

## 3. Error Handling

### Operational vs Programmer Errors
- **Operational errors** (network timeout, DB connection failure, invalid input): handle gracefully with appropriate HTTP status codes and user-facing messages.
- **Programmer errors** (undefined property access, unresolved promise): fix in code; do not suppress.

### Patterns
- Use `try/catch` for synchronous code and async/await.
- Chain `.catch()` on all Promises.
- Never leave a rejected Promise unhandled.
- Create custom error classes extending `Error` for domain-specific error types.

```js
class CustomError extends Error {
  constructor(message) {
    super(message);
    this.name = 'CustomError';
  }
}
```

- Use HTTP status codes semantically: `404` for Not Found, `400` for Bad Request, `500` for Internal Server Error.

---

## 4. Dependency Management

- Pin exact or tilde versions in `package.json`; commit the lock file.
- Separate `dependencies` (runtime) from `devDependencies` (development-only).
- Regularly audit dependencies with `npm audit` or `yarn audit`.
- Remove unused packages promptly.

---

## 5. Asynchronous Programming

- Prefer `async/await` over raw Promise chains for readability.
- Always `await` all asynchronous operations inside `async` functions.
- Handle errors in `async` functions with `try/catch`.
- Avoid callback-based patterns in new code; use Promise-based APIs.

---

## 6. Security Considerations

- Validate and sanitise all user input before use.
- Store all secrets in environment variables; use a vault in production.
- Implement rate limiting on public APIs.
- Use HTTPS in all environments.
- Keep dependencies up to date and patch known vulnerabilities promptly.

---

## 7. Testing

- Write unit tests for all service-layer functions.
- Write integration tests for controllers and data access layers.
- Use frameworks such as Jest, Mocha, or Chai.
- Run tests automatically in CI as part of pre-merge checks.
- Aim for meaningful coverage — prioritise critical paths over raw percentage targets.

---

## 8. Performance

- Use clustering or worker threads for CPU-intensive tasks.
- Implement caching (Redis, in-memory) for frequently read, rarely changed data.
- Paginate large dataset queries.
- Use connection pooling for database access.

---

## 9. Documentation

- Maintain a `README.md` at the project root covering setup, configuration, and usage.
- Document all APIs (OpenAPI/Swagger recommended).
- Use JSDoc for inline function documentation.

---

## Quick Checklist

- [ ] Layered architecture applied (Controller / Service / Model / Middleware)
- [ ] Environment variables used via `dotenv`; no hardcoded secrets
- [ ] ESLint + Prettier configured
- [ ] Husky pre-commit hooks enforce lint and test
- [ ] All Promises and async operations have error handling
- [ ] Lock file committed
- [ ] Custom error classes used for domain errors
- [ ] Unit and integration tests written and passing in CI
- [ ] JSDoc comments on all public functions
- [ ] `README.md` up to date
