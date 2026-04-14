<template>
  <div class="relative overflow-hidden min-h-[calc(100vh-4rem)]">
    <!-- Background Effects -->
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute top-1/4 right-1/4 w-80 h-80 bg-gold-400/5 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 left-1/4 w-72 h-72 bg-brand-800/8 rounded-full blur-3xl"></div>
    </div>

    <div class="relative max-w-4xl mx-auto px-4 py-16 lg:py-24">
      <!-- Page Header -->
      <div class="text-center mb-16">
        <h1 class="text-3xl sm:text-4xl lg:text-5xl font-bold font-display mb-4 animate-fade-in">
          <span class="text-surface-100">Our</span>
          <span class="gradient-text ml-2">Adviser</span>
        </h1>
        <p class="text-surface-400 max-w-lg mx-auto animate-fade-in" style="animation-delay: 0.1s">
          Meet the professor who guided and mentored us throughout this capstone project.
        </p>
      </div>

      <!-- Adviser Card -->
      <div class="glass rounded-3xl p-8 sm:p-12 lg:p-16 max-w-2xl mx-auto relative overflow-hidden animate-slide-up">
        <!-- Decorative accent -->
        <div class="absolute top-0 right-0 w-48 h-48 bg-gradient-to-bl from-gold-400/8 to-transparent rounded-bl-full"></div>
        <div class="absolute bottom-0 left-0 w-32 h-32 bg-gradient-to-tr from-brand-800/10 to-transparent rounded-tr-full"></div>

        <div class="relative text-center">
          <!-- Avatar Placeholder -->
          <div class="w-32 h-32 sm:w-40 sm:h-40 mx-auto rounded-full bg-gradient-to-br from-gold-400/20 to-brand-800/20 border-2 border-gold-400/20 flex items-center justify-center mb-8">
            <svg class="w-16 h-16 sm:w-20 sm:h-20 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>

          <!-- Info -->
          <div class="flex items-center justify-center gap-4 mb-2">
            <span class="h-px w-10 bg-gradient-to-r from-transparent to-gold-400/50"></span>
            <h2 class="text-2xl sm:text-3xl font-bold font-display text-surface-100">
              Ma'am Belga
            </h2>
            <span class="h-px w-10 bg-gradient-to-l from-transparent to-gold-400/50"></span>
          </div>

          <span class="inline-block px-4 py-1.5 rounded-full text-xs font-bold tracking-widest uppercase bg-gold-400/10 text-gold-400 border border-gold-400/20 mb-6">
            Capstone Adviser/Thesis Adviser
          </span>

          <p class="text-surface-400 text-sm leading-relaxed max-w-md mx-auto">
            Adviser details will be added soon. This section will feature our capstone adviser's profile, credentials, and academic contributions.
          </p>

          <!-- Decorative divider -->
          <div class="flex items-center justify-center gap-3 mt-8">
            <span class="h-px w-16 bg-surface-800"></span>
            <div class="w-2 h-2 rounded-full bg-gold-400/30"></div>
            <span class="h-px w-16 bg-surface-800"></span>
          </div>

          <!-- Department -->
          <p class="text-xs text-surface-500 mt-6 uppercase tracking-wider">
            Technological University of the Philippines — Manila<br>
            College of Engineering — CpET Department
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>
