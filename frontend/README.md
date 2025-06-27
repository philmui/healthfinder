# HealthFinder Frontend

Next.js + React **UI** for the HealthFinder healthcare-information search platform.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Available Scripts](#available-scripts)
4. [Environment Variables](#environment-variables)
5. [Project Structure](#project-structure)
6. [Styling & UI Toolkit](#styling--ui-toolkit)
7. [Authentication](#authentication)
8. [Docker (Dev Container)](#docker-dev-container)
9. [Linting / Formatting](#linting--formatting)
10. [References](#references)

---

## Prerequisites
| Tool | Version | Notes |
|------|---------|-------|
| Node.js | ≥ 18.x (LTS) | [Download](https://nodejs.org/) |
| npm | comes with Node | Yarn / pnpm also work |
| *Optional* Docker | ≥ 24.x | For containerised dev |

---

## Quick Start

```bash
# 1. Install dependencies
npm install      # or: pnpm install

# 2. Copy & edit environment variables
cp .env.local.example .env.local
# ↳ Fill in NEXT_PUBLIC_API_URL & Google OAuth keys

# 3. Start the dev server
npm run dev
# open http://localhost:3000
```

Production build:

```bash
npm run build     # generates .next/
npm start         # runs on PORT (defaults 3000)
```

---

## Available Scripts
| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server with Hot Reload |
| `npm run build` | Create production build |
| `npm start` | Start built app (uses `.next/`) |
| `npm run lint` | ESLint check |
| `npm run format` | Prettier write |
| `npm run type-check` | Run TypeScript compiler in type-check only mode |

---

## Environment Variables

Create **`frontend/.env.local`** (ignored by git) – required keys:

| Key | Example | Purpose |
|-----|---------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of FastAPI backend |
| `GOOGLE_CLIENT_ID` | _xxx.apps.googleusercontent.com_ | Google OAuth |
| `GOOGLE_CLIENT_SECRET` | _supersecret_ | Google OAuth |
| `NEXTAUTH_URL` | `http://localhost:3000` | Site URL for NextAuth callbacks |
| `NEXTAUTH_SECRET` | long-random-string | Used to sign cookies/JWT |
| *(Optional)* `NEXT_PUBLIC_RELEASE` | `dev` or commit SHA | Shown in footer |

See **`.env.local.example`** for the full list.

---

## Project Structure

```
frontend/
├─ pages/              # Route-based pages  (/search, /providers/[id])
│   └─ api/auth/[…].ts # NextAuth config
├─ components/         # Reusable UI pieces (Navbar, ProviderCard…)
├─ hooks/              # Custom React hooks (useAuth, useDebounce…)
├─ styles/             # globals.css + Tailwind config
├─ utils/              # API helpers (axios), constants, types
└─ docs/
   └─ DESIGN.md        # In-depth architecture notes
```

> Tip: We keep business logic out of `pages/` and colocate stateful hooks with UI components when feasible.

---

## Styling & UI Toolkit
- **Tailwind CSS** – utility-first styling. Configured via `tailwind.config.ts`.
- **Bootstrap 5** (via npm) – for a few ready-made components; class names are namespaced to avoid conflicts.
- **Heroicons** – SVG icons (already installed).

To add new colours or themes, edit `tailwind.config.ts` and refer to `styles/theme.css`.

---

## Authentication
Implemented with **NextAuth.js**.

1. Google OAuth provider enabled (`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`).
2. Apple provider file scaffolded; enable once Apple credentials are added.
3. Tokens are stored in secure, HTTP-only cookies.  
4. Protect SSR pages via `getServerSideProps` and `getSession()`. Static routes can use the `withAuth` middleware (see `middleware.ts`).

---

## Docker (Dev Container)

A lightweight Dockerfile is provided for running the frontend in isolation:

```bash
# build image
docker build -t healthfinder-frontend ./frontend

# run container (binds to port 3000)
docker run --env-file ./frontend/.env.local \
           -p 3000:3000 \
           healthfinder-frontend
```

> For a full-stack dev environment with both frontend & backend, see `compose.yaml` in the repository root (generated in a later step).

---

## Linting / Formatting
| Tool | Config |
|------|--------|
| **ESLint** | `.eslintrc.json` – extends `next/core-web-vitals` |
| **Prettier** | `.prettierrc` – opinionated formatting |
| **TypeScript** | `tsconfig.json` – strict settings |

CI will fail if linting or type-checks do not pass.

---

## References
- [Next.js Docs](https://nextjs.org/docs)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [NextAuth.js (Google provider)](https://next-auth.js.org/providers/google)
- [HealthFinder Backend README](../server/README.md) – API endpoints
- [Frontend DESIGN.md](docs/DESIGN.md) – component architecture, state management

---

Happy hacking 🩺
