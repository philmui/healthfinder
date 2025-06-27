# HealthFinder Frontend – Architecture & Design Guide

_Last updated: 2025-06-27_

---

## 1 . Overview
The **HealthFinder frontend** is a modern **Next.js 15 (App Router)** application written in **TypeScript**.  
Primary goals:

* **Modularity** – loosely coupled, highly cohesive components  
* **Extensibility** – easy addition of new data domains (BioMCP, Trials, Genetics…)  
* **Best-practice UX** – fast, accessible, responsive

The UI communicates with the FastAPI backend only through well-typed JSON APIs; no server-side rendering of Python pages.

---

## 2 . Folder Layout

```
frontend/
├ pages/                 # Route handlers (minimal logic)
│ └ api/auth/[...].ts    # NextAuth callbacks
├ components/            # Re-usable UI (atoms → organisms)
│ ├ layout/              # NavBar, LeftPanel, RightPanel
│ ├ providers/           # ProviderCard, Filters, MapView
│ └ shared/              # Buttons, Inputs, Icons
├ hooks/                 # Custom React hooks (useAuth, useFetch, ...)
├ utils/                 # API client, logger, feature flags
├ styles/                # Tailwind globals, Bootstrap overrides
└ docs/                  # ← you are here
```

_Key principles_

| Principle | Implementation |
|-----------|----------------|
| **Separation of Concerns** | `pages/` handles routing; UI & logic live in `components/` + `hooks/`. |
| **Atomic Design** | Atoms (Button) → Molecules (SearchBar) → Organisms (ProviderSearchPage). |
| **COLR** (Colocate-or-Lift Rule) | Keep a hook/component next to where it is used unless it is shared across features. |

---

## 3 . Routing Strategy

### 3.1 App Router
* File-based routing (`pages/`) for now (stable)  
* Gradual migration to `/app` directory is possible; no tight coupling

```
/search                  # global search (all domains)
/providers               # Provider Finder landing
/providers/[id]          # Provider detail
/clinical-trials         # (flagged off in early milestones)
```

### 3.2 Protection Middleware
`middleware.ts` checks `next-auth` session cookies for routes listed in `AUTH_PROTECTED_ROUTES`.  
SSR pages can use:

```ts
export const getServerSideProps = withAuth(async (ctx) => { … });
```

---

## 4 . State Management

| Layer | Tool | Notes |
|-------|------|-------|
| *Server cache* | SWR (`swr` package) | Stale-while-revalidate + focus revalidation |
| *Client global* | React Context (`AuthContext`, `FeatureFlagContext`) | Minimal, only truly global state |
| *Local component* | useState / useReducer | Keep local where possible |

Why no Redux? Current needs are simple; can introduce Redux Toolkit or Zustand when complexity grows.

---

## 5 . Styling & Theming

* **Tailwind CSS** – utility-first, tree-shaken via `content: [...]`  
* **Bootstrap 5** – for grid & a few ready components; imported via npm; prefix `.bt-` classes through SCSS map to avoid clashing.  
* **CSS Variables** provide light/dark themes. Hook `useTheme()` toggles.

---

## 6 . Authentication Flow

1. **Client** clicks _Sign in with Google_ → NextAuth `/api/auth/signin`  
2. Google OAuth → returns JWT & session cookie (`next-auth.session-token`)  
3. **SSR/Client** side retrieves session via `getServerSession()` / `useSession()`  
4. Tokens forwarded to backend via `Authorization: Bearer <JWT>` header (interceptor in `api.ts`).

`NEXTAUTH_SECRET` equals backend `SECRET_KEY` to allow backend verification (optional).

---

## 7 . API Layer

### 7.1 Axios Wrapper

```ts
// utils/api.ts
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true,
});
```

* **Interceptors** add auth header, handle 401 refresh, log errors with `utils/logger.ts`.
* **Generated Types** – OpenAPI schema → `openapi-typescript` ensures compile-time safety.

### 7.2 Error Boundaries
`components/shared/ErrorBoundary.tsx` wraps page-level features to catch render errors and show user-friendly toasts.

---

## 8 . Provider Finder UI Flow (Phase 1 MVP)

1. **SearchPage** (`/providers`)  
   * Sticky search bar (query, specialty, location)  
   * `useProviderSearch` hook calls `GET /providers/search` with SWR  
   * Results grid -> `ProviderCard`  
   * Map toggle shows Leaflet map with markers

2. **ProviderDetailPage** (`/providers/[id]`)  
   * Prefetch via `getServerSideProps` for SEO  
   * Tabs: Info · Availability · Reviews (future)  
   * “Book Now” button (placeholder)

Design emphasises:

* **Progressive Enhancement** – JS-only features degrade gracefully
* **Skeleton Loading** – shimmer while fetch in flight
* **A11y** – headings hierarchy, aria-labels, keyboard navigation

---

## 9 . Feature Flags

```ts
export const features = {
  providerFinder: process.env.NEXT_PUBLIC_ENABLE_PROVIDER_FINDER === 'true',
  biomcp: process.env.NEXT_PUBLIC_ENABLE_BIOMCP === 'true',
  trials: process.env.NEXT_PUBLIC_ENABLE_CLINICAL_TRIALS === 'true',
};
```

Used by `<FeatureGuard>` HOC to tree-shake code on build.

---

## 10 . Testing Strategy

| Layer | Tool | What we test |
|-------|------|--------------|
| Unit | Jest + ts-jest | Pure functions, utils, hooks |
| Component | React Testing Library | Props render, interaction, a11y |
| E2E (opt-in) | Playwright | Critical flows (sign-in, provider search) |

CI runs `npm test --coverage` – gate at ≥ 80 %.

---

## 11 . Performance & Optimisations

* **Turbopack** dev server for fast HMR (opt-in flag)  
* **Dynamic Imports** for heavy components (map, charts)  
* **next/image** for provider photos  
* **React Strict Mode** to surface side-effect issues  
* **Bundle Analyzer** script `npm run analyze` (analyze-client/build)

---

## 12 . Docker Development Container (Brief)

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --frozen-lockfile
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

Spin-up with:

```bash
docker build -t healthfinder-frontend ./frontend
docker run --env-file ./frontend/.env.local -p 3000:3000 healthfinder-frontend
```

`compose.yaml` (root) will later orchestrate both frontend & backend containers.

---

## 13 . Roadmap Post-MVP

1. **BioMCP integration** – toggle via flag, same UI pattern as Provider Finder  
2. **Clinical Trials UI** – patient eligibility wizard  
3. **Offline-first PWA** – caching search results  
4. **I18n** – `next-intl`, incremental translation JSONs  
5. **Design System extraction** – Storybook, tokens

---

## 14 . Contributing Guidelines

* Run `npm run lint && npm run type-check` before PR
* Commit message format: `feat(frontend): add ProviderCard`
* Keep PRs ≤ 400 LOC where possible
* All new components require at least one RTL test

---

### Appendix A – Decision Log (ADR style)

| # | Decision | Date |
|---|----------|------|
| ADR-001 | Use **Next.js** over pure React for routing/SSR & ecosystem | 2025-06-26 |
| ADR-002 | Tailwind + Bootstrap hybrid for rapid delivery, with prefixed Bootstrap classes | 2025-06-26 |
| ADR-003 | SWR over Redux for simple cache layer; revisit when global state grows | 2025-06-27 |

---

**Questions?** Open an issue or ping @engineering in Slack. Happy coding! 🩺
