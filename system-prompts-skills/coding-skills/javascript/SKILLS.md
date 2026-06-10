# JavaScript Coding Skills Reference

**Source:** JavaScript Coding Guidelines
**Owner:** InAppTMO

---

## Core Coding Skills

### 1. Variable Declarations
- Declare all variables at the top of their scope (function-level scoping, not block-level in legacy JS).
- Group all `var` declarations using a single `var` keyword with comma separation where appropriate.
- Declare loop variables and cached selectors **outside** the `for` statement to avoid repeated evaluation.
- Use `const` for objects and arrays to prevent accidental type reassignment.
- Use `let` for block-scoped mutable variables; avoid `var` in ES6+ code.

```js
// Good – cache outside the loop
var container = document.getElementById('container');
for (var i = 0, len = someArray.length; i < len; i++) {
  container.innerHTML += 'my number: ' + i;
}
```

### 2. Code Template & Closure Pattern
- Wrap all JS files in an IIFE (Immediately Invoked Function Expression) using `(function() { 'use strict'; ... })();`
- Place `'use strict'` at the top of every closure.
- Define all static DOM selectors in a dedicated `el` object within the app namespace.
- Separate concerns into `init`, event handler, and plugin initialisation functions.

### 3. Namespace & Global Variables
- Minimise global variable usage — contain all code within a single namespace/closure.
- Avoid inline JavaScript; keep all JS in `.js` files, not embedded in HTML.

### 4. DOM & jQuery
- Cache jQuery selectors for non-dynamic elements; never recreate selectors inside loops.
- Include all `<script>` tags just above the closing `</body>` tag.
- Include stylesheets inside the `<head>` tag.

### 5. Syntax Conventions
- End every statement with a semicolon.
- Use `===` (strict equality) instead of `==` (loose equality) in all comparisons.
- Follow One True Brace Style (OTBS): opening braces on the same line as the statement.
- Use braces for all `if/else/for/while/try` blocks — never omit them even for single-line bodies.
- Place commas and semicolons with no preceding space; place the `?` and `:` of a ternary with spaces on both sides.

### 6. Object & Array Best Practices
- Use literals (`{}`, `[]`) instead of constructors (`new Object()`, `new Array()`).
- Declare objects and arrays with `const` to prevent type mutation.
- Opening bracket of an object on the same line as the object name; closing bracket on a new line with a trailing semicolon.
- Do not add a comma after the last property-value pair.

### 7. Functions
- Always provide default values for optional parameters to prevent `undefined` errors.
- Always end `switch` statements with a `default` case.
- Never use `eval()` — it is both a security risk and a performance problem.
- Use named functions and action-verb naming to convey intent.

### 8. Naming Conventions
| Element | Convention | Example |
|---|---|---|
| Variables & functions | camelCase | `getUserData`, `totalAmount` |
| Constants | UPPER_SNAKE_CASE | `MAX_LENGTH`, `API_KEY` |
| Global variables | UPPERCASE (optional) | `APP_CONFIG` |
| Boolean-returning functions | prefix `is`/`has`/`can` | `isEmpty()`, `hasPermission()` |

### 9. Spacing & Formatting
- Maximum line length: 80 characters soft limit, 100 hard limit.
- No trailing whitespace on any line.
- One blank line at the end of every file.
- Indent with tabs; use spaces only for alignment within lines.
- No filler spaces inside empty constructs `{}`, `[]`, `fn()`.
- `!` negation operator must be followed by a space.

### 10. Multi-line Statements
- Break long lines **after** an operator, not before.
- Split ternary expressions across lines for readability when either branch is complex.

### 11. ECMAScript & Modern JS
- Prefer ES6+ features: `const`/`let`, arrow functions, template literals, destructuring, default parameters.
- Use `===` for all equality checks.
- Avoid legacy patterns like `new Function()`, `new String()`, `new Number()`.

### 12. Support Libraries
- Use `underscore.js` or `lodash` for efficient data transformations (`_.each`, `_.map`, `_.reduce`).

---

## Quick Checklist

- [ ] All code wrapped in an IIFE with `'use strict'`
- [ ] Variables declared at top of scope; no declarations inside loops
- [ ] `===` used for all comparisons
- [ ] No `eval()` usage
- [ ] No inline JavaScript in HTML
- [ ] DOM selectors cached outside loops
- [ ] Objects/arrays declared with `const` where applicable
- [ ] Semicolons at end of every statement
- [ ] OTBS brace style followed
- [ ] camelCase for variables and functions
- [ ] `switch` statements have a `default` case
- [ ] Lines within 100-character limit
