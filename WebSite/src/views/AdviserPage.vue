<template>
  <div class="relative overflow-hidden min-h-[calc(100vh-4rem)] flex items-center justify-center">
    <!-- Background Effects -->
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute top-1/4 right-1/4 w-80 h-80 bg-gold-400/5 light:bg-gold-500/10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 left-1/4 w-72 h-72 bg-brand-800/8 light:bg-brand-600/10 rounded-full blur-3xl"></div>
    </div>

    <div class="relative w-full max-w-4xl mx-auto px-4 py-8 lg:py-16">
      <!-- Page Header -->
      <div class="text-center mb-10 sm:mb-16">
        <h1 class="text-3xl sm:text-4xl lg:text-5xl font-bold font-display mb-4 animate-fade-in">
          <span class="text-surface-100">Our</span>
          <span class="gradient-text ml-2">Adviser</span>
        </h1>
        <p class="text-surface-400 max-w-lg mx-auto animate-fade-in" style="animation-delay: 0.1s">
          Meet the professor who guided and mentored us throughout this capstone project.
        </p>
      </div>

      <!-- Adviser Card -->
      <div 
        @click="toggleCard"
        class="card-wrapper group relative w-full h-[480px] sm:h-[500px] max-w-[320px] sm:max-w-[360px] md:max-w-[400px] mx-auto rounded-3xl overflow-hidden shadow-2xl light:shadow-xl transition-all duration-500 hover:-translate-y-2 animate-slide-up cursor-pointer"
      >
        
        <!-- Magic Card Glowing Border Effect -->
        <div class="absolute inset-0 z-0">
           <div 
             class="absolute inset-[-8px] rounded-3xl animate-spin-slow transition-opacity duration-1000"
             :class="isFlipped ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'"
             style="background: conic-gradient(from var(--angle), transparent 60%, #38bdf8, #818cf8, #c084fc);"
           ></div>
        </div>

        <!-- Card Inner Surface -->
        <div class="absolute inset-[3px] rounded-[22px] bg-surface-950 light:bg-white z-10 overflow-hidden flex flex-col shadow-inner">
          
          <!-- Front State: Picture & Basic Info -->
          <div 
            class="absolute inset-0 flex flex-col items-center justify-center p-6 transition-all duration-700 ease-in-out bg-surface-950 light:bg-white"
            :class="isFlipped ? 'opacity-0 scale-95 pointer-events-none' : 'opacity-100 scale-100 group-hover:opacity-0 group-hover:scale-95 group-hover:pointer-events-none'"
          >
            <div class="w-44 h-44 sm:w-52 sm:h-52 rounded-full overflow-hidden border-[3px] border-surface-800 light:border-surface-200 mb-6 shadow-xl transition-transform duration-500 group-hover:scale-105 mt-2">
              <img :src="adviserPhoto" alt="Prof. Gemma Belga" class="w-full h-full object-cover object-top" />
            </div>
            
            <h3 class="text-2xl sm:text-3xl font-display font-bold text-surface-100 pb-1 text-center">
              Prof. Gemma Belga
            </h3>
            <p class="text-gold-400 light:text-gold-600 mt-2 font-bold tracking-[0.2em] uppercase text-xs">
              Adviser
            </p>
            
            <!-- Mobile Tap Indicator -->
            <div class="mt-6 flex flex-col items-center opacity-60 light:opacity-50 sm:hidden animate-pulse">
              <svg class="w-5 h-5 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"></path>
              </svg>
              <span class="text-[10px] mt-1 text-surface-400 font-medium">Tap to flip</span>
            </div>
          </div>

          <!-- Back State (Hover/Flipped): Detailed Bio & Contact -->
          <div 
            class="absolute inset-0 flex flex-col items-center justify-between p-6 sm:p-8 bg-surface-950/98 light:bg-white/98 backdrop-blur-md transition-all duration-700 ease-in-out z-20 text-center"
            :class="isFlipped ? 'opacity-100 scale-100 pointer-events-auto' : 'opacity-0 scale-105 group-hover:opacity-100 group-hover:scale-100 pointer-events-none group-hover:pointer-events-auto'"
          >
            
            <div class="flex flex-col items-center w-full mt-2 sm:mt-4">
              <h2 class="text-xl sm:text-2xl lg:text-3xl font-bold font-display text-surface-100 mb-3">
                Prof. Gemma D. Belga - Robles
              </h2>
              <span class="inline-block px-3 py-1.5 rounded-full text-[10px] sm:text-xs font-bold tracking-widest uppercase bg-brand-600/20 light:bg-brand-100 text-brand-400 light:text-brand-700 border border-brand-600/30 light:border-brand-300 mb-4 sm:mb-6">
                College CIT Secretary
              </span>
              
              <p class="text-surface-400 text-xs sm:text-sm md:text-base leading-relaxed flex-1 max-h-[180px] sm:max-h-[160px] overflow-y-auto custom-scroll px-1 sm:px-2">
                Prof. Gemma D. Belga - Robles serves as the College Secretary for the College of Industrial Technology (CIT) at the Technological University of the Philippines. As our dedicated capstone and thesis adviser, she has provided invaluable guidance, technical expertise, and continuous support throughout the development of the Smart Hygiene Vending Machine project, ensuring its alignment with both academic standards and practical engineering applications.
              </p>
            </div>

            <!-- Contact Info / Email -->
            <div class="w-full pt-4 sm:pt-5 pb-2 border-t border-surface-800/50 light:border-surface-200 mt-4">
              <div class="flex flex-col items-center gap-3">
                <a href="mailto:gemma_belga@tup.edu.ph" class="flex items-center gap-2 text-surface-400 light:text-surface-500 hover:text-brand-400 light:hover:text-brand-600 transition-colors group/link w-full justify-center">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span class="text-xs sm:text-sm font-medium pr-1 group-hover/link:underline decoration-brand-400/50 light:decoration-brand-600/50 underline-offset-4 truncate max-w-[200px] sm:max-w-full">
                    gemma_belga@tup.edu.ph
                  </span>
                </a>
                <a href="mailto:cit@tup.edu.ph" class="flex items-center gap-2 text-surface-400 light:text-surface-500 hover:text-brand-400 light:hover:text-brand-600 transition-colors group/link w-full justify-center">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span class="text-xs sm:text-sm font-medium group-hover/link:underline decoration-brand-400/50 light:decoration-brand-600/50 underline-offset-4">
                    cit@tup.edu.ph
                  </span>
                </a>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTheme } from '../composables/useTheme'
import profBelgaDark from '../assets/members/ProfBelga.png'
import profBelgaLight from '../assets/members/ProfBelga2.png'

const { theme } = useTheme()

const adviserPhoto = computed(() => (theme.value === 'light' ? profBelgaLight : profBelgaDark))

const isFlipped = ref(false)

const toggleCard = () => {
  isFlipped.value = !isFlipped.value
}
</script>

<style scoped>
@property --angle {
  syntax: "<angle>";
  initial-value: 0deg;
  inherits: false;
}

.animate-spin-slow {
  animation: spin 3s linear infinite;
}

@keyframes spin {
  from {
    --angle: 0deg;
  }
  to {
    --angle: 360deg;
  }
}

.custom-scroll::-webkit-scrollbar { width: 4px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.3); border-radius: 4px; }
</style>
