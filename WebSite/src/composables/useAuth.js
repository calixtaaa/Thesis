import { ref, computed } from 'vue'
import { supabase, isSupabaseConfigured } from '../utils/supabase'

const session = ref(null)
const authReady = ref(false)

supabase.auth.onAuthStateChange((_event, s) => {
  session.value = s
  authReady.value = true
})

const currentUser = computed(() => {
  const u = session.value?.user
  if (!u) return null
  const email = u.email || ''
  return {
    uid: u.id,
    email,
    username: email.includes('@') ? email.split('@')[0] : email || 'user',
  }
})

const role = computed(() => {
  const r = session.value?.user?.user_metadata?.role
  return typeof r === 'string' ? r : 'staff'
})

export function useAuth() {
  const isLoggedIn = computed(() => !!session.value?.user)
  const isAdmin = computed(() => role.value === 'admin')
  const isMaintenance = computed(() => role.value === 'maintenance')

  async function login(email, password) {
    if (!isSupabaseConfigured()) {
      return { success: false, message: 'Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY to .env.local and restart Vite.' }
    }
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) {
      const msg = error.message || ''
      if (/invalid login credentials/i.test(msg)) {
        return { success: false, message: 'Incorrect email or password' }
      }
      return { success: false, message: msg || 'Login failed.' }
    }
    return { success: true }
  }

  async function logout() {
    if (!isSupabaseConfigured()) return
    await supabase.auth.signOut()
  }

  async function createUser(email, password, roleName) {
    if (!isSupabaseConfigured()) {
      return { success: false, message: 'Supabase is not configured. Add .env.local and restart Vite.' }
    }
    if (!['admin', 'staff', 'maintenance'].includes(roleName)) {
      return { success: false, message: 'Role must be admin, staff, or maintenance' }
    }
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { role: roleName } },
    })
    if (error) {
      const msg = error.message || ''
      if (/already registered/i.test(msg)) return { success: false, message: 'Email is already in use' }
      if (/password/i.test(msg) && /6/i.test(msg)) return { success: false, message: 'Password should be at least 6 characters' }
      return { success: false, message: msg || 'Account creation failed.' }
    }
    if (data?.user && !session.value) {
      return {
        success: true,
        message: 'Check your email to confirm the account if confirmation is enabled in Supabase.',
      }
    }
    return { success: true }
  }

  function getUsers() {
    return []
  }

  function deleteUser() {
    return { success: false, message: 'Not supported on client' }
  }

  return {
    currentUser,
    role,
    authReady,
    isLoggedIn,
    isAdmin,
    isMaintenance,
    login,
    logout,
    createUser,
    getUsers,
    deleteUser,
  }
}
