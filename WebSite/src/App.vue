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
import NavBar from './components/NavBar.vue'
import FooterBar from './components/FooterBar.vue'
import LoadingScreen from './components/LoadingScreen.vue'
</script>
