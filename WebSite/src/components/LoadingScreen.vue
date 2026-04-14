<template>
  <transition name="loading-fade">
    <div v-if="visible" class="loading-overlay">
      <!-- Cat SVG Animation -->
      <div class="cat-container">
        <svg class="cat-svg" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          <!-- Tail -->
          <path class="cat-tail" d="M130 155 C145 140, 165 130, 170 115" stroke="#f59e0b" stroke-width="4" fill="none" stroke-linecap="round"/>

          <!-- Body -->
          <ellipse cx="100" cy="155" rx="38" ry="25" fill="#f59e0b" class="cat-body"/>

          <!-- Head -->
          <circle cx="100" cy="110" r="28" fill="#f59e0b" class="cat-head"/>

          <!-- Left Ear -->
          <polygon points="78,90 70,62 92,82" fill="#f59e0b"/>
          <polygon points="80,88 74,68 90,83" fill="#fbbf24"/>

          <!-- Right Ear -->
          <polygon points="122,90 130,62 108,82" fill="#f59e0b"/>
          <polygon points="120,88 126,68 110,83" fill="#fbbf24"/>

          <!-- Eyes -->
          <g class="cat-eyes">
            <ellipse cx="90" cy="108" rx="5" ry="5.5" fill="#1e293b"/>
            <ellipse cx="110" cy="108" rx="5" ry="5.5" fill="#1e293b"/>
            <!-- Eye shine -->
            <circle cx="88" cy="106" r="1.5" fill="white"/>
            <circle cx="108" cy="106" r="1.5" fill="white"/>
          </g>

          <!-- Nose -->
          <polygon points="100,115 97,118 103,118" fill="#ec7a95"/>

          <!-- Mouth -->
          <path d="M97 119 Q100 123 103 119" stroke="#a16207" stroke-width="1" fill="none"/>
          <path d="M93 118 Q90 121 86 119" stroke="#a16207" stroke-width="0.8" fill="none"/>
          <path d="M107 118 Q110 121 114 119" stroke="#a16207" stroke-width="0.8" fill="none"/>

          <!-- Whiskers -->
          <g class="cat-whiskers" stroke="#a16207" stroke-width="0.8" fill="none">
            <line x1="65" y1="112" x2="85" y2="115"/>
            <line x1="63" y1="118" x2="84" y2="118"/>
            <line x1="65" y1="124" x2="85" y2="121"/>
            <line x1="135" y1="112" x2="115" y2="115"/>
            <line x1="137" y1="118" x2="116" y2="118"/>
            <line x1="135" y1="124" x2="115" y2="121"/>
          </g>

          <!-- Front Paws -->
          <ellipse cx="82" cy="172" rx="10" ry="6" fill="#f59e0b" class="cat-paw-l"/>
          <ellipse cx="118" cy="172" rx="10" ry="6" fill="#f59e0b" class="cat-paw-r"/>

          <!-- Paw Details -->
          <g fill="#fbbf24" class="cat-paw-l">
            <circle cx="78" cy="171" r="2"/>
            <circle cx="82" cy="169" r="2"/>
            <circle cx="86" cy="171" r="2"/>
          </g>
          <g fill="#fbbf24" class="cat-paw-r">
            <circle cx="114" cy="171" r="2"/>
            <circle cx="118" cy="169" r="2"/>
            <circle cx="122" cy="171" r="2"/>
          </g>
        </svg>

        <!-- Loading dots -->
        <div class="loading-text">
          <span class="brand-text">Syntax Error</span>
          <div class="dot-container">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const visible = ref(true)

onMounted(() => {
  setTimeout(() => {
    visible.value = false
  }, 2200)
})
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #020617;
  transition: opacity 0.6s ease, visibility 0.6s ease;
}

html.light .loading-overlay {
  background: #f2f2f7;
}

.cat-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.cat-svg {
  width: 140px;
  height: 140px;
  animation: catBounce 1.2s ease-in-out infinite;
}

/* Cat bounce */
@keyframes catBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

/* Tail wag */
.cat-tail {
  animation: tailWag 0.8s ease-in-out infinite alternate;
  transform-origin: 130px 155px;
}

@keyframes tailWag {
  0% { d: path("M130 155 C145 140, 165 130, 170 115"); }
  100% { d: path("M130 155 C145 140, 165 145, 175 135"); }
}

/* Eye blink */
.cat-eyes {
  animation: blink 3s ease-in-out infinite;
}

@keyframes blink {
  0%, 92%, 100% { transform: scaleY(1); }
  95% { transform: scaleY(0.1); }
}

/* Whisker twitch */
.cat-whiskers {
  animation: whiskerTwitch 2s ease-in-out infinite;
}

@keyframes whiskerTwitch {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(1deg); }
  75% { transform: rotate(-1deg); }
}

/* Paw kneading */
.cat-paw-l {
  animation: pawKneadL 1.2s ease-in-out infinite;
}

.cat-paw-r {
  animation: pawKneadR 1.2s ease-in-out infinite;
}

@keyframes pawKneadL {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

@keyframes pawKneadR {
  0%, 100% { transform: translateY(-3px); }
  50% { transform: translateY(0); }
}

.loading-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.brand-text {
  font-family: 'Outfit', 'Inter', system-ui, sans-serif;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #f1f5f9;
}

html.light .brand-text {
  color: #0f172a;
}

.dot-container {
  display: flex;
  gap: 6px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f59e0b;
  animation: dotPulse 1.4s ease-in-out infinite;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotPulse {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1.1); opacity: 1; }
}

/* Fade out */
.loading-fade-leave-active {
  transition: opacity 0.5s ease;
}

.loading-fade-leave-to {
  opacity: 0;
}
</style>
