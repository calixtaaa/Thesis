import { ref, computed } from 'vue'

const AUTH_KEY = 'syntax-error-auth'
const USERS_KEY = 'syntax-error-users'

// Default admin account
const DEFAULT_USERS = [
  { username: 'admin', password: 'admin', role: 'admin' }
]

function loadUsers() {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(USERS_KEY)
    if (saved) return JSON.parse(saved)
  }
  return [...DEFAULT_USERS]
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

export function useAuth() {
  const isLoggedIn = computed(() => !!currentUser.value)
  const isAdmin = computed(() => currentUser.value?.role === 'admin')

  function login(username, password) {
    const user = users.value.find(
      u => u.username === username && u.password === password
    )
    if (user) {
      currentUser.value = { username: user.username, role: user.role }
      localStorage.setItem(AUTH_KEY, JSON.stringify(currentUser.value))
      return { success: true }
    }
    return { success: false, message: 'Invalid username or password' }
  }

  function logout() {
    currentUser.value = null
    localStorage.removeItem(AUTH_KEY)
  }

  function createUser(username, password, role) {
    if (users.value.find(u => u.username === username)) {
      return { success: false, message: 'Username already exists' }
    }
    if (!username || !password) {
      return { success: false, message: 'Username and password are required' }
    }
    if (!['admin', 'staff'].includes(role)) {
      return { success: false, message: 'Role must be admin or staff' }
    }
    users.value.push({ username, password, role })
    saveUsers(users.value)
    return { success: true }
  }

  function getUsers() {
    return users.value.map(u => ({ username: u.username, role: u.role }))
  }

  function deleteUser(username) {
    if (username === 'admin') {
      return { success: false, message: 'Cannot delete the default admin account' }
    }
    users.value = users.value.filter(u => u.username !== username)
    saveUsers(users.value)
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
