import { ref, computed } from 'vue'
import { supabase } from '../lib/supabaseClient'
import { debounce } from '../utils/timing'

const AUTH_KEY = 'syntax-error-auth'
const LEGACY_USERS_KEY = 'syntax-error-users'
const USERS_KEY = 'syntax-error-user-accounts'
const LOGIN_THROTTLE_KEY = 'syntax-error-login-throttle-v1'
/** Clears old bundled accounts + legacy storage once per browser (see SYNC_KEY). */
const ACCOUNT_SYNC_KEY = 'syntax-error-account-sync-v2'

function syncStoredAccountsOnce() {
  if (typeof window === 'undefined') return
  if (localStorage.getItem(ACCOUNT_SYNC_KEY)) return
  try {
    localStorage.removeItem(LEGACY_USERS_KEY)
    localStorage.removeItem(USERS_KEY)
    localStorage.removeItem(AUTH_KEY)
    localStorage.setItem(ACCOUNT_SYNC_KEY, '1')
  } catch (_) {
    /* ignore quota / private mode */
  }
}

syncStoredAccountsOnce()

function _nowMs() {
  return Date.now()
}

function loadLoginThrottle() {
  if (typeof window === 'undefined') return { fails: 0, lockUntil: 0 }
  try {
    const raw = localStorage.getItem(LOGIN_THROTTLE_KEY)
    if (!raw) return { fails: 0, lockUntil: 0 }
    const parsed = JSON.parse(raw)
    const fails = Number(parsed?.fails ?? 0)
    const lockUntil = Number(parsed?.lockUntil ?? 0)
    return {
      fails: Number.isFinite(fails) && fails > 0 ? fails : 0,
      lockUntil: Number.isFinite(lockUntil) && lockUntil > 0 ? lockUntil : 0,
    }
  } catch {
    return { fails: 0, lockUntil: 0 }
  }
}

function saveLoginThrottle(next) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(LOGIN_THROTTLE_KEY, JSON.stringify(next))
  } catch (_) {
    /* ignore quota / private mode */
  }
}

function resetLoginThrottle() {
  saveLoginThrottle({ fails: 0, lockUntil: 0 })
}

function isLockedOut() {
  const t = loadLoginThrottle()
  const now = _nowMs()
  if (t.lockUntil && now < t.lockUntil) {
    return { locked: true, lockUntil: t.lockUntil, remainingMs: t.lockUntil - now, fails: t.fails }
  }
  if (t.lockUntil && now >= t.lockUntil) {
    // Lock expired; clear it so refreshes don't show stale state.
    resetLoginThrottle()
  }
  return { locked: false, lockUntil: 0, remainingMs: 0, fails: 0 }
}

function registerFailedLogin() {
  const t = loadLoginThrottle()
  const nextFails = (Number(t.fails ?? 0) || 0) + 1
  const maxFails = 5
  const lockMs = 30_000
  if (nextFails >= maxFails) {
    const lockUntil = _nowMs() + lockMs
    saveLoginThrottle({ fails: nextFails, lockUntil })
    return { locked: true, lockUntil, remainingMs: lockMs, fails: nextFails, maxFails }
  }
  saveLoginThrottle({ fails: nextFails, lockUntil: 0 })
  return { locked: false, lockUntil: 0, remainingMs: 0, fails: nextFails, maxFails }
}

function loadUsers() {
  if (typeof window !== 'undefined') {
    try {
      localStorage.removeItem(LEGACY_USERS_KEY)
    } catch (_) {
      /* ignore */
    }
    const saved = localStorage.getItem(USERS_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        return Array.isArray(parsed) ? parsed : []
      } catch {
        return []
      }
    }
  }
  return []
}

function saveUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

function loadAuth() {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(AUTH_KEY)
    if (saved) return JSON.parse(saved)
  }
  return null
}

const currentUser = ref(loadAuth())
const users = ref(loadUsers())

/** TUP Manila school email only (normalized to lowercase for storage and login). */
function isTupSchoolEmail(s) {
  const t = String(s || '').trim().toLowerCase()
  return /^[^\s@]+@tup\.edu\.ph$/.test(t)
}

/**
 * Upsert email + optional password for TUP dashboard accounts (newsletter-only rows stay password null).
 */
const _syncEmailRowToSupabaseDebounced = debounce(async (payload, hasPwd, emailTrim) => {
  const { error } = await supabase.from('emails').insert(payload)
  if (!error) return

  const dup = error.code === '23505' || /duplicate|unique/i.test(error.message || '')
  if (dup && hasPwd) {
    const { data: list, error: selErr } = await supabase.from('emails').select('id, email').limit(500)
    if (selErr) {
      if (import.meta.env.DEV) console.warn('[emails sync]', selErr.message)
      return
    }
    const row = list?.find((r) => String(r.email).trim().toLowerCase() === emailTrim)
    if (row?.id) {
      const { error: uerr } = await supabase.from('emails').update({ password: payload.password }).eq('id', row.id)
      if (uerr && import.meta.env.DEV) console.warn('[emails sync update]', uerr.message)
    }
    return
  }

  if (import.meta.env.DEV) {
    const ignorable = dup || /row-level security|RLS|permission denied|42501/i.test(error.message || '')
    if (!ignorable) console.warn('[emails sync]', error.message)
  }
}, 400)

function syncEmailRowToSupabase(emailRaw, password, role) {
  if (!isTupSchoolEmail(emailRaw)) return
  const emailTrim = emailRaw.trim().toLowerCase()
  const hasPwd = password != null && String(password).length > 0
  const payload = { email: emailTrim }
  if (hasPwd) payload.password = String(password)
  if (role === 'admin' || role === 'staff') payload.role = role

  void _syncEmailRowToSupabaseDebounced(payload, hasPwd, emailTrim)
}

export function useAuth() {
  const isLoggedIn = computed(() => !!currentUser.value)
  const isAdmin = computed(() => currentUser.value?.role === 'admin')

  async function login(username, password) {
    const lock = isLockedOut()
    if (lock.locked) {
      return {
        success: false,
        code: 'LOCKED',
        lockUntil: lock.lockUntil,
        remainingMs: lock.remainingMs,
        message: `Too many incorrect attempts. Please wait ${Math.ceil(lock.remainingMs / 1000)}s and try again.`,
      }
    }

    const key = String(username || '').trim().toLowerCase()
    if (!isTupSchoolEmail(key)) {
      return { success: false, message: 'Use your TUP email (@tup.edu.ph).' }
    }
    const user = users.value.find(
      (u) => u.username.toLowerCase() === key && u.password === password
    )
    if (user) {
      currentUser.value = { username: user.username, role: user.role }
      localStorage.setItem(AUTH_KEY, JSON.stringify(currentUser.value))
      syncEmailRowToSupabase(user.username, password, user.role)
      resetLoginThrottle()
      return { success: true }
    }

    // Incognito / new browser: no localStorage users yet. Fall back to Supabase `emails` table.
    try {
      const { data, error } = await supabase
        .from('emails')
        .select('email, password, role')
        .eq('email', key)
        .limit(1)
      if (error) {
        if (import.meta.env.DEV) console.warn('[auth supabase login]', error.message)
        return { success: false, message: 'Login service unavailable. Try again.' }
      }
      const row = Array.isArray(data) ? data[0] : null
      const storedPwd = row?.password != null ? String(row.password) : ''
      if (!row || !storedPwd || storedPwd !== String(password ?? '')) {
        const t = registerFailedLogin()
        if (t.locked) {
          return {
            success: false,
            code: 'LOCKED',
            lockUntil: t.lockUntil,
            remainingMs: t.remainingMs,
            message: `Too many incorrect attempts. Please wait ${Math.ceil(t.remainingMs / 1000)}s and try again.`,
          }
        }
        return {
          success: false,
          code: 'INVALID',
          fails: t.fails,
          attemptsLeft: Math.max(0, t.maxFails - t.fails),
          message: `Invalid email or password (${Math.max(0, t.maxFails - t.fails)} attempt(s) left)`,
        }
      }

      const role = row.role === 'admin' ? 'admin' : 'staff'
      currentUser.value = { username: key, role }
      localStorage.setItem(AUTH_KEY, JSON.stringify(currentUser.value))
      resetLoginThrottle()

      // Cache into this browser for faster next logins and for Manage Users list.
      if (!users.value.find((u) => u.username.toLowerCase() === key)) {
        users.value.push({ username: key, password: String(password ?? ''), role })
        saveUsers(users.value)
      }
      return { success: true }
    } catch (e) {
      if (import.meta.env.DEV) console.warn('[auth supabase login]', e)
      return { success: false, message: 'Login service unavailable. Try again.' }
    }
  }

  function logout() {
    currentUser.value = null
    localStorage.removeItem(AUTH_KEY)
  }

  function createUser(username, password, role) {
    const normalized = String(username || '').trim().toLowerCase()
    if (!normalized || !password) {
      return { success: false, message: 'Email and password are required' }
    }
    if (!isTupSchoolEmail(normalized)) {
      return { success: false, message: 'School login must be a TUP email ending in @tup.edu.ph' }
    }
    if (users.value.find((u) => u.username.toLowerCase() === normalized)) {
      return { success: false, message: 'An account with this email already exists' }
    }
    if (!['admin', 'staff'].includes(role)) {
      return { success: false, message: 'Role must be admin or staff' }
    }
    users.value.push({ username: normalized, password, role })
    saveUsers(users.value)
    syncEmailRowToSupabase(normalized, password, role)
    return { success: true }
  }

  function getUsers() {
    return users.value.map(u => ({ username: u.username, role: u.role }))
  }

  function deleteUser(username) {
    users.value = users.value.filter((u) => u.username !== username)
    saveUsers(users.value)
    if (currentUser.value?.username === username) logout()
    const key = String(username || '').trim().toLowerCase()
    if (isTupSchoolEmail(key)) {
      void supabase.from('emails').delete().eq('email', key).then(({ error }) => {
        if (error && import.meta.env.DEV) console.warn('[emails delete]', error.message)
      })
    }
    return { success: true }
  }

  return {
    currentUser,
    isLoggedIn,
    isAdmin,
    login,
    logout,
    createUser,
    getUsers,
    deleteUser,
  }
}
