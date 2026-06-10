# Architectural Decision Records — JavaScript

**Project:** InAppTMO JavaScript Development
**Owner:** InAppTMO

---

## ADR-JS-001: Encapsulate All Code in IIFEs with Strict Mode

**Status:** Accepted

**Context:**
JavaScript's function-level (not block-level) scoping and its permissive default mode allow variables and functions to leak into the global scope, causing naming collisions and unpredictable behaviour in multi-file applications.

**Decision:**
Every JavaScript file must be wrapped in an Immediately Invoked Function Expression (IIFE) and must declare `'use strict'` at the top of the closure.

```js
(function() {
  'use strict';
  // all code here
})();
```

**Consequences:**
- Global namespace pollution is eliminated.
- Strict mode catches common coding mistakes early (undeclared variables, duplicate params, etc.).
- All developers must be comfortable with the IIFE pattern.

---

## ADR-JS-002: Use Strict Equality (`===`) Over Loose Equality (`==`)

**Status:** Accepted

**Context:**
JavaScript's `==` operator performs implicit type coercion, which produces unexpected results (e.g., `0 == ''` is `true`). This is a common source of hard-to-find bugs.

**Decision:**
All equality comparisons must use `===` (strict equality) and `!==` (strict inequality). The use of `==` and `!=` is disallowed.

**Consequences:**
- Code behaviour is predictable and explicit.
- Developers must be conscious of types when writing comparisons.
- Linting rules (ESLint `eqeqeq`) can enforce this automatically.

---

## ADR-JS-003: Separate JavaScript from HTML — No Inline Scripts

**Status:** Accepted

**Context:**
Mixing JavaScript inside HTML via inline `onclick`, `onload` attributes, or embedded `<script>` blocks makes both the markup and the logic harder to read, test, and maintain.

**Decision:**
All JavaScript must reside in dedicated `.js` files. Inline JavaScript in HTML is prohibited. Script tags must be placed immediately before the closing `</body>` tag; stylesheets must be in `<head>`.

**Consequences:**
- Clear separation of concerns between structure (HTML) and behaviour (JS).
- JS files are individually cacheable and testable.
- Requires consistent project layout discipline.

---

## ADR-JS-004: Adopt camelCase Naming and UPPER_SNAKE_CASE Constants

**Status:** Accepted

**Context:**
Inconsistent naming conventions reduce readability and increase the cognitive load for new developers joining the project.

**Decision:**
- Variables and functions: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Boolean-returning functions: prefix with `is`, `has`, or `can`

**Consequences:**
- Codebase is consistently readable and scannable.
- Reviewers can quickly identify constants vs mutable variables.
- Linters can enforce naming conventions automatically.

---

## ADR-JS-005: Prefer Object/Array Literals Over Constructors

**Status:** Accepted

**Context:**
Using constructor functions (`new Object()`, `new Array()`, `new String()`) is verbose, slower, and can be misused. Literal syntax is idiomatic JavaScript.

**Decision:**
Always use literals: `{}` instead of `new Object()`, `[]` instead of `new Array()`, `""` instead of `new String()`, `false` instead of `new Boolean()`, and function expressions instead of `new Function()`.

**Consequences:**
- Cleaner, more idiomatic code.
- Avoids subtle bugs introduced by `new Boolean(false)` being truthy.
- Slightly reduced verbosity.

---

## ADR-JS-006: Cache DOM Selectors and Avoid Lookups Inside Loops

**Status:** Accepted

**Context:**
Repeated DOM queries inside loops cause significant performance degradation in applications with complex DOM structures. Each `document.getElementById()` or jQuery selector call traverses the DOM tree.

**Decision:**
DOM selectors must be cached in variables before use and must never be called inside loops. Static element references should be stored in a dedicated `el` object within the app namespace.

**Consequences:**
- Improved rendering performance, especially in data-heavy views.
- Requires discipline to separate selector caching from logic.

---

## ADR-JS-007: Prohibit `eval()`

**Status:** Accepted

**Context:**
The `eval()` function executes arbitrary string input as code, making it a vector for injection attacks and a barrier to JavaScript engine optimisations.

**Decision:**
The use of `eval()` is strictly prohibited in all application code. ESLint's `no-eval` rule must be enabled.

**Consequences:**
- Eliminates a class of XSS-related security vulnerabilities.
- Code is more optimisable by the JavaScript engine.
- In rare legitimate cases (e.g., dynamic expression evaluation), a safer alternative must be designed and reviewed.
