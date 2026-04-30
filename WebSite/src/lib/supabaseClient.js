import { createClient } from '@supabase/supabase-js'

/**
 * Project URL from Supabase → Settings → API → "Project URL".
 * Use only the root, e.g. https://xxxx.supabase.co — not .../emails (that is a table name in code, not part of the URL).
 * The real "API key" is the anon public key in the same screen (VITE_SUPABASE_PUBLISHABLE_KEY).
 */
function normalizeProjectUrl(raw) {
  if (!raw || typeof raw !== 'string') return raw
  let u = raw.trim().replace(/\/+$/, '')
  if (/\/emails$/i.test(u)) u = u.replace(/\/emails$/i, '')
  return u
}

const url = normalizeProjectUrl(import.meta.env.VITE_SUPABASE_URL)
// Allow common env var aliases so deploys don't silently break.
// Preferred: VITE_SUPABASE_PUBLISHABLE_KEY (Supabase "anon/public" key).
const key =
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ||
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  import.meta.env.VITE_SUPABASE_ANON_PUBLIC_KEY

if (!url || !key) {
  throw new Error(
    'Missing VITE_SUPABASE_URL or Supabase anon key (VITE_SUPABASE_PUBLISHABLE_KEY / VITE_SUPABASE_ANON_KEY)'
  )
}

export const supabase = createClient(url, key)

