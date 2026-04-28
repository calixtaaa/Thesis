import { ref, computed } from 'vue'
import { supabase } from '../lib/supabaseClient'
import { debounce } from '../utils/timing'

const AUTH_KEY = 'syntax-error-auth'
const LEGACY_USERS_KEY = 'syntax-error-users'
const USERS_KEY = 'syntax-error-user-accounts'
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

function syncEmailRowToSupabase(emailRaw, password) {
  if (!isTupSchoolEmail(emailRaw)) return
  const emailTrim = emailRaw.trim().toLowerCase()
  const hasPwd = password != null && String(password).length > 0
  const payload = { email: emailTrim }
  if (hasPwd) payload.password = String(password)

  void _syncEmailRowToSupabaseDebounced(payload, hasPwd, emailTrim)
}

export function useAuth() {
  const isLoggedIn = computed(() => !!currentUser.value)
  const isAdmin = computed(() => currentUser.value?.role === 'admin')

  function login(username, password) {
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
      syncEmailRowToSupabase(user.username, password)
      return { success: true }
    }
    return { success: false, message: 'Invalid email or password' }
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
    syncEmailRowToSupabase(normalized, password)
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
