<template>
  <nav class="fixed top-0 left-0 right-0 z-50 glass border-b border-surface-800/50 light:bg-white/80 light:border-surface-200/50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16 lg:h-18">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-3 group">
          <div class="w-9 h-9 rounded-lg overflow-hidden shadow-lg shadow-brand-800/30 group-hover:shadow-brand-800/50 transition-shadow duration-300">
            <img :src="logoImg" alt="Syntax Error" class="w-full h-full object-cover" />
          </div>
          <span class="text-lg font-bold font-display tracking-tight">
            <span class="text-surface-100 light:text-surface-900">Syntax</span>
            <span class="gradient-text ml-1">Error</span>
          </span>
        </router-link>

        <!-- Desktop Navigation + Controls -->
        <div class="hidden md:flex items-center gap-1">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            class="relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300"
            :class="isActive(link.path)
              ? 'text-gold-300 bg-gold-400/10'
              : 'text-surface-400 hover:text-surface-100 hover:bg-surface-800/50 light:text-surface-500 light:hover:text-surface-800 light:hover:bg-surface-100'"
          >
            <span class="flex items-center gap-2">
              <component :is="link.icon" class="w-4 h-4" />
              {{ link.name }}
            </span>
            <span
              v-if="isActive(link.path)"
              class="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5 bg-gradient-to-r from-gold-400 to-gold-300 rounded-full"
            ></span>
          </router-link>

          <!-- Divider -->
          <div class="w-px h-6 bg-surface-700/50 mx-2 light:bg-surface-200"></div>

          <!-- Theme Toggle -->
          <button
            @click="toggleTheme"
            class="p-2 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-800/50 light:hover:bg-surface-100 light:hover:text-surface-800 transition-all duration-300"
            :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
          >
            <!-- Sun icon (show in dark mode) -->
            <svg v-if="theme === 'dark'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <!-- Moon icon (show in light mode) -->
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>

          <!-- Logout (if logged in) -->
          <button
            v-if="isLoggedIn"
            @click="handleLogout"
            class="p-2 rounded-lg text-surface-400 hover:text-red-400 hover:bg-red-400/10 transition-all duration-300"
            aria-label="Logout"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>

        <!-- Mobile: Theme Toggle + Menu Toggle -->
        <div class="md:hidden flex items-center gap-2">
          <button
            @click="toggleTheme"
            class="p-2 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-800/50 transition-all duration-300"
          >
            <svg v-if="theme === 'dark'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>
          <button
            @click="mobileOpen = !mobileOpen"
            class="p-2 rounded-lg text-surface-400 hover:text-surface-100 hover:bg-surface-800/50 transition-all duration-300"
            :aria-label="mobileOpen ? 'Close menu' : 'Open menu'"
          >
            <svg v-if="!mobileOpen" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Menu -->
    <transition
      enter-active-class="transition ease-out duration-300"
      enter-from-class="opacity-0 -translate-y-4"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-4"
    >
      <div v-if="mobileOpen" class="md:hidden glass border-t border-surface-800/30 light:bg-white/90 light:border-surface-200/30">
        <div class="px-4 py-3 space-y-1">
          <router-link
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            @click="mobileOpen = false"
            class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300"
            :class="isActive(link.path)
              ? 'text-gold-300 bg-gold-400/10'
              : 'text-surface-400 hover:text-surface-100 hover:bg-surface-800/50 light:text-surface-500 light:hover:text-surface-800 light:hover:bg-surface-100'"
          >
            <component :is="link.icon" class="w-5 h-5" />
            {{ link.name }}
          </router-link>

          <!-- Mobile Logout -->
          <button
            v-if="isLoggedIn"
            @click="handleLogout(); mobileOpen = false"
            class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-red-400 hover:bg-red-400/10 transition-all duration-300 w-full"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Logout
          </button>
        </div>
      </div>
    </transition>
  </nav>
</template>

<script setup>
import { ref, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { useAuth } from '../composables/useAuth'
import logoImg from '../assets/LogoThesis.png'

const route = useRoute()
const router = useRouter()
const mobileOpen = ref(false)
const { theme, toggle: toggleTheme } = useTheme()
const { isLoggedIn, logout } = useAuth()

const isActive = (path) => route.path === path

function handleLogout() {
  logout()
  router.push('/')
}

// Simple inline SVG icon components
const HomeIcon = { render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', class: 'w-4 h-4' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' })]) }
const TeamIcon = { render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', class: 'w-4 h-4' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' })]) }
const AdviserIcon = { render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', class: 'w-4 h-4' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' })]) }
const DashIcon = { render: () => h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', class: 'w-4 h-4' }, [h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z' })]) }

const navLinks = [
  { name: 'Home', path: '/', icon: HomeIcon },
  { name: 'Team', path: '/team', icon: TeamIcon },
  { name: 'Adviser', path: '/adviser', icon: AdviserIcon },
  { name: 'Dashboard', path: '/dashboard', icon: DashIcon },
]
</script>
