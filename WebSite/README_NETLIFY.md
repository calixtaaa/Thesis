## Netlify deploy (WebSite)

This Vite + Vue app is configured to deploy from the `WebSite/` subfolder.

### Build settings
- **Base directory**: `WebSite`
- **Build command**: `npm run build`
- **Publish directory**: `WebSite/dist`
- **Node version**: `22` (already set in `netlify.toml`)

### Required environment variables (Netlify → Site settings → Environment variables)
- **`VITE_SUPABASE_URL`**: Your Supabase Project URL (example: `https://xxxx.supabase.co`)
- **`VITE_SUPABASE_PUBLISHABLE_KEY`**: Supabase **anon/public** key (NOT service role)

If these are missing, the app will fail fast with: `Missing VITE_SUPABASE_URL or VITE_SUPABASE_PUBLISHABLE_KEY`.

### SPA routing (important)
SPA refresh / deep links like `/dashboard` are handled by `public/_redirects`:
- `/* /index.html 200`

### Realtime in production
Realtime is handled via Supabase `postgres_changes` subscriptions in `src/composables/useRealtimeMachineData.js`.

If you don’t see realtime updates on Netlify, check:
1. Supabase project is up and reachable from the deployed site.
2. Tables `products`, `transactions`, `live_feed`, `emails` exist in the `public` schema.
3. Row Level Security (RLS) policies allow **select** for anon (or whichever auth you use).
4. In Supabase dashboard: Realtime is enabled for the tables you subscribe to.

