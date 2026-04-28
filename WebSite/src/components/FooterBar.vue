<template>
  <footer class="relative border-t border-surface-800/50 mt-auto">
    <!-- Glow accent -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-px bg-gradient-to-r from-transparent via-brand-800/50 to-transparent"></div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12">
      <div class="flex flex-col md:flex-row items-center justify-between gap-6">
        <!-- Brand -->
        <div class="flex flex-col items-center md:items-start gap-2">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg overflow-hidden">
              <img :src="logoImg" alt="Syntax Error" class="w-full h-full object-cover" />
            </div>
            <span class="text-sm font-bold font-display tracking-tight text-surface-300 light:text-surface-700">
              Syntax <span class="gradient-text">Error</span>
            </span>
          </div>
          <p class="text-xs text-surface-500 text-center md:text-left max-w-xs">
            Technological University of the Philippines — Manila<br>
            Bachelor of Engineering Technology — CpET
          </p>
        </div>

        <!-- Quick Links -->
        <div class="flex items-center gap-6 flex-wrap justify-center">
          <router-link
            v-for="link in links"
            :key="link.path"
            :to="link.path"
            class="text-xs text-surface-500 hover:text-surface-200 transition-colors duration-300"
          >
            {{ link.name }}
          </router-link>
        </div>

        <!-- Copyright -->
        <p class="text-xs text-surface-600">
          &copy; {{ currentYear }} All rights reserved.
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import logoImg from '../assets/LogoThesis.png'

const currentYear = new Date().getFullYear()
const links = [
  { name: 'Home', path: '/' },
  { name: 'Team', path: '/team' },
  { name: 'Adviser', path: '/adviser' },
  { name: 'Dashboard', path: '/dashboard' },
]
</script>
