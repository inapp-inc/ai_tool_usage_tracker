# React JS Coding Skills Reference

**Source:** React JS Development Coding Guide Line v1.0 (15-May-2024)
**Owner:** InApp | **Author:** Ansu R | **Reviewers:** Vivek R, Jackson John, Harilal K M

---

## 1. Project Setup & Structure

- Scaffold with `npx create-react-app <AppName>` or Vite for new projects.
- Ensure Node.js and npm/yarn are installed; choose one package manager consistently.
- Keep the folder structure **flat** — avoid deep nesting.
- Use consistent, descriptive naming for files and folders.
- Configure **absolute import paths** (via `jsconfig.json` or `tsconfig.json`) to avoid brittle relative import chains.

### Recommended Folder Structure
```
src/
├── components/       # Shared/reusable UI components
├── pages/            # Route-level page components
├── hooks/            # Custom React hooks
├── services/         # API call abstractions (Axios wrappers)
├── store/            # State management (Redux / Context)
├── utils/            # Pure utility/helper functions
├── styles/           # Global stylesheets / theme tokens
└── assets/           # Images, fonts, static files
```

---

## 2. Component Architecture

- **Prefer functional components** with React Hooks over class components.
- Follow the **Single Responsibility Principle** — each component does one thing.
- Keep components small and focused; extract logic into custom hooks.
- Use **prop types** or **TypeScript** to enforce component interface contracts.
- Prefer functional composition over class inheritance.
- Implement reusable, composable components to promote DRY code.
- Separate UI (presentation) from logic (container/hooks).

---

## 3. Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Components | PascalCase | `UserProfile`, `LoginForm` |
| Component files | PascalCase | `UserProfile.js`, `LoginForm.tsx` |
| State variables | camelCase | `isLoading`, `userName` |
| Boolean state | prefix `is`/`has`/`should` | `isVisible`, `hasFetched` |
| Event handlers | camelCase, prefix `handle` | `handleSubmit`, `handleInputChange` |
| Custom hooks | prefix `use` | `useAuth`, `useFetch` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| CSS classes | kebab-case / BEM | `user-card`, `user-card__title` |
| Helper functions | camelCase, verb-led | `formatDate()`, `parseResponse()` |
| Props | camelCase, descriptive | `onSubmit`, `isDisabled` |

---

## 4. Custom Hooks Best Practices

1. Always prefix hook names with `use` (e.g., `useAuth`, `useFormValidation`).
2. Keep each hook focused on a **single concern**.
3. Do not include side effects (data fetching, DOM manipulation) directly in hooks unless that is the hook's sole purpose.
4. Handle errors inside hooks for API/async operations; do not leak raw errors to consumers.
5. Document hooks clearly: purpose, parameters, return values, dependencies.
6. Parameterise hooks to allow flexible reuse.
7. Write tests for every custom hook.
8. Manage `useEffect` dependencies accurately to avoid stale closures and unnecessary re-runs.
9. Use `useMemo` and `useCallback` to prevent unnecessary recalculations and re-renders.
10. Follow React's Rules of Hooks: call at the top level only, never conditionally.

---

## 5. Error Handling & Logging

- Wrap risky code in `try/catch` blocks; never silently swallow errors.
- Assign meaningful error codes to distinguish failure types.
- Display **user-friendly messages** — never expose raw stack traces to users.
- Use **Error Boundary** components to catch rendering errors and show fallback UI.
- Integrate crash reporting tools (Sentry) for production monitoring.
- Handle **network errors** separately from application-level errors.
- Clear error state once the user has taken corrective action.

---

## 6. State Management

- Use **React Hooks + Context API** for small-to-medium applications (replaces Redux in many cases).
- Use **Redux** or **MobX** for complex, large-scale applications with intricate data flows.
- Separate **application state** (server data, auth) from **UI state** (modal open/closed, form input).
- Minimise unnecessary state updates to avoid performance issues.
- Avoid prop drilling — use Context or a state manager when props chain more than 2 levels deep.

---

## 7. Routing

- Use **React Router v6** (`react-router-dom`) for all routing.
- Define routes declaratively with `<Routes>` and `<Route>`.
- Implement **protected routes** (PrivateRoute) for authenticated areas.
- Support **nested routes** to reflect component hierarchy.
- Use **code splitting** with `React.lazy` + `Suspense` to reduce initial load time.
- Create a custom **404 page** for unmatched routes.
- Document route configuration (paths, params, guards).

---

## 8. Performance Optimisation

- Use `React.memo` to prevent unnecessary re-renders of pure components.
- Use `useCallback` for stable function references passed as props.
- Use `useMemo` for expensive computed values.
- Lazy-load routes and heavy components with `React.lazy` + `Suspense`.
- Avoid inline function definitions in JSX (creates new function reference on every render).
- Avoid multiple `useEffect` hooks in a single component — consolidate related effects.
- Remove unused packages, files, functions, variables, and states.

---

## 9. Styling & Theming

- Use a CSS framework (Tailwind CSS, Bootstrap, Ant Design, Material-UI, Prime-React) consistently across the project.
- Use **CSS-in-JS** (styled-components, emotion) or **CSS Modules** for component-scoped styles.
- Use **media queries** and viewport-relative units (`vw`, `vh`, `rem`, `em`) for responsive design.
- Follow **BEM** methodology for plain CSS class naming.
- Test responsive layouts on multiple screen sizes and devices.

---

## 10. Linting & Code Quality

- Use **ESLint** with `eslint:recommended` + `plugin:react/recommended`.
- Use **Prettier** for consistent code formatting.
- Configure pre-commit hooks (Husky + lint-staged) to run lint and format before every commit.
- Keep lines under 80 characters; use ES6+ features (arrow functions, destructuring, spread).
- Organise imports: library imports first, then local imports.
- Avoid magic numbers and hardcoded values — extract to named constants.

---

## 11. Dependency Management

- Commit `package-lock.json` (npm) or `yarn.lock` (yarn) to version control.
- Lock dependency versions; update intentionally after reviewing changelogs.
- Minimise the number of dependencies; prefer well-maintained libraries.

### Recommended Libraries
| Category | Library |
|---|---|
| Forms | Formik, react-hook-form |
| Schema validation | Yup |
| HTTP client | Axios |
| Routing | react-router-dom |
| State management | Redux Toolkit, MobX, React Context |
| UI components | Material-UI, Ant Design, Prime-React |
| Testing | Jest, React Testing Library |
| Charts | D3.js, Chart.js, recharts |
| Dates | date-fns, Day.js, Luxon |
| i18n | react-i18next |
| Error tracking | Sentry |
| Maps | react-leaflet |

---

## 12. Testing

- Use **Jest** + **React Testing Library** for unit and integration tests.
- Test components, hooks, and utility functions.
- Mock API calls and external dependencies.
- Run tests in CI on every push; block merges on test failure.
- Test protected routes and routing edge cases.

---

## Quick Checklist

- [ ] Functional components used throughout (no unnecessary class components)
- [ ] Custom hooks prefixed with `use`; single responsibility
- [ ] Error Boundaries implemented for rendering error isolation
- [ ] ESLint + Prettier configured and passing
- [ ] Husky pre-commit hooks enforcing lint/format
- [ ] React Router v6 used; protected routes in place
- [ ] `useMemo` / `useCallback` used for performance-sensitive code
- [ ] No inline functions passed as JSX props unnecessarily
- [ ] Absolute imports configured
- [ ] Lock file committed; dependencies minimal and up to date
- [ ] Unit tests written and passing in CI
- [ ] Sentry (or equivalent) configured for production error tracking
