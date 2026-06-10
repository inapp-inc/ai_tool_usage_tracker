# Architectural Decision Records — Python

**Project:** InApp TMO Python Development
**Document Version:** 1.0 | **Date:** 20-Mar-2024
**Authors:** Darshna Venugopal, Anupam B | **Reviewer:** Rohith R

---

## ADR-PY-001: Mandate Python 3 for All New Projects

**Status:** Accepted

**Context:**
Python 2 reached end-of-life on 1 January 2020 and no longer receives security patches. Maintaining dual-version compatibility adds complexity with no long-term benefit.

**Decision:**
All new Python projects must target **Python 3** (minimum version specified in `pyproject.toml` or `setup.cfg`). Python 2 code must be migrated to Python 3 when significantly modified.

**Consequences:**
- Access to modern Python features (f-strings, `asyncio`, `dataclasses`, etc.).
- Security vulnerabilities in Python 2's standard library are not a concern in new work.
- Legacy Python 2 codebases require a migration plan before major changes.

---

## ADR-PY-002: Enforce PEP 8 via Black Auto-Formatter and flake8 Linter

**Status:** Accepted

**Context:**
Inconsistent code style across a team creates unnecessary diffs, cognitive overhead during code review, and maintainability issues over time.

**Decision:**
- **Black** is the mandatory code formatter. Its opinionated, zero-config approach removes style debates.
- **flake8** is the mandatory linter for catching unused imports, undefined names, and other issues.
- Both tools must be run as pre-commit hooks (using `pre-commit`).
- CI pipelines must fail on any formatting or linting violations.

**Consequences:**
- Code style is enforced automatically; code review focuses on logic and design.
- All developers must install and configure `pre-commit` on project setup.
- Black's formatting decisions are not up for debate — they are adopted as-is.

---

## ADR-PY-003: Require Virtual Environments for Every Project

**Status:** Accepted

**Context:**
Installing Python packages globally conflicts between projects with different dependency versions and makes it impossible to reproduce a known-good environment on another machine.

**Decision:**
Every Python project must use an isolated virtual environment (`venv`, `virtualenv`, or `conda`). The environment must be created from a pinned `requirements.txt` or `pyproject.toml`. The virtual environment directory must be in `.gitignore`.

**Consequences:**
- Dependency environments are reproducible and isolated.
- `requirements.txt` or lockfile must be committed and kept up to date.
- CI pipelines create a fresh virtual environment for each run.

---

## ADR-PY-004: Add Type Hints to All Public Function Signatures

**Status:** Accepted

**Context:**
Dynamically typed Python code is flexible but loses clarity as codebase size grows. Without type hints, IDEs cannot provide meaningful autocompletion and bugs from type mismatches are caught only at runtime.

**Decision:**
All public functions and methods must include parameter and return type hints following PEP 484. **mypy** must be configured and run as part of the linting step.

```python
def get_user(user_id: int) -> Optional[User]:
    ...
```

**Consequences:**
- IDEs provide accurate autocompletion and early error detection.
- mypy catches type errors before runtime.
- Developers must be familiar with Python's typing module.
- Gradual adoption is acceptable for legacy code; new code must always be typed.

---

## ADR-PY-005: Use Specific Exception Handling — No Bare `except:`

**Status:** Accepted

**Context:**
Bare `except:` clauses catch all exceptions including `SystemExit`, `KeyboardInterrupt`, and `GeneratorExit`, masking serious errors and making debugging extremely difficult.

**Decision:**
All `except` clauses must specify the exception type(s) being caught. A bare `except:` or `except Exception:` without logging and re-raising is prohibited. Domain-specific error conditions must use custom exception classes (extending `Exception`) ending in `Error`.

```python
# Required
except (ValueError, KeyError) as e:
    logger.error("Input error: %s", e)

# Prohibited
except:
    pass
```

**Consequences:**
- Unexpected errors propagate correctly and are visible in logs.
- Debugging time is reduced significantly.
- Developers must understand which exceptions a function can raise.

---

## ADR-PY-006: Use Generators for Large Dataset Processing

**Status:** Accepted

**Context:**
Loading large datasets entirely into memory (e.g., as lists) can exhaust available RAM and cause application crashes or severe performance degradation.

**Decision:**
Data processing pipelines that iterate over large collections must use **generators** (`yield`) or generator expressions instead of materialising full lists. Libraries such as `itertools` should be used for lazy transformations.

**Consequences:**
- Memory usage stays bounded regardless of dataset size.
- Processing begins immediately (lazy evaluation) rather than waiting to load all data.
- Generators can only be iterated once — code must account for this where re-iteration is needed.

---

## ADR-PY-007: Manage Dependencies via pip with Pinned requirements.txt (or Poetry)

**Status:** Accepted

**Context:**
Unpinned dependencies resolve to different versions over time, breaking reproducibility and introducing unvetted security patches or breaking changes into production environments.

**Decision:**
Production dependencies must be pinned to exact versions in `requirements.txt` (generated by `pip freeze`) or managed with **Poetry** (which produces a lockfile). Development dependencies are tracked separately in `requirements-dev.txt` or `[tool.poetry.dev-dependencies]`. Dependencies must be audited regularly for CVEs using `pip-audit` or `safety`.

**Consequences:**
- All environments resolve identical dependency trees.
- Security updates require explicit, reviewed version bumps.
- Dependency files must be updated when packages are added or upgraded.

---

## ADR-PY-008: Write Tests with pytest Following the AAA Pattern

**Status:** Accepted

**Context:**
Python's built-in `unittest` module is verbose and requires class-based test organisation. The absence of a test standard leads to inconsistent, hard-to-read test suites.

**Decision:**
**pytest** is the standard testing framework. All tests must follow the **Arrange-Act-Assert (AAA)** pattern. Fixtures must be used for test setup/teardown. `unittest.mock` or `pytest-mock` must be used to isolate units from external dependencies.

**Consequences:**
- Tests are concise, readable, and consistently structured.
- pytest's fixture system simplifies complex test setup.
- CI must be configured to run `pytest` on every push.
