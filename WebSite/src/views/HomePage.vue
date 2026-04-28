<template>
  <div class="relative overflow-hidden">
    <!-- Background Effects -->
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute top-0 left-1/4 w-96 h-96 bg-brand-800/10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gold-400/5 rounded-full blur-3xl"></div>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-800/5 rounded-full blur-3xl"></div>
    </div>

    <!-- Hero Section -->
    <section class="relative min-h-[90vh] flex items-center justify-center px-4">
      <div class="max-w-5xl mx-auto text-center">
        <!-- Badge -->
        <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-light mb-8 animate-fade-in">
          <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
          <span class="text-xs font-medium text-surface-300 tracking-wide uppercase">
            Syntax Error — TUP-Manila Capstone 2026
          </span>
        </div>

        <!-- Main Heading -->
        <h1 class="text-4xl sm:text-5xl lg:text-7xl font-bold font-display leading-tight mb-6 animate-slide-up">
          <span class="text-surface-100">Smart Hygiene</span><br>
          <span class="gradient-text">Vending Machine</span>
        </h1>

        <!-- Description -->
        <p class="text-lg sm:text-xl text-surface-400 max-w-2xl mx-auto mb-10 animate-slide-up leading-relaxed" style="animation-delay: 0.1s">
          An innovative IoT-based vending solution developed by Computer Engineering Technology students at the Technological University of the Philippines — Manila.
        </p>

        <!-- CTA Buttons -->
        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up" style="animation-delay: 0.2s">
          <router-link to="/team" class="btn-primary flex items-center gap-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Meet the Team
          </router-link>
          <router-link to="/dashboard" class="btn-secondary flex items-center gap-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            View Dashboard
          </router-link>
        </div>
      </div>

      <!-- Scroll indicator -->
      <div class="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <svg class="w-6 h-6 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>

    <!-- Quick Links Section -->
    <section class="relative py-20 lg:py-28 px-4">
      <div class="max-w-6xl mx-auto">
        <!-- Section Header -->
        <div class="text-center mb-16">
          <h2 class="text-3xl sm:text-4xl font-bold font-display mb-4">
            <span class="text-surface-100">Explore</span>
            <span class="gradient-text ml-2">Our Project</span>
          </h2>
          <p class="text-surface-400 max-w-lg mx-auto">
            Navigate through the different sections of our capstone project website.
          </p>
        </div>

        <!-- Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
          <router-link
            v-for="(card, index) in cards"
            :key="card.path"
            :to="card.path"
            class="group glass rounded-2xl p-8 card-hover"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <!-- Icon -->
            <div class="w-14 h-14 rounded-xl mb-6 flex items-center justify-center transition-all duration-300 group-hover:scale-110"
              :class="card.iconBg"
            >
              <span v-html="card.icon" class="w-7 h-7"></span>
            </div>

            <!-- Content -->
            <h3 class="text-xl font-bold font-display text-surface-100 mb-3 group-hover:text-white transition-colors">
              {{ card.title }}
            </h3>
            <p class="text-sm text-surface-400 leading-relaxed mb-6">
              {{ card.description }}
            </p>

            <!-- Arrow -->
            <div class="flex items-center gap-2 text-sm font-medium transition-all duration-300"
              :class="card.arrowColor"
            >
              <span>Explore</span>
              <svg class="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </div>
          </router-link>
        </div>
      </div>
    </section>

    <!-- About Section -->
    <section class="relative py-20 lg:py-28 px-4">
      <div class="max-w-4xl mx-auto">
        <div class="glass rounded-3xl p-8 sm:p-12 lg:p-16 relative overflow-hidden">
          <!-- Decorative accent -->
          <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-brand-800/10 to-transparent rounded-bl-full"></div>
          <div class="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-gold-400/5 to-transparent rounded-tr-full"></div>

          <div class="relative">
            <h2 class="text-3xl sm:text-4xl font-bold font-display mb-6">
              <span class="text-surface-100">About the</span>
              <span class="gradient-text ml-2">Project</span>
            </h2>
            <p class="text-surface-300 leading-relaxed mb-6 text-lg">
              This capstone project is developed by students of the <strong class="text-surface-100">Bachelor of Engineering Technology</strong> major in <strong class="text-surface-100">Computer Engineering Technology</strong> at the Technological University of the Philippines — Manila.
            </p>
            <p class="text-surface-400 leading-relaxed">
              Our Smart Hygiene Vending Machine integrates IoT technology, real-time monitoring, and intelligent inventory management to provide a modern, efficient solution for dispensing hygiene products in public spaces.
            </p>

            <!-- Email signup (stored in Supabase `emails`; shown on admin dashboard) -->
            <div class="mt-10 pt-8 border-t border-surface-800/50">
              <h3 class="text-lg font-bold font-display text-surface-100 mb-2">Project updates</h3>
              <p class="text-sm text-surface-500 mb-4">Leave your email — it appears in the admin dashboard for your team.</p>
              <form class="flex flex-col sm:flex-row gap-3 max-w-lg" @submit.prevent="submitSignup">
                <input
                  v-model="signupEmail"
                  type="email"
                  required
                  autocomplete="email"
                  placeholder="you@school.edu.ph"
                  class="flex-1 px-4 py-3 rounded-xl bg-surface-900/40 border border-surface-700/50 text-surface-100 text-sm placeholder:text-surface-600 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500/30"
                />
                <button
                  type="submit"
                  :disabled="signupLoading"
                  class="px-6 py-3 rounded-xl text-sm font-bold bg-brand-600 text-white hover:bg-brand-500 disabled:opacity-50 disabled:pointer-events-none transition-colors shrink-0"
                >
                  {{ signupLoading ? 'Sending…' : 'Notify me' }}
                </button>
              </form>
              <p v-if="signupMsg" class="text-xs mt-3" :class="signupOk ? 'text-emerald-400' : 'text-amber-400'">{{ signupMsg }}</p>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-3 gap-6 mt-10 pt-8 border-t border-surface-800/50">
              <div v-for="stat in stats" :key="stat.label" class="text-center">
                <div class="text-2xl sm:text-3xl font-bold font-display gradient-text">{{ stat.value }}</div>
                <div class="text-xs text-surface-500 mt-1 uppercase tracking-wider">{{ stat.label }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { supabase } from '../lib/supabaseClient'

const signupEmail = ref('')
const signupMsg = ref('')
const signupOk = ref(false)
const signupLoading = ref(false)

async function submitSignup() {
  signupMsg.value = ''
  signupOk.value = false
  const email = signupEmail.value.trim()
  if (!email) return
  signupLoading.value = true
  const { error } = await supabase.from('emails').insert({ email })
  signupLoading.value = false
  if (error) {
    signupOk.value = false
    if (/relation|does not exist|not find/i.test(error.message)) {
      signupMsg.value = 'Database is not ready: create the emails table in Supabase (see WebSite/supabase/emails_table.sql).'
    } else if (error.code === '23505' || /duplicate key|unique constraint/i.test(error.message || '')) {
      signupMsg.value = 'That email is already on the list.'
    } else {
      signupMsg.value = error.message
    }
    return
  }
  signupOk.value = true
  signupMsg.value = 'Saved. Your admin dashboard will list this address.'
  signupEmail.value = ''
}

const cards = [
  {
    title: 'Our Team',
    description: 'Meet the talented engineers and developers behind this capstone project.',
    path: '/team',
    iconBg: 'bg-brand-800/20',
    arrowColor: 'text-brand-400 group-hover:text-brand-300',
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>',
  },
  {
    title: 'Adviser',
    description: 'Learn about our project adviser who guided us throughout this capstone journey.',
    path: '/adviser',
    iconBg: 'bg-gold-400/20',
    arrowColor: 'text-gold-400 group-hover:text-gold-300',
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>',
  },
  {
    title: 'Dashboard',
    description: 'View real-time data and analytics from the Smart Hygiene Vending Machine.',
    path: '/dashboard',
    iconBg: 'bg-emerald-400/20',
    arrowColor: 'text-emerald-400 group-hover:text-emerald-300',
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" /></svg>',
  },
]

const stats = [
  { value: '6', label: 'Team Members' },
  { value: 'IoT', label: 'Technology' },
  { value: '2026', label: 'Batch Year' },
]
</script>
