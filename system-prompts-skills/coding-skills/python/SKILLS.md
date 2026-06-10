# Python Coding Skills Reference

**Source:** Python Coding Guidelines v1.0 (20-Mar-2024)
**Owner:** InApp TMO | **Authors:** Darshna Venugopal, Anupam B | **Reviewer:** Rohith R

---

## 1. Naming Conventions (PEP 8)

| Element | Convention | Example |
|---|---|---|
| Packages | lowercase, underscore-separated | `user_auth`, `data_utils` |
| Modules | lowercase, underscore-separated (prefer single word) | `models`, `user_service` |
| Classes | UpperCaseCamelCase | `UserProfile`, `OrderService` |
| Exception classes | UpperCaseCamelCase + `Error` suffix | `ValidationError`, `DatabaseError` |
| Functions & methods | lowercase, underscore-separated; verb-led | `calculate_average()`, `get_user()` |
| Instance variables | lowercase, underscore-separated | `user_name`, `order_total` |
| Non-public members | prefix with single underscore | `_internal_cache` |
| Name-mangled members | prefix with double underscore | `__private_key` |
| Global variables | lowercase, underscore-separated | `default_timeout` |
| Constants | UPPER_SNAKE_CASE | `MAX_VALUE`, `DEFAULT_TIMEOUT` |
| Instance method arg | always `self` | `def save(self):` |
| Class method arg | always `cls` | `def create(cls):` |

**Key rules:**
- Abbreviations in CamelCase: use `HTTPServer`, not `HttpServer`.
- Avoid single-letter names except for loop counters (`i`, `j`) and universally understood conventions.
- Do not shadow built-in names (`list`, `dict`, `id`, `type`, etc.).

---

## 2. Code Structure & Layout

### Indentation
- Use **4 spaces** per indentation level; never use tabs.
- Be consistent — Python's parser is whitespace-sensitive.

### Line Length
- Limit lines to **79–80 characters**.
- Break long expressions or function calls across multiple lines, maintaining clear structure.

### Import Statements
Organise imports in three groups, separated by a blank line:
1. Standard library imports
2. Third-party library imports
3. Local application/module imports

Use **absolute or explicit relative imports**. Avoid wildcard imports (`from module import *`).

### Whitespace
- Two blank lines before and after top-level function and class definitions.
- One blank line between methods inside a class.
- Use whitespace within functions to separate logical code blocks.
- No trailing whitespace.

### Comments
- Write clear, concise inline comments explaining *why*, not *what*.
- Keep comments up to date with code changes.
- Avoid commented-out dead code in commits.

---

## 3. Python Features & Best Practices

### Python Version
- Use **Python 3** for all new projects. Python 2 is end-of-life.
- Specify the minimum Python version in `pyproject.toml` or `setup.cfg`.

### Virtual Environments
- Always create an isolated virtual environment per project using `venv` or `conda`.
- Never install project dependencies into the global Python installation.
- Include `requirements.txt` or `pyproject.toml` in version control.

### Exception Handling
- Catch **specific** exception types; avoid bare `except:` clauses.
- Use custom exception classes (extending `Exception`) for domain errors.
- Use `finally` for resource cleanup (or prefer context managers).

```python
try:
    result = fetch_data(url)
except ConnectionError as e:
    logger.error("Network error: %s", e)
    raise
```

### List Comprehensions
- Prefer list comprehensions over `map()`/`filter()` for simple transformations — more readable.
- Avoid deeply nested or overly complex comprehensions; break them into explicit loops if needed.

### Lambda Functions
- Use lambdas only for short, simple anonymous functions (e.g., as sort keys).
- Prefer named functions for anything requiring explanation or reuse.

### Generators
- Use generator expressions and `yield` for large datasets to avoid loading all data into memory.

### Decorators
- Use decorators to cleanly implement cross-cutting concerns (logging, authentication, caching).
- Document decorator behaviour in the function's docstring.

### Global Variables
- Minimise use of global variables. Pass data through function arguments and return values.
- Use `global` keyword sparingly and only when necessary.

---

## 4. Documentation & Docstrings

- Write docstrings for all public modules, classes, functions, and methods.
- Use the **Google** or **NumPy** docstring style consistently across the project.
- Docstrings must describe purpose, parameters (`Args:`), return values (`Returns:`), and exceptions (`Raises:`).
- Generate API docs from docstrings using **Sphinx** or **pdoc**.

```python
def calculate_discount(price: float, rate: float) -> float:
    """Calculate the discounted price.

    Args:
        price: The original price.
        rate: The discount rate as a decimal (0.0 to 1.0).

    Returns:
        The discounted price.

    Raises:
        ValueError: If rate is not between 0 and 1.
    """
```

---

## 5. Testing

- Use **pytest** (preferred) or `unittest` for all tests.
- Write unit tests for all functions and methods; integration tests for service interactions.
- Follow Arrange-Act-Assert (AAA) pattern.
- Use fixtures and mocking to isolate units.
- Run tests automatically in CI on every push.
- Strive for meaningful coverage of critical paths.

---

## 6. Code Style & Linting

- Follow **PEP 8** as the baseline style guide.
- Use **Black** for automatic code formatting (zero-config).
- Use **flake8** or **pylint** for linting.
- Use **mypy** for static type checking; add type hints to all function signatures.
- Configure pre-commit hooks to run formatters and linters before every commit.

---

## 7. Dependency Management

- Use **pip** with `requirements.txt` or **Poetry** / **pip-tools** for dependency management.
- Pin exact versions in `requirements.txt` for production deployments.
- Separate development dependencies (`requirements-dev.txt`) from production ones.
- Regularly audit with `pip-audit` or `safety`.

---

## 8. Security Considerations

- Validate and sanitise all external input.
- Never hardcode credentials — use environment variables or a secrets manager.
- Use `ssl`/`TLS` for all network communications.
- Scan dependencies for known CVEs.
- Encrypt sensitive data at rest and in transit.
- Apply authentication and authorisation checks consistently.

---

## 9. Performance

- Profile before optimising (`cProfile`, `line_profiler`).
- Use generators and lazy evaluation for large datasets.
- Leverage built-in data structures (sets, dicts) for O(1) lookups.
- Cache expensive function results with `functools.lru_cache`.
- Use async/await (`asyncio`) for I/O-bound operations.

---

## Quick Checklist

- [ ] PEP 8 naming conventions applied throughout
- [ ] 4-space indentation; no tabs
- [ ] Virtual environment created and activated
- [ ] Imports organised in three groups (stdlib / third-party / local)
- [ ] Docstrings on all public modules, classes, and functions
- [ ] Specific exception types caught; no bare `except:`
- [ ] Type hints added to all function signatures
- [ ] Black formatting applied
- [ ] flake8/pylint passes with no errors
- [ ] Unit tests written and passing in CI
- [ ] No hardcoded credentials
- [ ] `requirements.txt` / `pyproject.toml` committed with pinned versions
