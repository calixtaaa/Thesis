<template>
  <div class="relative overflow-hidden min-h-[calc(100vh-4rem)] flex items-center justify-center px-4">
    <!-- Background Effects -->
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute top-1/4 left-1/4 w-80 h-80 bg-brand-800/10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 right-1/4 w-72 h-72 bg-gold-400/5 rounded-full blur-3xl"></div>
    </div>

    <div class="relative w-full max-w-md">
      <!-- Login Card -->
      <div class="glass rounded-3xl p-8 sm:p-10 animate-slide-up">
        <!-- Header -->
        <div class="text-center mb-8">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl overflow-hidden shadow-lg shadow-brand-800/30">
            <img :src="logoImg" alt="Syntax Error" class="w-full h-full object-cover" />
          </div>
          <h1 class="text-2xl sm:text-3xl font-bold font-display text-surface-100 dark:text-surface-100">
            Welcome Back
          </h1>
          <p class="text-sm text-surface-400 mt-2">Sign in to access the dashboard</p>
          <p class="text-xs text-surface-500 mt-3 max-w-xs mx-auto leading-relaxed">
            Use your <span class="text-surface-400">@tup.edu.ph</span> email only. No default login — use <span class="text-surface-400">Create a new account</span> first on this device if needed.
          </p>
        </div>

        <!-- Login Form -->
        <form v-if="!showCreateUser" @submit.prevent="handleLogin" class="space-y-5">
          <div>
            <label for="login-email" class="block text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">
              Email
            </label>
            <input
              id="login-email"
              v-model="username"
              type="email"
              inputmode="email"
              required
              autocomplete="email"
              class="w-full px-4 py-3 rounded-xl bg-surface-800/50 border border-surface-700/50 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600 transition-all duration-300 text-sm"
              placeholder="name@tup.edu.ph"
            />
          </div>
          <div>
            <label for="login-password" class="block text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">
              Password
            </label>
            <div class="relative">
              <input
                id="login-password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                class="w-full px-4 py-3 rounded-xl bg-surface-800/50 border border-surface-700/50 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600 transition-all duration-300 text-sm pr-12"
                placeholder="Enter password"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-surface-300 transition-colors"
              >
                <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Error Message -->
          <transition name="text-fade">
            <div v-if="error" class="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
              {{ error }}
            </div>
          </transition>

          <button
            type="submit"
            class="w-full btn-primary text-center justify-center"
          >
            Sign In
          </button>

          <button
            type="button"
            @click="showCreateUser = true"
            class="w-full text-center text-xs text-surface-500 hover:text-surface-300 transition-colors duration-300 mt-2"
          >
            Create a new account →
          </button>
        </form>

        <!-- Create User Form -->
        <form v-else @submit.prevent="handleCreateUser" class="space-y-5">
          <div class="flex items-center gap-2 mb-4">
            <button type="button" @click="showCreateUser = false" class="text-surface-400 hover:text-surface-200 transition-colors">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h2 class="text-lg font-bold font-display text-surface-100">Create Account</h2>
          </div>

          <div>
            <label for="new-email" class="block text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">
              Email
            </label>
            <input
              id="new-email"
              v-model="newUsername"
              type="email"
              inputmode="email"
              required
              autocomplete="email"
              class="w-full px-4 py-3 rounded-xl bg-surface-800/50 border border-surface-700/50 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600 transition-all duration-300 text-sm"
              placeholder="name@tup.edu.ph"
            />
          </div>
          <div>
            <label for="new-password" class="block text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">
              Password
            </label>
            <input
              id="new-password"
              v-model="newPassword"
              type="password"
              required
              class="w-full px-4 py-3 rounded-xl bg-surface-800/50 border border-surface-700/50 text-surface-100 placeholder-surface-500 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600 transition-all duration-300 text-sm"
              placeholder="Choose password"
            />
          </div>
          <div>
            <label for="new-role" class="block text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">
              Role
            </label>
            <select
              id="new-role"
              v-model="newRole"
              class="w-full px-4 py-3 rounded-xl bg-surface-800/50 border border-surface-700/50 text-surface-100 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600 transition-all duration-300 text-sm"
            >
              <option value="admin">Admin</option>
              <option value="staff">Staff</option>
            </select>
          </div>

          <!-- Messages -->
          <transition name="text-fade">
            <div v-if="createError" class="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
              {{ createError }}
            </div>
          </transition>
          <transition name="text-fade">
            <div v-if="createSuccess" class="px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm text-center">
              {{ createSuccess }}
            </div>
          </transition>

          <button
            type="submit"
            class="w-full btn-primary text-center justify-center"
          >
            Create Account
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import logoImg from '../assets/LogoThesis.png'

const router = useRouter()
const { login, createUser } = useAuth()

// Login
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref('')

function handleLogin() {
  error.value = ''
  const result = login(username.value, password.value)
  if (result.success) {
    router.push('/dashboard')
  } else {
    error.value = result.message
  }
}

// Create User
const showCreateUser = ref(false)
const newUsername = ref('')
const newPassword = ref('')
const newRole = ref('staff')
const createError = ref('')
const createSuccess = ref('')

function handleCreateUser() {
  createError.value = ''
  createSuccess.value = ''
  const result = createUser(newUsername.value, newPassword.value, newRole.value)
  if (result.success) {
    createSuccess.value = `Account ${newUsername.value.trim()} created! You can now sign in.`
    newUsername.value = ''
    newPassword.value = ''
    newRole.value = 'staff'
    setTimeout(() => {
      showCreateUser.value = false
      createSuccess.value = ''
    }, 2000)
  } else {
    createError.value =
      result.message === 'An account with this email already exists'
        ? `${result.message} — sign in with that email, or use a different @tup.edu.ph address.`
        : result.message
  }
}
</script>

<style scoped>
.text-fade-enter-active { transition: all 0.3s ease-out; }
.text-fade-leave-active { transition: all 0.2s ease-in; }
.text-fade-enter-from { opacity: 0; transform: translateY(5px); }
.text-fade-leave-to { opacity: 0; transform: translateY(-5px); }
</style>
