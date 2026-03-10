# frontend-solid

Kahvesiz Calisma icin SolidJS tabanli yeni frontend katmani (Faz 1 iskeleti).

## Scripts

```bash
npm install
npm run dev
npm run build
npm run preview
npm run size:check
```

## Development Topology

- Flask API: `http://localhost:5040`
- Solid dev server: `http://localhost:5173`
- Vite proxy routes: `/api`, `/login`, `/signup`, `/logout`, `/confirm`

## Architecture Notes

- Router: `@solidjs/router`
- Layout shell: `Navbar + Footer + route container`
- API client: `src/lib/api.ts`
- Fetch default: `credentials: "include"`
- Timeout strategy: default `10s` via `AbortController`
- CSRF strategy: meta token, fallback backend login/signup HTML parse
- Auth skeleton: `src/auth/AuthContext.tsx`
- Global error boundary: `src/components/GlobalErrorFallback.tsx`

## Performance Budget

Ayrintili hedefler: `docs/performance-budget.md`
