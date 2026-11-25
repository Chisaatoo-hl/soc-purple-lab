# Analyst Console — Web (React + TypeScript)

Vite + React + TypeScript, Tailwind v4, React Router, TanStack Query.
Talks to the FastAPI backend; API types are generated from its OpenAPI spec.

## Run
```bash
npm install
cp .env.example .env            # VITE_API_URL=http://localhost:8000

# optional: generate TS types from the running API (backend up on :8000)
npm run gen:api                 # -> src/types/api.ts

npm run dev                     # http://localhost:5173
```

The Alerts page fetches `/alerts` through TanStack Query — if the backend is up
and seeded, it shows the alert count. Full table (Step 3) and detail/decision
view (Step 4) build on this foundation.

## Scripts
| Script | Purpose |
|---|---|
| `npm run dev` | dev server on :5173 |
| `npm run build` | typecheck + production build |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run gen:api` | regenerate `src/types/api.ts` from `/openapi.json` |

## Layout
```
src/
  main.tsx            router + providers
  index.css           @import "tailwindcss";
  lib/api.ts          typed fetch wrapper (VITE_API_URL)
  lib/queryClient.ts  TanStack Query client
  routes/
    Layout.tsx        sidebar shell (Alerts / Stats)
    AlertsPage.tsx    Step 3 lands here
    StatsPage.tsx     Step 5 lands here
  types/api.ts        generated (npm run gen:api)
```
