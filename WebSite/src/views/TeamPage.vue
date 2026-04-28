<template>
  <div class="relative min-h-[calc(100vh-4rem)] overflow-hidden">
    <!-- Background -->
    <div class="absolute inset-0 bg-gradient-to-br from-surface-950 via-surface-900 to-surface-950 pointer-events-none" :class="{ 'light-bg-gradient': theme === 'light' }"></div>

    <!-- Page Header -->
    <div class="relative text-center pt-10 pb-4 px-4 z-10">
      <h1 class="text-3xl sm:text-4xl lg:text-5xl font-bold font-display mb-2 animate-fade-in">
        <span class="text-surface-100">Meet Our</span>
        <span class="gradient-text ml-2">Team</span>
      </h1>
      <p class="text-surface-400 max-w-lg mx-auto text-sm sm:text-base animate-fade-in" style="animation-delay: 0.1s">
        The talented engineers behind the Smart Hygiene Vending Machine project.
      </p>
    </div>

    <!-- Main Carousel Layout -->
    <div class="relative max-w-7xl mx-auto px-4 py-4 lg:py-8 z-10">
      <div class="flex flex-col lg:flex-row items-center lg:items-center gap-6 lg:gap-16 justify-center min-h-[500px] lg:min-h-[560px]">

        <!-- LEFT: Stacked Card Carousel -->
        <div class="relative w-full lg:w-auto flex justify-center items-center" style="perspective: 1200px">
          <div class="relative w-[260px] sm:w-[280px] lg:w-[320px] h-[360px] sm:h-[380px] lg:h-[420px]">
            <div
              v-for="(member, index) in members"
              :key="member.name"
              class="absolute inset-0 cursor-pointer transition-all duration-700 ease-out"
              :style="getCardStyle(index)"
              @click="goTo(index)"
            >
              <div
                class="w-full h-full rounded-2xl lg:rounded-3xl overflow-hidden shadow-2xl border-2 transition-all duration-700"
                :class="[
                  index === currentIndex
                    ? 'border-brand-600/50 shadow-brand-800/20'
                    : 'border-surface-700/20 shadow-surface-900/40',
                  index !== currentIndex ? 'grayscale' : ''
                ]"
              >
                <img
                  :src="member.photo"
                  :alt="member.name"
                  class="w-full h-full object-cover object-top"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- RIGHT: Info Panel -->
        <div class="w-full lg:w-auto flex flex-col items-center lg:items-start justify-center lg:min-w-[340px] lg:max-w-[400px]">
          <!-- Social Icons -->
          <transition name="text-fade" mode="out-in">
            <div :key="currentMember.name + '-social'" class="flex items-center gap-3 mb-6">
              <a
                :href="currentMember.facebook"
                target="_blank"
                rel="noopener noreferrer"
                class="w-10 h-10 rounded-full bg-blue-600/15 flex items-center justify-center hover:bg-blue-600/25 transition-all duration-300 group"
              >
                <img :src="facebookIcon" alt="Facebook" class="w-5 h-5 opacity-60 group-hover:opacity-100 transition-opacity" />
              </a>
            </div>
          </transition>

          <!-- Name with decorative lines -->
          <div class="flex items-center gap-4 mb-1 justify-center lg:justify-start w-full">
            <span class="h-[2px] w-10 bg-gradient-to-r from-transparent to-brand-600/60 hidden sm:block"></span>
            <transition name="text-fade" mode="out-in">
              <h2
                :key="currentMember.name"
                class="text-2xl sm:text-3xl lg:text-4xl font-bold font-display text-surface-100 whitespace-nowrap"
              >
                {{ currentMember.name }}
              </h2>
            </transition>
            <span class="h-[2px] w-10 bg-gradient-to-l from-transparent to-brand-600/60 hidden sm:block"></span>
          </div>

          <!-- Role -->
          <transition name="text-fade" mode="out-in">
            <p
              :key="currentMember.role"
              class="text-xs font-bold tracking-[.25em] uppercase text-surface-400 mb-5 text-center lg:text-left w-full"
            >
              {{ currentMember.role }}
            </p>
          </transition>

          <!-- Bionote -->
          <transition name="text-fade" mode="out-in">
            <p
              :key="currentMember.name + '-bio'"
              class="text-sm text-surface-400 leading-relaxed mb-6 max-h-32 overflow-y-auto pr-2 text-center lg:text-left bio-scroll"
            >
              {{ currentMember.bio }}
            </p>
          </transition>

          <!-- Pagination Dots -->
          <div class="flex items-center gap-2.5 mt-2">
            <button
              v-for="(member, index) in members"
              :key="member.name + '-dot'"
              @click="goTo(index)"
              class="rounded-full transition-all duration-500"
              :class="index === currentIndex
                ? 'w-3 h-3 bg-brand-600 shadow-lg shadow-brand-600/40'
                : 'w-2.5 h-2.5 bg-surface-600 hover:bg-surface-500'"
              :aria-label="'Go to ' + member.name"
            ></button>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile Quick Select -->
    <div class="lg:hidden px-4 py-6 relative z-10">
      <div class="text-center mb-4">
        <p class="text-xs text-surface-500 uppercase tracking-widest">All Members</p>
      </div>
      <div class="flex justify-center gap-3 flex-wrap">
        <button
          v-for="(member, index) in members"
          :key="member.name + '-thumb'"
          @click="goTo(index); scrollToTop()"
          class="group transition-all duration-300"
        >
          <div
            class="w-12 h-12 rounded-full overflow-hidden border-2 transition-all duration-300"
            :class="index === currentIndex
              ? 'border-brand-600 scale-110 shadow-lg shadow-brand-600/30'
              : 'border-surface-700/30 grayscale opacity-60 hover:opacity-80'"
          >
            <img :src="member.photo" :alt="member.name" class="w-full h-full object-cover object-top" />
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { rafThrottle } from '../utils/timing'
import { useTheme } from '../composables/useTheme'

const { theme } = useTheme()
import dacerPhoto from '../assets/members/Dacer.jpg'
import tiuPhoto from '../assets/members/Tiu.jpg'
import romuloPhoto from '../assets/members/Romulo.png'
import valeroPhoto from '../assets/members/Valero.png'
import soberanoPhoto from '../assets/members/Soberano.png'
import lacernaPhoto from '../assets/members/Lacerna.png'
import facebookIcon from '../assets/facebook.svg'

const members = [
  {
    name: 'Asriel Romulo',
    role: 'Leader',
    photo: romuloPhoto,
    facebook: 'https://www.facebook.com/calixta27',
    bio: 'A student in the Bachelor of Engineering Technology major in Computer Engineering Technology program at the Technological University of the Philippines-Manila. In this capstone study, she contributed to setting up the hardware components and helped develop the prototype, including fabricating the project. She is also an editor and is responsible for proofreading. She was responsible for organizing and finalizing the entire paper. She manages team logistics and project budgeting.',
  },
  {
    name: 'Jonamae Tiu',
    role: 'Papers',
    photo: tiuPhoto,
    facebook: 'https://www.facebook.com/nam.ssi.906',
    bio: 'A student in the Bachelor of Engineering Technology major in Computer Engineering Technology program at the Technological University of the Philippines-Manila. She assisted in setting up the hardware components. She is also one of the paper\'s editors. She also assisted in organizing and finalizing the entire paper.',
  },
  {
    name: 'Zharie Ann R. Valero',
    role: 'Papers',
    photo: valeroPhoto,
    facebook: 'https://www.facebook.com/ZharieAnn23',
    bio: 'A student in the Bachelor of Engineering Technology major in Computer Engineering Technology program at the Technological University of the Philippines-Manila. She is also one of the paper\'s editors. She also assisted in organizing and finalizing the entire paper.',
  },
  {
    name: 'John Renzo G. Dacer',
    role: 'Lead UX/UI',
    photo: dacerPhoto,
    facebook: 'https://www.facebook.com/huaxxxxiii',
    bio: 'A student in the Bachelor of Engineering Technology major in Computer Engineering Technology program at the Technological University of the Philippines-Manila. In this capstone study, he is one of the main programmers on the software system, front-end and back-end development team. He also assisted in setting up the hardware.',
  },
  {
    name: 'Gideon Soberano',
    role: 'Lead Programmer',
    photo: soberanoPhoto,
    facebook: 'https://www.facebook.com/gideon.soberano',
    bio: 'A student in the Bachelor of Engineering Technology major in Computer Engineering Technology program at the Technological University of the Philippines-Manila. In this capstone study, he has designed the main prototype, ensuring its structure and layout align with the project\'s objectives and functional requirements. He also assisted the front-end and back-end developer teams. He also assisted in organizing the entire paper.',
  },
  {
    name: 'Jose Angelo F. Lacerna',
    role: 'Lead Programmer',
    photo: lacernaPhoto,
    facebook: 'https://www.facebook.com/joseangelo.lacerna.9',
    bio: 'A student in the Bachelor of Engineering Technology major in Computer Engineering Technology program at the Technological University of the Philippines-Manila. In this capstone study, he is one of the main programmers on the software system, front-end and back-end development team. He also assisted in setting up the hardware.',
  },
]

const currentIndex = ref(0)
const currentMember = computed(() => members[currentIndex.value])

function goTo(index) {
  currentIndex.value = index
}

function goNext() {
  currentIndex.value = (currentIndex.value + 1) % members.length
}

function goPrev() {
  currentIndex.value = (currentIndex.value - 1 + members.length) % members.length
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleKeydown(e) {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    e.preventDefault()
    goNext()
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault()
    goPrev()
  }
}

// Keep the card stack animation smooth if the user holds a key down.
const handleKeydownRaf = rafThrottle(handleKeydown)

onMounted(() => {
  window.addEventListener('keydown', handleKeydownRaf)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydownRaf)
})

function getCardStyle(index) {
  const diff = index - currentIndex.value
  const absDiff = Math.abs(diff)

  if (absDiff > 2) {
    return {
      transform: `translateY(${diff > 0 ? 180 : -180}px) scale(0.6) rotateZ(${diff > 0 ? 8 : -8}deg)`,
      opacity: 0,
      zIndex: 0,
      pointerEvents: 'none',
    }
  }

  // Fan/stack effect: offset + slight rotation
  const translateY = diff * 55
  const translateX = diff * -15
  const scale = 1 - absDiff * 0.08
  const opacity = 1 - absDiff * 0.35
  const zIndex = 10 - absDiff
  const rotateZ = diff * -4

  return {
    transform: `translateY(${translateY}px) translateX(${translateX}px) scale(${scale}) rotateZ(${rotateZ}deg)`,
    opacity: Math.max(opacity, 0),
    zIndex,
    pointerEvents: absDiff === 0 ? 'auto' : 'auto',
  }
}
</script>

<style scoped>
.text-fade-enter-active { transition: all 0.4s ease-out; }
.text-fade-leave-active { transition: all 0.2s ease-in; }
.text-fade-enter-from { opacity: 0; transform: translateY(10px); }
.text-fade-leave-to { opacity: 0; transform: translateY(-10px); }

.grayscale {
  filter: grayscale(100%);
}

.light-bg-gradient {
  background: linear-gradient(135deg, #f8fafc, #e2e8f0, #f1f5f9);
}

/* Custom scrollbar for bionote */
.bio-scroll::-webkit-scrollbar { width: 3px; }
.bio-scroll::-webkit-scrollbar-track { background: transparent; }
.bio-scroll::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 2px; }
</style>
