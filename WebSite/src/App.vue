<template>
  <div class="min-h-screen flex flex-col bg-surface-950">
    <LoadingScreen />
    <NavBar />
    <main class="flex-1 pt-16 lg:pt-18">
      <router-view v-slot="{ Component }">
        <transition
          enter-active-class="transition-opacity duration-300 ease-out"
          enter-from-class="opacity-0"
          enter-to-class="opacity-100"
          leave-active-class="transition-opacity duration-200 ease-in"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
          mode="out-in"
        >
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <FooterBar />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import NavBar from './components/NavBar.vue'
import FooterBar from './components/FooterBar.vue'
import LoadingScreen from './components/LoadingScreen.vue'

let tuqlasEl
onMounted(() => {
  // Load Tuqlas chatbot once (avoid duplicates on hot reload / remount).
  const existing = document.querySelector('script[data-tuqlas="1"]')
  if (existing) {
    tuqlasEl = existing
    return
  }
  tuqlasEl = document.createElement('script')
  tuqlasEl.src = 'https://www.tuqlas.com/chatbot.js'
  tuqlasEl.setAttribute('data-tuqlas', '1')
  tuqlasEl.setAttribute('data-key', 'tq_live_29a16781b90f0349dde1556b59c1dc8ea40750ae')
  tuqlasEl.setAttribute('data-api', 'https://www.tuqlas.com')
  tuqlasEl.defer = true
  document.body.appendChild(tuqlasEl)
})
onUnmounted(() => tuqlasEl?.remove())
</script>
