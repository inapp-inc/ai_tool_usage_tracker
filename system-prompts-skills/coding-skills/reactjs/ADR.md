# Architectural Decision Records — React JS

**Project:** InApp React JS Development
**Document Version:** 1.0 | **Date:** 15-May-2024
**Author:** Ansu R | **Reviewers:** Vivek R, Jackson John, Harilal K M

---

## ADR-REACT-001: Mandate Functional Components with React Hooks

**Status:** Accepted

**Context:**
React's class component API requires lifecycle methods, `this` binding, and boilerplate that increases cognitive overhead and makes logic reuse difficult. React Hooks (introduced in React 16.8) provide a simpler, composable model for managing state and side effects in functional components.

**Decision:**
All new components must be written as **functional components** using React Hooks. Class components are permitted only for Error Boundaries (which currently require `componentDidCatch`) or when consuming a legacy codebase that cannot be migrated immediately.

**Consequences:**
- Components are simpler, shorter, and easier to test.
- Logic is reusable through custom hooks — not possible with class lifecycle methods.
- Team must be proficient in Hooks (`useState`, `useEffect`, `useContext`, `useReducer`, `useMemo`, `useCallback`).

---

## ADR-REACT-002: Use React Hooks + Context API as the Default State Management

**Status:** Accepted

**Context:**
Redux was historically necessary to manage shared state across a React app, but introduced significant boilerplate and complexity. For small-to-medium applications, React's built-in Hooks and Context API provide sufficient state management without the overhead.

**Decision:**
- **React Hooks + Context API** is the default state management approach.
- **Redux Toolkit** (or MobX) is adopted only when the application state is complex (many slices, derived data, time-travel debugging needed) and Context + Hooks proves insufficient.
- Application state (server data, auth) must be separated from UI state (form inputs, modal visibility).

**Consequences:**
- Simpler architecture for most projects.
- Reduced bundle size (no Redux runtime in small apps).
- Teams must design Context providers thoughtfully to avoid re-render cascades from broad context updates.
- Large projects must evaluate Redux Toolkit adoption early, before refactoring becomes painful.

---

## ADR-REACT-003: Isolate Business Logic in Custom Hooks

**Status:** Accepted

**Context:**
Mixing API calls, data transformation, and UI rendering logic inside component bodies makes components hard to test, re-use, and reason about.

**Decision:**
All business logic (data fetching, form state, derived calculations, side effects) must be extracted into **custom hooks** named with the `use` prefix. Components must remain thin: they render UI and call hooks for logic.

**Consequences:**
- Components become purely presentational and are trivially testable.
- Hooks are independently testable without mounting a component.
- Separation must be maintained rigorously through code review.

---

## ADR-REACT-004: Implement Error Boundaries for Rendering Error Isolation

**Status:** Accepted

**Context:**
A JavaScript error in one React component can crash the entire component tree. Without Error Boundaries, users see a blank page with no feedback.

**Decision:**
Every major section of the application (e.g., page layout, data widget, form area) must be wrapped in an **Error Boundary** component. Error Boundaries must render a user-friendly fallback UI and report errors to Sentry (or equivalent).

**Consequences:**
- A single component error is isolated; the rest of the app remains functional.
- Users receive meaningful feedback instead of a blank screen.
- Error Boundaries currently require class components — a thin wrapper class is acceptable for this specific purpose.

---

## ADR-REACT-005: Use React Router v6 for All Client-Side Routing

**Status:** Accepted

**Context:**
Multiple routing approaches in a single codebase (hash routing, history routing, manual URL parsing) create inconsistency and make navigation logic hard to follow.

**Decision:**
**React Router v6** (`react-router-dom`) is the sole routing library. Routes are defined declaratively using `<Routes>` and `<Route>`. Authenticated routes must use a `PrivateRoute` wrapper that redirects unauthenticated users to the login page. Route components must be lazy-loaded with `React.lazy` + `Suspense`.

**Consequences:**
- Consistent navigation patterns across the codebase.
- Code splitting via lazy loading reduces initial bundle size.
- Protected routes enforce authentication at the routing layer.
- All team members must be familiar with React Router v6's breaking changes from v5.

---

## ADR-REACT-006: Enforce Performance Guards with useMemo, useCallback, and React.memo

**Status:** Accepted

**Context:**
React re-renders a component whenever its parent re-renders, even if its own props have not changed. In components with expensive renders or many children, this causes perceptible UI lag.

**Decision:**
- Wrap expensive computed values in `useMemo`.
- Wrap callback functions passed as props in `useCallback` to maintain referential stability.
- Wrap pure presentational components in `React.memo` to skip re-renders when props are unchanged.
- Avoid inline function definitions in JSX (they create new references on every render, defeating `React.memo`).

**Consequences:**
- Reduced unnecessary re-renders improves perceived performance.
- Over-memoisation adds complexity — apply these optimisations to measured bottlenecks, not everywhere by default.
- Developers must understand referential equality to use these hooks correctly.

---

## ADR-REACT-007: Commit Dependency Lockfiles and Use Minimal, Well-Maintained Libraries

**Status:** Accepted

**Context:**
The React ecosystem has a very high rate of package churn. Projects with many dependencies and unpinned versions frequently encounter breaking changes and security vulnerabilities.

**Decision:**
- `package-lock.json` (npm) or `yarn.lock` (yarn) must be committed to version control.
- Prefer widely adopted, well-maintained libraries from the recommended list.
- The number of direct dependencies must be minimised — evaluate whether a library is truly needed before adding it.
- Dependencies must be audited with `npm audit` on a regular basis.

**Consequences:**
- Reproducible dependency trees across all environments.
- Smaller bundle size due to fewer dependencies.
- Security vulnerabilities are detected systematically, not by accident.

---

## ADR-REACT-008: Apply Absolute Imports for Module Resolution

**Status:** Accepted

**Context:**
Relative import paths (e.g., `../../../components/Button`) break during refactoring when files are moved and are difficult to read in deeply nested modules.

**Decision:**
Configure `jsconfig.json` (JavaScript) or `tsconfig.json` (TypeScript) to set the project root as a base URL, enabling absolute imports (e.g., `import Button from 'components/Button'`). All new imports must use absolute paths; relative paths are only acceptable for files in the same directory.

**Consequences:**
- Imports are readable and do not break when files are relocated.
- IDEs with absolute path support provide accurate autocompletion.
- Initial configuration is required in the project setup — document in `README.md`.
