<template>
  <div class="relative min-h-[calc(100vh-4rem)] flex flex-col lg:flex-row">

    <!-- Overlay for mobile sidebar -->
    <div
      v-if="sidebarOpen"
      @click="sidebarOpen = false"
      class="lg:hidden fixed inset-0 bg-surface-950/60 z-40 backdrop-blur-sm transition-opacity"
    ></div>

    <!-- Sidebar -->
    <aside
      class="fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out glass lg:translate-x-0 lg:sticky lg:top-16 lg:h-[calc(100vh-4rem)] lg:z-30 lg:border-r border-surface-800/30 flex flex-col shadow-2xl lg:shadow-none"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="p-5 lg:p-6 pb-2">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-2xl lg:text-3xl font-bold font-display text-surface-100 light:text-surface-900 mb-0.5 tracking-tight">Admin</h2>
            <p class="text-xs lg:text-sm text-surface-400 light:text-surface-700 font-medium break-all">{{ currentUser?.username || '—' }}</p>
          </div>
          <!-- Profile Image Upload Node -->
          <div class="relative group cursor-pointer w-12 h-12 shrink-0">
            <input type="file" accept="image/*" @change="handleProfileUpload" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" title="Change Profile Picture" />
            <div class="w-full h-full rounded-full overflow-hidden bg-surface-800/40 border-2 border-transparent group-hover:border-brand-500/50 transition-all duration-300 transform group-hover:scale-110 group-hover:rotate-[15deg] shadow-md flex items-center justify-center">
              <img v-if="adminProfileImage" :src="adminProfileImage" class="w-full h-full object-cover" />
              <svg v-else class="w-6 h-6 text-surface-400 group-hover:text-brand-500 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
            </div>
          </div>
        </div>

        <nav class="space-y-1.5 flex-1">
          <button
            v-for="item in sidebarItems"
            :key="item.id"
            @click="activeSection = item.id; sidebarOpen = false"
            class="relative w-full flex items-center p-3.5 rounded-2xl transition-all duration-300 group"
            :class="activeSection === item.id
              ? 'bg-brand-700 text-white shadow-lg shadow-brand-800/30 border border-brand-900/10'
              : 'text-surface-500 hover:text-surface-100 font-medium hover:bg-surface-800/30'"
          >
            <span v-html="item.icon" class="absolute left-4 w-5 h-5 shrink-0 transition-opacity" :class="activeSection === item.id ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'"></span>
            <span class="w-full text-center leading-[1.25] text-[14.5px] font-display pr-1 pl-6" :class="activeSection === item.id ? 'font-bold' : 'font-medium'">{{ item.label }}</span>
          </button>
        </nav>
      </div>

      <div class="flex-1"></div>

      <!-- Philippines clock (sidebar bottom, above logout) -->
      <div class="px-5 lg:px-6 pb-3">
        <div class="rounded-2xl border border-surface-800/40 light:border-surface-200/80 bg-surface-900/50 light:bg-surface-100/90 px-3 py-3 text-center shadow-inner">
          <p class="text-lg font-mono font-bold text-surface-100 light:text-surface-900 tabular-nums tracking-tight">{{ phTime }}</p>
          <p class="text-[11px] text-surface-400 light:text-surface-600 mt-1">{{ phDate }} · PHT</p>
        </div>
      </div>

      <!-- Logout -->
      <div class="p-5 lg:p-6 pt-2 border-t border-surface-800/30 mt-auto">
        <button
          @click="handleLogout"
          class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-[14.5px] font-bold text-red-500 hover:bg-red-500/10 hover:text-red-400 transition-all duration-300"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span class="leading-none mt-0.5">Logout</span>
        </button>
      </div>
    </aside>

    <!-- Mobile sidebar toggle -->
    <button
      @click="sidebarOpen = !sidebarOpen"
      class="lg:hidden fixed bottom-6 right-6 z-30 w-14 h-14 rounded-full bg-brand-700 text-white shadow-xl shadow-brand-800/40 flex items-center justify-center active:scale-95 transition-transform border border-brand-600/30"
    >
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>

    <!-- Main Content -->
    <main class="flex-1 w-full lg:w-auto p-4 sm:p-6 lg:p-8">

      <!-- Header -->
      <div class="flex flex-wrap items-center justify-between gap-2 mb-6">
        <h1 class="text-xl sm:text-2xl font-bold font-display text-surface-100">
          {{ currentSidebarItem?.label || 'Overview' }}
        </h1>
        <div class="flex items-center gap-3">
          <span class="flex h-2.5 w-2.5 relative">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span class="text-xs text-surface-400">Online</span>
        </div>
      </div>

      <!-- OVERVIEW SECTION -->
      <div v-if="activeSection === 'overview'">
        <!-- Metric Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6">
          <div
            v-for="(stat, i) in overviewStats"
            :key="stat.label"
            class="ios-card rounded-2xl p-4 sm:p-5 animate-slide-up relative"
            :class="stat.id === 'totalSales' && showSalesModeMenu && !isCompactUi ? 'z-[80]' : 'z-0'"
            :style="{ animationDelay: `${i * 0.05}s` }"
          >
            <p class="text-xs text-surface-500 uppercase tracking-wider mb-1">{{ stat.label }}</p>
            <button
              v-if="stat.id === 'totalSales'"
              type="button"
              class="text-left w-full rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              @click="toggleSalesModeMenu"
              ref="salesModeBtnEl"
            >
              <p class="text-xl sm:text-2xl font-bold font-display" :class="stat.color">{{ stat.value }}</p>
              <p class="text-[11px] text-surface-500 mt-1 font-semibold">
                {{ salesModeLabel }} · click to change
              </p>
            </button>
            <p v-else class="text-xl sm:text-2xl font-bold font-display" :class="stat.color">{{ stat.value }}</p>

            <transition name="sales-pop">
              <div
                v-if="!isCompactUi && stat.id === 'totalSales' && showSalesModeMenu"
                ref="salesModeMenuEl"
                class="absolute top-3 right-3 z-[90] w-52 rounded-2xl border border-surface-800/50 light:border-surface-200/80 bg-surface-950/90 light:bg-white/95 backdrop-blur-xl shadow-[0_22px_60px_rgba(0,0,0,0.55)] light:shadow-[0_18px_50px_rgba(2,6,23,0.18)] overflow-hidden"
              >
                <div class="px-3 py-2.5 border-b border-surface-800/40 light:border-surface-200/70">
                  <p class="text-[10px] uppercase tracking-[0.18em] text-surface-500 light:text-surface-600 font-extrabold">Total sales</p>
                  <p class="text-[11px] text-surface-400 light:text-surface-600 -mt-0.5">Choose a range</p>
                </div>
                <div class="p-2 max-h-72 overflow-y-auto overscroll-contain sales-menu-scroll space-y-1">
                  <button
                    v-for="opt in totalSalesModeOptions"
                    :key="opt.id"
                    type="button"
                    class="w-full flex items-center justify-between px-3 py-2 rounded-xl text-[12px] font-bold transition-colors duration-150"
                    :class="totalSalesMode === opt.id
                      ? 'bg-brand-600 text-white shadow-lg shadow-brand-900/20'
                      : 'text-surface-200 light:text-surface-800 hover:bg-surface-800/40 light:hover:bg-surface-200/70 active:bg-surface-800/55 light:active:bg-surface-200/90'"
                    @click.stop="setTotalSalesMode(opt.id)"
                  >
                    <span>{{ opt.label }}</span>
                    <span
                      class="w-5 h-5 rounded-lg flex items-center justify-center"
                      :class="totalSalesMode === opt.id ? 'bg-white/15 text-white' : 'text-surface-500 light:text-surface-500'"
                    >
                      <svg v-if="totalSalesMode === opt.id" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M16.704 5.29a1 1 0 010 1.415l-7.25 7.25a1 1 0 01-1.415 0l-3.25-3.25a1 1 0 011.415-1.415l2.542 2.543 6.542-6.543a1 1 0 011.416 0z" clip-rule="evenodd" />
                      </svg>
                    </span>
                  </button>
                </div>
              </div>
            </transition>
          </div>
        </div>

        <!-- Mobile/compact: Total Sales bottom sheet -->
        <transition name="sales-sheet">
          <div v-if="isCompactUi && showSalesModeMenu" class="fixed inset-0 z-[60]">
            <button
              type="button"
              class="absolute inset-0 bg-surface-950/70 light:bg-surface-950/30 backdrop-blur-[2px]"
              @click="closeSalesModeMenu"
              aria-label="Close"
            />
            <div class="absolute left-0 right-0 bottom-0">
              <div class="mx-auto max-w-md">
                <div class="rounded-t-3xl border border-surface-800/60 light:border-surface-200 bg-surface-950/95 light:bg-white/98 backdrop-blur-xl shadow-[0_-18px_50px_rgba(0,0,0,0.55)]">
                  <div class="px-5 pt-3 pb-2 border-b border-surface-800/40 light:border-surface-200/70">
                    <div class="w-10 h-1 rounded-full bg-surface-700/60 light:bg-surface-300 mx-auto mb-3"></div>
                    <p class="text-xs font-extrabold tracking-widest uppercase text-surface-500 light:text-surface-600">Total sales</p>
                    <p class="text-sm font-bold text-surface-100 light:text-surface-900 mt-1">{{ salesModeLabel }}</p>
                  </div>
                  <div class="p-3 max-h-[50vh] overflow-y-auto overscroll-contain sales-menu-scroll space-y-2">
                    <button
                      v-for="opt in totalSalesModeOptions"
                      :key="opt.id"
                      type="button"
                      class="w-full flex items-center justify-between px-4 py-3 rounded-2xl text-sm font-bold transition-colors"
                      :class="totalSalesMode === opt.id
                        ? 'bg-brand-600 text-white shadow-lg shadow-brand-900/20'
                        : 'bg-surface-900/40 light:bg-surface-100 text-surface-100 light:text-surface-900 border border-surface-800/40 light:border-surface-200 hover:bg-surface-800/40 light:hover:bg-surface-200/70'"
                      @click="setTotalSalesMode(opt.id)"
                    >
                      <span>{{ opt.label }}</span>
                      <span class="w-6 h-6 rounded-xl flex items-center justify-center" :class="totalSalesMode === opt.id ? 'bg-white/15' : 'bg-surface-800/40 light:bg-surface-200/70'">
                        <svg v-if="totalSalesMode === opt.id" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M16.704 5.29a1 1 0 010 1.415l-7.25 7.25a1 1 0 01-1.415 0l-3.25-3.25a1 1 0 011.415-1.415l2.542 2.543 6.542-6.543a1 1 0 011.416 0z" clip-rule="evenodd" />
                        </svg>
                      </span>
                    </button>
                  </div>
                  <div class="p-4 border-t border-surface-800/40 light:border-surface-200/70">
                    <button type="button" class="w-full py-3 rounded-2xl font-bold text-sm bg-surface-900/40 light:bg-surface-100 text-surface-200 light:text-surface-800 border border-surface-800/40 light:border-surface-200" @click="closeSalesModeMenu">
                      Close
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </transition>

        <p v-if="!machine.loading" class="text-xs text-surface-500 mb-4">{{ machineSummaryLine }}</p>

        <!-- Realtime activity from vending machine -->
          <div class="ios-card rounded-2xl p-5 sm:p-6 mb-6">
            <div class="flex flex-wrap items-start justify-between gap-3 mb-1">
              <h3 class="text-sm font-bold text-surface-200 light:text-surface-900 mb-1">Machine live feed</h3>
              <div class="flex items-center flex-wrap justify-end gap-1.5">
                <button
                  v-for="opt in liveFeedRangeOptions"
                  :key="opt.id"
                  type="button"
                  class="px-2.5 py-1.5 rounded-lg text-[11px] font-bold transition-colors border"
                  :class="liveFeedRange === opt.id
                    ? 'bg-brand-600 text-white border-brand-500/30 shadow-lg shadow-brand-900/25'
                    : 'bg-surface-900/30 text-surface-400 border-surface-800/40 hover:text-surface-200 hover:bg-surface-800/30'"
                  @click="liveFeedRange = opt.id"
                >
                  {{ opt.label }}
                </button>
              </div>
            </div>
          <div class="overflow-x-auto max-h-52 overflow-y-auto rounded-xl border border-surface-800/30">
            <table class="w-full text-sm">
              <thead class="sticky top-0 bg-surface-950/95 light:bg-surface-100/95 z-10">
                <tr class="border-b border-surface-800/40">
                  <th class="text-left text-xs text-surface-400 uppercase pb-2 pr-3 font-semibold">Time (PH)</th>
                  <th class="text-left text-xs text-surface-400 uppercase pb-2 pr-3 font-semibold">Type</th>
                  <th class="text-left text-xs text-surface-400 uppercase pb-2 font-semibold">Message</th>
                  <th class="hidden sm:table-cell text-right text-xs text-surface-400 uppercase pb-2 pr-3 font-semibold whitespace-nowrap">Quantity</th>
                  <th class="hidden sm:table-cell text-left text-xs text-surface-400 uppercase pb-2 font-semibold whitespace-nowrap">IR - Beam Sensed</th>
                  <th class="hidden sm:table-cell text-right text-xs text-surface-400 uppercase pb-2 font-semibold whitespace-nowrap">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in liveFeedPreview" :key="row.key" class="border-b border-surface-800/20">
                  <td class="py-2 pr-3 text-surface-500 text-xs whitespace-nowrap">{{ row.time }}</td>
                  <td class="py-2 pr-3 text-brand-400 text-xs">{{ row.type }}</td>
                  <td class="py-2 text-surface-200 text-xs">{{ row.message }}</td>
                  <td class="hidden sm:table-cell py-2 pr-3 text-right text-surface-300 text-xs whitespace-nowrap">{{ row.quantity ?? '—' }}</td>
                  <td class="hidden sm:table-cell py-2 text-surface-300 text-xs whitespace-nowrap">{{ row.irBeamSensed ?? '—' }}</td>
                  <td class="hidden sm:table-cell py-2 text-right text-surface-300 text-xs whitespace-nowrap">{{ row.totalAmount != null ? `₱${row.totalAmount}` : '—' }}</td>
                </tr>
                <tr v-if="liveFeedPreview.length === 0">
                  <td colspan="3" class="py-10 text-center text-surface-500 text-sm">No feed rows yet — run <code class="text-surface-400">machine_live_feed.sql</code> and insert from the machine.</td>
                </tr>
              </tbody>
              <tfoot v-if="!isCompactUi && liveFeedPreview.length > 0" class="sticky bottom-0 bg-surface-950/95 light:bg-surface-100/95 border-t border-surface-800/40">
                <tr>
                  <td colspan="3" class="py-2.5 pr-3 pl-0">
                    <span class="text-xs font-bold text-surface-300">Total</span>
                    <span class="text-xs text-surface-500 ml-2">{{ liveFeedPreviewTotals.count }} row(s)</span>
                  </td>
                  <td class="py-2.5 pr-3 text-right text-surface-200 text-xs font-bold whitespace-nowrap">{{ liveFeedPreviewTotals.totalQty }}</td>
                  <td class="py-2.5 text-surface-400 text-xs whitespace-nowrap">
                    Yes: <span class="text-surface-200 font-semibold">{{ liveFeedPreviewTotals.irYes }}</span>
                  </td>
                  <td class="py-2.5 text-right text-surface-200 text-xs font-bold whitespace-nowrap">₱{{ liveFeedPreviewTotals.totalAmount }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- Calendar (Manila dates) + sales for selected day -->
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
          <div class="ios-card rounded-2xl p-5 sm:p-6">
            <div class="flex items-center justify-between gap-3 mb-4">
              <h3 class="text-sm font-bold text-surface-200">Sales calendar</h3>
              <div class="flex items-center gap-2">
                <button type="button" class="p-2 rounded-lg text-surface-400 hover:bg-surface-800/50 hover:text-surface-200 transition-colors" @click="calendarPrevMonth" aria-label="Previous month">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
                </button>
                <span class="text-xs font-semibold text-surface-300 min-w-0 sm:min-w-[8.5rem] text-center">{{ calendarTitle }}</span>
                <button type="button" class="p-2 rounded-lg text-surface-400 hover:bg-surface-800/50 hover:text-surface-200 transition-colors" @click="calendarNextMonth" aria-label="Next month">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
                </button>
              </div>
            </div>
            <p class="text-xs text-surface-500 mb-3">Dates use <strong class="text-surface-400">Asia/Manila</strong>. Click a day to list sales.</p>
            <div class="grid grid-cols-7 gap-1 text-center text-[10px] uppercase tracking-wider text-surface-500 mb-2">
              <span>Su</span><span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span>
            </div>
            <div class="grid grid-cols-7 gap-1">
              <button
                v-for="(cell, idx) in calendarCells"
                :key="idx"
                type="button"
                :disabled="!cell.ymd"
                @click="cell.ymd && selectCalendarDay(cell.ymd)"
                class="aspect-square rounded-xl text-xs font-medium transition-all disabled:opacity-0 disabled:pointer-events-none"
                :class="cell.ymd === selectedYmd
                  ? 'bg-brand-600 text-white shadow-lg shadow-brand-900/30'
                  : cell.isToday
                    ? 'border border-brand-500/40 text-brand-300 hover:bg-surface-800/40'
                    : 'text-surface-300 hover:bg-surface-800/40'"
              >
                {{ cell.day }}
              </button>
            </div>
            <p class="text-xs text-surface-500 mt-4">
              <template v-if="selectedYmd">
                Selected: <span class="text-surface-200 font-semibold">{{ selectedYmd }}</span>
                · Total: <span class="text-emerald-400 font-bold">₱{{ selectedDayTotal.toFixed(2) }}</span>
                · {{ salesForSelectedDay.length }} sale(s)
              </template>
              <template v-else>
                Select a date to view transaction history.
              </template>
            </p>
          </div>

          <div class="ios-card rounded-2xl p-5 sm:p-6">
            <h3 class="text-sm font-bold text-surface-200 light:text-surface-900 mb-1">Sales on selected date</h3>
            <p class="text-xs text-surface-500 light:text-surface-600 mb-4">From synced machine transactions (same timezone as calendar).</p>
            <div class="overflow-x-auto max-h-72 overflow-y-auto">
              <table class="w-full text-sm">
                <thead class="sticky top-0 z-10 border-b border-surface-800/40 light:border-surface-200/80 bg-surface-950/95 light:bg-surface-200/95 backdrop-blur">
                  <tr>
                    <th class="text-left text-xs text-surface-200 light:text-surface-800 uppercase tracking-wider pb-2 pr-3 font-semibold">Item</th>
                    <th class="text-left text-xs text-surface-200 light:text-surface-800 uppercase tracking-wider pb-2 pr-3 font-semibold">Time (PH)</th>
                    <th class="text-right text-xs text-surface-200 light:text-surface-800 uppercase tracking-wider pb-2 pr-3 font-semibold">Qty</th>
                    <th class="text-right text-xs text-surface-200 light:text-surface-800 uppercase tracking-wider pb-2 font-semibold">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in salesForSelectedDayRows" :key="row.key" class="border-b border-surface-800/20 last:border-0">
                    <td class="py-2.5 pr-3 text-surface-200">{{ row.item }}</td>
                    <td class="py-2.5 pr-3 text-surface-500 text-xs whitespace-nowrap">{{ row.timePh }}</td>
                    <td class="py-2.5 pr-3 text-right text-surface-300 text-xs whitespace-nowrap">{{ row.qty }}</td>
                    <td class="py-2.5 text-right font-semibold text-emerald-400">₱{{ row.amount }}</td>
                  </tr>
                  <tr v-if="salesForSelectedDayRows.length === 0">
                    <td colspan="4" class="py-8 text-center text-surface-500 text-sm">
                      {{ selectedYmd ? 'No sales for this day in the loaded history.' : 'Select a date on the calendar.' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="ios-card rounded-2xl p-5 sm:p-6 mb-6">
          <h3 class="text-sm font-bold text-surface-200 light:text-surface-900 mb-1">Machine events on selected date</h3>
          <p class="text-xs text-surface-500 light:text-surface-600 mb-4">Filtered from <code class="text-surface-400">live_feed</code> using the calendar date.</p>
          <div class="overflow-x-auto max-h-72 overflow-y-auto rounded-xl border border-surface-800/30">
            <table class="w-full text-sm">
              <thead class="sticky top-0 bg-surface-950/95 light:bg-surface-100/95 z-10 border-b border-surface-800/40">
                <tr>
                  <th class="text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold">Time (PH)</th>
                  <th class="text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold">Type</th>
                  <th class="text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold">Message</th>
                  <th class="hidden sm:table-cell text-right text-xs text-surface-400 uppercase py-3 px-4 font-semibold whitespace-nowrap">Quantity</th>
                  <th class="hidden sm:table-cell text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold whitespace-nowrap">IR - Beam Sensed</th>
                  <th class="hidden sm:table-cell text-right text-xs text-surface-400 uppercase py-3 px-4 font-semibold whitespace-nowrap">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in liveFeedForSelectedDayRows" :key="row.key" class="border-b border-surface-800/20">
                  <td class="py-3 px-4 text-surface-500 text-xs whitespace-nowrap">{{ row.time }}</td>
                  <td class="py-3 px-4 text-brand-400 text-xs font-medium">{{ row.type }}</td>
                  <td class="py-3 px-4 text-surface-200">{{ row.message }}</td>
                  <td class="hidden sm:table-cell py-3 px-4 text-right text-surface-300 text-xs whitespace-nowrap">{{ row.quantity }}</td>
                  <td class="hidden sm:table-cell py-3 px-4 text-surface-300 text-xs whitespace-nowrap">{{ row.irBeamSensed }}</td>
                  <td class="hidden sm:table-cell py-3 px-4 text-right text-surface-300 text-xs whitespace-nowrap">{{ row.totalAmount != null ? `₱${row.totalAmount}` : '—' }}</td>
                </tr>
                <tr v-if="liveFeedForSelectedDayRows.length === 0">
                  <td colspan="6" class="py-10 text-center text-surface-500 text-sm">
                    {{ selectedYmd ? 'No machine events for this day.' : 'Select a date on the calendar.' }}
                  </td>
                </tr>
              </tbody>
              <tfoot v-if="liveFeedForSelectedDayRows.length > 0" class="sticky bottom-0 bg-surface-950/95 light:bg-surface-100/95 border-t border-surface-800/40">
                <tr>
                  <td colspan="3" class="py-3 px-4">
                    <span class="text-xs font-bold text-surface-300">Total</span>
                    <span class="text-xs text-surface-500 ml-2">{{ liveFeedForSelectedDayTotals.count }} row(s)</span>
                  </td>
                  <td class="hidden sm:table-cell py-3 px-4 text-right text-surface-200 text-xs font-bold whitespace-nowrap">{{ liveFeedForSelectedDayTotals.totalQty }}</td>
                  <td class="hidden sm:table-cell py-3 px-4 text-surface-400 text-xs whitespace-nowrap">
                    Yes: <span class="text-surface-200 font-semibold">{{ liveFeedForSelectedDayTotals.irYes }}</span>
                  </td>
                  <td class="hidden sm:table-cell py-3 px-4 text-right text-surface-200 text-xs font-bold whitespace-nowrap">₱{{ liveFeedForSelectedDayTotals.totalAmount }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- Email signups (Supabase `emails` table) -->
        <div class="ios-card rounded-2xl p-5 sm:p-6 mb-6">
          <div class="flex items-start justify-between gap-3 mb-3">
            <div>
              <h3 class="text-sm font-bold text-surface-200 light:text-surface-900 mb-1">Newsletter &amp; contact emails</h3>
              <p class="text-xs text-surface-500">Passwords are masked. Click a password to copy its SHA-256 hash.</p>
            </div>
            <transition name="text-fade">
              <span v-if="passHashToast" class="text-xs px-3 py-1.5 rounded-xl bg-surface-800/30 border border-surface-700/40 text-surface-300 whitespace-nowrap">
                {{ passHashToast }}
              </span>
            </transition>
          </div>
          <div class="overflow-x-auto max-h-64 overflow-y-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-surface-800/40 light:border-surface-200/80">
                  <th class="text-left text-xs text-surface-400 light:text-surface-600 uppercase tracking-wider pb-3 pr-4 font-semibold">Email</th>
                  <th class="text-left text-xs text-surface-400 light:text-surface-600 uppercase tracking-wider pb-3 pr-4 font-semibold">Password</th>
                  <th class="text-left text-xs text-surface-400 light:text-surface-600 uppercase tracking-wider pb-3 font-semibold">Signed up (PH)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in subscriberEmailRows" :key="row.id" class="border-b border-surface-800/20 last:border-0 light:border-surface-200/60">
                  <td class="py-3 pr-4 text-surface-200 light:text-surface-900">{{ row.email }}</td>
                  <td class="py-3 pr-4">
                    <button
                      type="button"
                      class="font-mono text-xs text-surface-300 light:text-surface-800 hover:text-surface-100 transition-colors underline decoration-surface-700/60 underline-offset-4"
                      :disabled="!row.passwordRaw"
                      @click="copyPasswordHash(row.passwordRaw)"
                      :title="row.passwordRaw ? 'Copy SHA-256 hash to clipboard' : 'No password saved'"
                    >
                      {{ row.passwordRaw ? '********' : '—' }}
                    </button>
                  </td>
                  <td class="py-3 text-surface-400 light:text-surface-700 text-xs">{{ row.createdPh }}</td>
                </tr>
                <tr v-if="subscriberEmailRows.length === 0">
                  <td colspan="3" class="py-8 text-center text-surface-500 text-sm">No rows yet — create the table and submit the homepage signup form.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Sales Trend Chart -->
        <div class="ios-card rounded-2xl p-5 sm:p-6 mb-6">
          <div class="flex items-start justify-between gap-3 mb-1">
            <div>
              <h3 class="text-sm font-bold text-surface-200 mb-0.5">Sales by Created Date</h3>
              <p class="text-xs text-surface-500">Realtime synced from transactions</p>
            </div>
            <div class="flex items-center gap-1.5">
              <button
                v-for="opt in salesRangeOptions"
                :key="opt.id"
                type="button"
                class="px-2.5 py-1.5 rounded-lg text-[11px] font-bold transition-colors border"
                :class="salesTrendRange === opt.id
                  ? 'bg-brand-600 text-white border-brand-500/30 shadow-lg shadow-brand-900/25'
                  : 'bg-surface-900/30 text-surface-400 border-surface-800/40 hover:text-surface-200 hover:bg-surface-800/30'"
                @click="salesTrendRange = opt.id"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>
          <div class="w-full h-56 sm:h-72">
            <canvas ref="salesTrendChart"></canvas>
          </div>
        </div>

        <!-- Monthly Sales Chart -->
        <div class="ios-card rounded-2xl p-5 sm:p-6 mb-6">
          <div class="flex items-start justify-between gap-3 mb-1">
            <div>
              <h3 class="text-sm font-bold text-surface-200 mb-0.5">Monthly Sales</h3>
              <p class="text-xs text-surface-500">Realtime synced from transactions</p>
            </div>
            <div class="flex items-center gap-1.5">
              <button
                v-for="opt in monthlyRangeOptions"
                :key="opt.id"
                type="button"
                class="px-2.5 py-1.5 rounded-lg text-[11px] font-bold transition-colors border"
                :class="monthlyRange === opt.id
                  ? 'bg-brand-600 text-white border-brand-500/30 shadow-lg shadow-brand-900/25'
                  : 'bg-surface-900/30 text-surface-400 border-surface-800/40 hover:text-surface-200 hover:bg-surface-800/30'"
                @click="monthlyRange = opt.id"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>
          <div class="w-full h-52 sm:h-64">
            <canvas ref="monthlySalesChart"></canvas>
          </div>
        </div>

        <!-- Two columns: Top Products + Low Stock -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <!-- Top Selling Products -->
          <div class="ios-card rounded-2xl p-5 sm:p-6">
            <h3 class="text-sm font-bold text-surface-200 mb-0.5">Top-selling Products</h3>
            <p class="text-xs text-surface-500 mb-4">Bars extend to the right · realtime synced</p>
            <div class="w-full h-52 sm:h-64">
              <canvas ref="topProductsChart"></canvas>
            </div>
          </div>

          <!-- Low Stock Inventory -->
          <div class="ios-card rounded-2xl p-5 sm:p-6">
            <h3 class="text-sm font-bold text-surface-200 mb-0.5">Low-stock Products</h3>
            <p class="text-xs text-surface-500 mb-4">Current stock vs capacity</p>
            <div class="mt-2 overflow-x-auto rounded-xl border border-surface-800/30">
              <table class="w-full text-sm">
                <thead class="bg-surface-950/60 light:bg-surface-100/80 border-b border-surface-800/40">
                  <tr>
                    <th class="text-left text-[11px] text-surface-400 uppercase tracking-wider py-3 px-3 font-semibold whitespace-nowrap">Slot#</th>
                    <th class="text-left text-[11px] text-surface-400 uppercase tracking-wider py-3 px-3 font-semibold">Product</th>
                    <th class="text-right text-[11px] text-surface-400 uppercase tracking-wider py-3 px-3 font-semibold whitespace-nowrap">Price</th>
                    <th class="hidden sm:table-cell text-right text-[11px] text-surface-400 uppercase tracking-wider py-3 px-3 font-semibold whitespace-nowrap">Ratio</th>
                    <th class="hidden sm:table-cell text-left text-[11px] text-surface-400 uppercase tracking-wider py-3 px-3 font-semibold whitespace-nowrap">Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in lowStockTableRows"
                    :key="row.key"
                    class="border-b border-surface-800/20 last:border-0"
                  >
                    <td class="py-2.5 px-3 text-surface-300 font-mono text-xs whitespace-nowrap">{{ row.slot }}</td>
                    <td class="py-2.5 px-3 text-surface-200 font-medium truncate max-w-[14rem]">{{ row.product }}</td>
                    <td class="py-2.5 px-3 text-right text-surface-300 whitespace-nowrap">₱{{ row.price }}</td>
                    <td class="hidden sm:table-cell py-2.5 px-3 text-right text-surface-400 font-semibold whitespace-nowrap">{{ row.ratio }}</td>
                    <td class="hidden sm:table-cell py-2.5 px-3">
                      <span class="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold border"
                        :class="row.statusClass"
                      >
                        {{ row.status }}
                      </span>
                    </td>
                  </tr>
                  <tr v-if="lowStockTableRows.length === 0">
                    <td colspan="5" class="py-10 text-center text-surface-500 text-sm">
                      No low-stock products right now.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Recent Transactions -->
        <div class="ios-card rounded-2xl p-5 sm:p-6">
          <h3 class="text-sm font-bold text-surface-200 mb-4">Recent Transactions</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-surface-800/40">
                  <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3 pr-4">Item</th>
                  <th class="hidden sm:table-cell text-left text-xs text-surface-500 uppercase tracking-wider pb-3 pr-4">Time</th>
                  <th class="text-right text-xs text-surface-500 uppercase tracking-wider pb-3">Amount</th>
                </tr>
              </thead>
              <tbody>
                <template v-if="recentTransactions.length === 0">
                  <tr>
                    <td colspan="3" class="py-10 text-center text-surface-500 text-sm">No transactions yet — purchases appear when the machine inserts into <code class="text-surface-400">transactions</code>.</td>
                  </tr>
                </template>
                <template v-else>
                  <tr v-for="tx in recentTransactions" :key="tx.id ?? tx.time" class="border-b border-surface-800/20 last:border-0">
                    <td class="py-3 pr-4 text-surface-200">{{ tx.item }}</td>
                    <td class="hidden sm:table-cell py-3 pr-4 text-surface-500 text-xs">{{ tx.time }}</td>
                    <td class="py-3 text-right font-semibold text-emerald-400">₱{{ tx.amount }}</td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- LIVE FEED (full list) -->
      <div v-else-if="activeSection === 'machine-feed'">
        <div class="ios-card rounded-2xl p-5 sm:p-6">
          <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-4">
            <div>
              <h3 class="text-lg font-bold text-surface-100 light:text-surface-900 mb-1">Machine live feed</h3>
              <p class="text-sm text-surface-500">Realtime stream from <code class="text-surface-400">public.live_feed</code>.</p>
            </div>
          </div>

          <!-- Calendar-like filter (same behavior as Sales Calendar) -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div class="rounded-2xl border border-surface-800/30 light:border-surface-200/80 bg-surface-900/20 light:bg-white/85 p-4">
              <div class="flex items-center justify-between gap-3 mb-3">
                <p class="text-xs font-bold text-surface-300 light:text-surface-800 uppercase tracking-wider">Filter by date (PH)</p>
                <div class="flex items-center gap-2">
                  <button type="button" class="p-2 rounded-lg text-surface-400 hover:bg-surface-800/50 hover:text-surface-200 transition-colors" @click="feedCalendarPrevMonth" aria-label="Previous month">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
                  </button>
                  <span class="text-xs font-semibold text-surface-300 light:text-surface-800 min-w-0 sm:min-w-[8.5rem] text-center">{{ feedCalendarTitle }}</span>
                  <button type="button" class="p-2 rounded-lg text-surface-400 hover:bg-surface-800/50 hover:text-surface-200 transition-colors" @click="feedCalendarNextMonth" aria-label="Next month">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
                  </button>
                </div>
              </div>

              <div class="grid grid-cols-7 gap-1 text-center text-[10px] uppercase tracking-wider text-surface-500 light:text-surface-600 mb-2">
                <span>Su</span><span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span>
              </div>
              <div class="grid grid-cols-7 gap-1">
                <button
                  v-for="(cell, idx) in feedCalendarCells"
                  :key="idx"
                  type="button"
                  :disabled="!cell.ymd"
                  @click="cell.ymd && selectFeedCalendarDay(cell.ymd)"
                  class="aspect-square rounded-xl text-xs font-medium transition-all disabled:opacity-0 disabled:pointer-events-none"
                  :class="cell.ymd === feedSelectedYmd
                    ? 'bg-brand-600 text-white shadow-lg shadow-brand-900/30'
                    : cell.isToday
                      ? 'border border-brand-500/40 text-brand-300 hover:bg-surface-800/40'
                      : 'text-surface-300 light:text-surface-800 hover:bg-surface-800/40 light:hover:bg-surface-200/70'"
                >
                  {{ cell.day }}
                </button>
              </div>

              <p class="text-xs text-surface-500 light:text-surface-600 mt-3">
                <template v-if="feedSelectedYmd">
                  Selected: <span class="text-surface-200 font-semibold">{{ feedSelectedYmd }}</span>
                  · {{ liveFeedRowsForSelectedDay.length }} event(s)
                </template>
                <template v-else>
                  Select a date to view machine events.
                </template>
              </p>
            </div>

            <div class="rounded-2xl border border-surface-800/30 light:border-surface-200/80 bg-surface-900/20 light:bg-white/85 p-4">
              <p class="text-xs font-bold text-surface-300 light:text-surface-800 uppercase tracking-wider mb-2">Quick actions</p>
              <div class="flex flex-wrap gap-2">
                <button
                  type="button"
                  class="px-3 py-2 rounded-xl text-xs font-bold transition-colors border bg-surface-900/30 light:bg-surface-100 text-surface-300 light:text-surface-800 border-surface-800/40 light:border-surface-200 hover:bg-surface-800/30 light:hover:bg-surface-200/70"
                  @click="clearFeedSelection"
                >
                  Clear selection
                </button>
              </div>

              <div v-if="feedSelectedYmd" class="mt-4 space-y-3">
                <div class="rounded-xl border border-surface-800/30 light:border-surface-200/80 bg-surface-950/40 light:bg-surface-100/80 px-3 py-2.5">
                  <p class="text-[11px] uppercase tracking-wider text-surface-500 light:text-surface-600 font-bold">Selected date</p>
                  <p class="text-sm font-bold text-surface-100 light:text-surface-900 mt-1">{{ feedSelectedYmd }}</p>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <div class="rounded-xl border border-surface-800/30 light:border-surface-200/80 bg-surface-950/40 light:bg-surface-100/80 px-3 py-2.5">
                    <p class="text-[10px] uppercase tracking-wider text-surface-500 light:text-surface-600 font-bold">Events</p>
                    <p class="text-base font-extrabold text-surface-100 light:text-surface-900 tabular-nums mt-1">{{ liveFeedSelectedTotals.count }}</p>
                  </div>
                  <div class="rounded-xl border border-surface-800/30 light:border-surface-200/80 bg-surface-950/40 light:bg-surface-100/80 px-3 py-2.5">
                    <p class="text-[10px] uppercase tracking-wider text-surface-500 light:text-surface-600 font-bold">Qty</p>
                    <p class="text-base font-extrabold text-surface-100 light:text-surface-900 tabular-nums mt-1">{{ liveFeedSelectedTotals.totalQty }}</p>
                  </div>
                  <div class="rounded-xl border border-surface-800/30 light:border-surface-200/80 bg-surface-950/40 light:bg-surface-100/80 px-3 py-2.5">
                    <p class="text-[10px] uppercase tracking-wider text-surface-500 light:text-surface-600 font-bold">IR Yes</p>
                    <p class="text-base font-extrabold text-surface-100 light:text-surface-900 tabular-nums mt-1">{{ liveFeedSelectedTotals.irYes }}</p>
                  </div>
                  <div class="rounded-xl border border-surface-800/30 light:border-surface-200/80 bg-surface-950/40 light:bg-surface-100/80 px-3 py-2.5">
                    <p class="text-[10px] uppercase tracking-wider text-surface-500 light:text-surface-600 font-bold">Total</p>
                    <p class="text-base font-extrabold text-emerald-400 tabular-nums mt-1">₱{{ liveFeedSelectedTotals.totalAmount }}</p>
                  </div>
                </div>

                <div v-if="liveFeedRowsForSelectedDay.length" class="rounded-xl border border-surface-800/30 light:border-surface-200/80 bg-surface-950/40 light:bg-surface-100/80 px-3 py-2.5">
                  <p class="text-[11px] uppercase tracking-wider text-surface-500 light:text-surface-600 font-bold mb-1">Latest event</p>
                  <p class="text-xs text-surface-300 light:text-surface-700 line-clamp-2">
                    {{ liveFeedRowsForSelectedDay[0]?.message || '—' }}
                  </p>
                </div>
              </div>

              <p v-else class="text-xs text-surface-500 light:text-surface-600 mt-3">
                This view shows <span class="text-surface-300 font-semibold">no history</span> until you pick a date, same as the Sales Calendar.
              </p>
            </div>
          </div>

          <div class="overflow-x-auto max-h-[70vh] overflow-y-auto rounded-xl border border-surface-800/30">
            <table class="w-full text-sm">
              <thead class="sticky top-0 bg-surface-950/95 light:bg-surface-100/95 z-10 border-b border-surface-800/40">
                <tr>
                  <th class="text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold">Time (PH)</th>
                  <th class="text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold">Type</th>
                  <th class="text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold">Message</th>
                  <th class="hidden sm:table-cell text-right text-xs text-surface-400 uppercase py-3 px-4 font-semibold whitespace-nowrap">Quantity</th>
                  <th class="hidden sm:table-cell text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold whitespace-nowrap">IR - Beam Sensed</th>
                  <th class="hidden sm:table-cell text-right text-xs text-surface-400 uppercase py-3 px-4 font-semibold whitespace-nowrap">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in liveFeedRowsForSelectedDay" :key="row.id" class="border-b border-surface-800/20">
                  <td class="py-3 px-4 text-surface-500 text-xs whitespace-nowrap">{{ row.time }}</td>
                  <td class="py-3 px-4 text-brand-400 text-xs font-medium">{{ row.type }}</td>
                  <td class="py-3 px-4 text-surface-200">{{ row.message }}</td>
                  <td class="hidden sm:table-cell py-3 px-4 text-right text-surface-300 text-xs whitespace-nowrap">{{ row.quantity ?? '—' }}</td>
                  <td class="hidden sm:table-cell py-3 px-4 text-surface-300 text-xs whitespace-nowrap">{{ row.irBeamSensed ?? '—' }}</td>
                  <td class="hidden sm:table-cell py-3 px-4 text-right text-surface-300 text-xs whitespace-nowrap">{{ row.totalAmount != null ? `₱${row.totalAmount}` : '—' }}</td>
                </tr>
                <tr v-if="liveFeedRowsForSelectedDay.length === 0">
                  <td colspan="6" class="py-16 text-center text-surface-500">
                    {{ feedSelectedYmd ? 'No machine events for this day.' : 'Select a date on the calendar to view history.' }}
                  </td>
                </tr>
              </tbody>
              <tfoot v-if="liveFeedRowsForSelectedDay.length > 0" class="sticky bottom-0 bg-surface-950/95 light:bg-surface-100/95 border-t border-surface-800/40">
                <tr>
                  <td colspan="3" class="py-3 px-4">
                    <span class="text-xs font-bold text-surface-300">Total</span>
                    <span class="text-xs text-surface-500 ml-2">{{ liveFeedSelectedTotals.count }} row(s)</span>
                  </td>
                  <td class="hidden sm:table-cell py-3 px-4 text-right text-surface-200 text-xs font-bold whitespace-nowrap">{{ liveFeedSelectedTotals.totalQty }}</td>
                  <td class="hidden sm:table-cell py-3 px-4 text-surface-400 text-xs whitespace-nowrap">
                    Yes: <span class="text-surface-200 font-semibold">{{ liveFeedSelectedTotals.irYes }}</span>
                  </td>
                  <td class="hidden sm:table-cell py-3 px-4 text-right text-surface-200 text-xs font-bold whitespace-nowrap">₱{{ liveFeedSelectedTotals.totalAmount }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      <!-- PREDICTION ANALYSIS SECTION -->
      <div v-else-if="activeSection === 'prediction'">
        <div class="ios-card rounded-2xl p-5 sm:p-6">
          <h3 class="text-sm font-bold text-surface-200 light:text-surface-900 mb-0.5">Prediction Analysis (Demand + Restock)</h3>
          <p class="text-xs text-surface-500 light:text-surface-600 mb-4">
            Loads deep-learning (MLP) forecasts when available and renders charts for quick decisions.
          </p>

          <div class="flex items-center gap-3 mb-4">
            <button
              @click="runPrediction"
              :disabled="predictionRan"
              class="px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-200"
              :class="predictionRan
                ? 'bg-surface-800/40 text-surface-500 cursor-not-allowed'
                : 'bg-emerald-500 text-white hover:bg-emerald-400 active:scale-95'"
            >
              {{ predictionRan ? '✓ Prediction Ready' : 'Run Prediction Analysis' }}
            </button>
            <span v-if="predictionLoading" class="text-xs text-surface-400 light:text-surface-600 animate-pulse">Analyzing...</span>
            <span v-if="predictionModelLabel" class="text-xs text-surface-500 light:text-surface-700">Model: <span class="text-surface-300 light:text-surface-900 font-semibold">{{ predictionModelLabel }}</span></span>
          </div>

          <!-- Charts -->
          <div v-if="predictionResults.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-4">
            <div class="rounded-2xl border border-surface-800/30 light:border-surface-200/80 bg-surface-900/20 light:bg-white/80 p-4 shadow-sm light:shadow-md">
              <p class="text-xs font-bold text-surface-300 light:text-surface-800 mb-2 uppercase tracking-wider">Restock quantity (Top)</p>
              <div class="w-full h-56">
                <canvas ref="predictionRestockChart"></canvas>
              </div>
            </div>
            <div class="rounded-2xl border border-surface-800/30 light:border-surface-200/80 bg-surface-900/20 light:bg-white/80 p-4 shadow-sm light:shadow-md">
              <p class="text-xs font-bold text-surface-300 light:text-surface-800 mb-2 uppercase tracking-wider">Restock split</p>
              <div class="w-full h-56">
                <canvas ref="predictionSplitChart"></canvas>
              </div>
            </div>
          </div>

          <!-- Results Table -->
          <div v-if="predictionResults.length > 0" class="mt-4">
            <p class="text-xs text-surface-500 light:text-surface-600 mb-3">Based on transaction data from the vending machine</p>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-surface-800/40">
                    <th class="text-left text-xs text-surface-500 light:text-surface-600 uppercase tracking-wider pb-3 pr-4">Product</th>
                    <th class="text-left text-xs text-surface-500 light:text-surface-600 uppercase tracking-wider pb-3 pr-4">Predicted Sales Tomorrow</th>
                    <th class="text-left text-xs text-surface-500 light:text-surface-600 uppercase tracking-wider pb-3 pr-4">Current Stock</th>
                    <th class="text-left text-xs text-surface-500 light:text-surface-600 uppercase tracking-wider pb-3">Restock Needed</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="r in predictionResults" :key="r.product_name" class="border-b border-surface-800/20 last:border-0">
                    <td class="py-3 pr-4 text-surface-200 light:text-surface-900 font-medium">{{ r.product_name }}</td>
                    <td class="py-3 pr-4 text-surface-300 light:text-surface-700 tabular-nums">{{ Number(r.predicted_sales_tomorrow ?? 0).toFixed(2) }}</td>
                    <td class="py-3 pr-4 text-surface-300 light:text-surface-700 tabular-nums whitespace-nowrap">{{ r.current_stock }}/{{ r.capacity }}</td>
                    <td class="py-3">
                      <span
                        class="px-2.5 py-1 rounded-lg text-xs font-bold"
                        :class="r.recommended_restock_qty > 0
                          ? 'bg-amber-400/15 text-amber-400'
                          : 'bg-emerald-400/15 text-emerald-400'"
                      >
                        {{ r.recommended_restock_qty > 0 ? `Yes (${r.recommended_restock_qty})` : 'No' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Insights -->
          <div v-if="predictionInsights" class="mt-5 pt-4 border-t border-surface-800/20">
            <h4 class="text-xs font-bold text-surface-300 light:text-surface-800 uppercase tracking-wider mb-3">Insights from Transaction Data</h4>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <!-- Top Products -->
              <div class="p-3 rounded-xl bg-surface-800/20 light:bg-surface-100/90 border border-transparent light:border-surface-200/70">
                <p class="text-xs font-bold text-surface-400 light:text-surface-800 mb-2">🏆 Top Products</p>
                <div v-for="(item, i) in predictionInsights.topProducts.slice(0, 5)" :key="item.name" class="flex justify-between text-xs py-0.5">
                  <span class="text-surface-300 light:text-surface-800">{{ i + 1 }}. {{ item.name }}</span>
                  <span class="text-surface-500 light:text-surface-600 font-medium">{{ item.qty }} sold</span>
                </div>
              </div>
              <!-- Peak Hours -->
              <div class="p-3 rounded-xl bg-surface-800/20 light:bg-surface-100/90 border border-transparent light:border-surface-200/70">
                <p class="text-xs font-bold text-surface-400 light:text-surface-800 mb-2">⏰ Peak Hours</p>
                <div v-for="item in predictionInsights.peakHours.slice(0, 5)" :key="item.hour" class="flex justify-between text-xs py-0.5">
                  <span class="text-surface-300 light:text-surface-800">{{ formatHourAmPm(item.hour) }}</span>
                  <span class="text-surface-500 light:text-surface-600 font-medium">{{ item.qty }} items</span>
                </div>
              </div>
              <!-- Busiest Days -->
              <div class="p-3 rounded-xl bg-surface-800/20 light:bg-surface-100/90 border border-transparent light:border-surface-200/70">
                <p class="text-xs font-bold text-surface-400 light:text-surface-800 mb-2">📅 Busiest Days</p>
                <div v-for="item in predictionInsights.weekdays.slice(0, 5)" :key="item.day" class="flex justify-between text-xs py-0.5">
                  <span class="text-surface-300 light:text-surface-800">{{ item.day }}</span>
                  <span class="text-surface-500 light:text-surface-600 font-medium">{{ item.qty }} items</span>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 mt-4">
              <div class="rounded-2xl border border-surface-800/30 light:border-surface-200/80 bg-surface-900/20 light:bg-white/80 p-4 shadow-sm light:shadow-md">
                <p class="text-xs font-bold text-surface-300 light:text-surface-800 mb-2 uppercase tracking-wider">Peak hours (items)</p>
                <div class="w-full h-52">
                  <canvas ref="predictionPeakHoursChart"></canvas>
                </div>
              </div>
              <div class="rounded-2xl border border-surface-800/30 light:border-surface-200/80 bg-surface-900/20 light:bg-white/80 p-4 shadow-sm light:shadow-md">
                <p class="text-xs font-bold text-surface-300 light:text-surface-800 mb-2 uppercase tracking-wider">Busiest days</p>
                <div class="w-full h-52">
                  <canvas ref="predictionWeekdaysChart"></canvas>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- SALES REPORTS SECTION -->
      <div v-else-if="activeSection === 'sales-reports'">
        <div class="ios-card rounded-2xl p-4 sm:p-6">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-10 h-10 rounded-xl bg-emerald-400/15 flex items-center justify-center">
              <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-bold text-surface-100">Sales Reports</h3>
              <p class="text-xs text-surface-500">Generate reports from realtime machine transactions</p>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div class="rounded-2xl border border-surface-800/30 bg-surface-900/20 p-4">
              <p class="text-xs font-bold uppercase tracking-wider text-surface-400 mb-2">Report source</p>
              <p class="text-sm text-surface-300">
                {{ machine.transactions.length }} transaction row(s) loaded from Supabase realtime.
              </p>
              <p class="text-xs text-surface-500 mt-2">
                Exports include: Date/Time (PH), Product, Quantity, Total Amount, Payment Method, RFID User ID.
              </p>
            </div>

            <div class="rounded-2xl border border-surface-800/30 bg-surface-900/20 p-4">
              <p class="text-xs font-bold uppercase tracking-wider text-surface-400 mb-3">Download format</p>
              <div class="flex flex-wrap gap-2">
                <button
                  type="button"
                  class="px-4 py-2.5 rounded-xl text-sm font-bold bg-emerald-500 text-white hover:bg-emerald-400 transition-colors"
                  @click="downloadSalesReportXlsx"
                >
                  Download .xlsx
                </button>
                <button
                  type="button"
                  class="px-4 py-2.5 rounded-xl text-sm font-bold bg-surface-800/60 text-surface-200 border border-surface-700/40 hover:bg-surface-700/60 transition-colors"
                  @click="downloadSalesReportCsv"
                >
                  Download .csv
                </button>
              </div>
              <p class="text-xs text-surface-500 mt-3">
                For template mode, place <code class="text-surface-400">IC-Annual-Sales-Performance-Report-11538.xlsx</code> inside <code class="text-surface-400">WebSite/public/</code>.
              </p>
            </div>
          </div>

          <p v-if="salesReportMsg" class="text-xs mt-4" :class="salesReportMsgType === 'ok' ? 'text-emerald-400' : 'text-amber-400'">
            {{ salesReportMsg }}
          </p>
        </div>
      </div>

      <!-- REPORTS SECTION -->
      <div v-else-if="activeSection === 'reports'">
        <!-- Reports: default dark styling + light-mode palette overrides (only affects light mode) -->
        <div class="rounded-2xl p-4 sm:p-6 bg-surface-950 text-surface-100 border border-surface-800/40 shadow-sm light:bg-[#F0D8A1] light:text-slate-900 light:border-[#DD9E59]/40">
          <div class="flex items-center gap-3 mb-6">
            <div
              class="w-10 h-10 rounded-xl bg-amber-400/15 flex items-center justify-center border border-transparent light:bg-[#DD9E59]/25 light:border-[#DD9E59]/35"
            >
              <svg class="w-5 h-5 text-amber-300 light:text-[#7A4A1C]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h10M7 11h10M7 15h6M6 3h9l3 3v15a2 2 0 01-2 2H6a2 2 0 01-2-2V5a2 2 0 012-2z" />
              </svg>
            </div>
            <div class="flex-1">
              <h3 class="text-lg font-extrabold text-surface-100 light:!text-slate-900">Reports</h3>
              <p class="text-xs text-surface-500 light:!text-slate-700">Bug reports submitted from the machine (realtime)</p>
            </div>
            <div class="text-right">
              <p class="text-xs text-surface-500 light:!text-slate-700">Total</p>
              <p class="text-sm font-extrabold text-surface-100 light:!text-slate-900">{{ bugReportRows.length }}</p>
            </div>
          </div>

          <div class="flex items-center gap-2 mb-4">
            <button
              type="button"
              class="px-3 py-2 rounded-xl text-xs font-extrabold border shadow-sm transition-colors"
              :class="
                bugReportTab === 'open'
                  ? 'bg-amber-400/20 text-amber-200 border-amber-400/30 hover:bg-amber-400/28 light:bg-[#DD9E59] light:text-white light:border-[#DD9E59]/60 light:hover:bg-[#D08E43]'
                  : 'bg-surface-900/30 text-surface-400 border-surface-800/40 hover:text-surface-200 hover:bg-surface-800/30 light:bg-[#F0D8A1]/70 light:text-slate-900 light:border-[#DD9E59]/35 light:hover:bg-[#F0D8A1]'
              "
              @click="bugReportTab = 'open'"
            >
              Open ({{ bugReportsOpen.length }})
            </button>
            <button
              type="button"
              class="px-3 py-2 rounded-xl text-xs font-extrabold border shadow-sm transition-colors"
              :class="
                bugReportTab === 'fixed'
                  ? 'bg-emerald-400/15 text-emerald-200 border-emerald-400/30 hover:bg-emerald-400/22 light:bg-[#DCF0C3] light:text-slate-900 light:border-[#DCF0C3]/80 light:hover:bg-[#CBE9AA]'
                  : 'bg-surface-900/30 text-surface-400 border-surface-800/40 hover:text-surface-200 hover:bg-surface-800/30 light:bg-[#F0D8A1]/70 light:text-slate-900 light:border-[#DD9E59]/35 light:hover:bg-[#F0D8A1]'
              "
              @click="bugReportTab = 'fixed'"
            >
              Fixed ({{ bugReportsFixed.length }})
            </button>
          </div>

          <div
            class="overflow-x-auto max-h-[60vh] overflow-y-auto rounded-xl border border-surface-800/30 bg-surface-950/40 shadow-sm light:border-[#DD9E59]/35 light:bg-white/60"
          >
            <table class="w-full text-sm">
              <thead class="sticky top-0 bg-surface-950/95 light:bg-[#DD9E59] z-10 border-b border-surface-800/40 light:border-[#DD9E59]/70">
                <tr>
                  <th class="text-left text-xs text-surface-400 light:text-white uppercase py-3 px-4 font-bold whitespace-nowrap">Time (PH)</th>
                  <th class="hidden sm:table-cell text-left text-xs text-surface-400 light:text-white uppercase py-3 px-4 font-bold whitespace-nowrap">Machine</th>
                  <th class="text-left text-xs text-surface-400 light:text-white uppercase py-3 px-4 font-bold whitespace-nowrap">Category</th>
                  <th class="text-left text-xs text-surface-400 light:text-white uppercase py-3 px-4 font-bold">Details</th>
                  <th class="hidden md:table-cell text-left text-xs text-surface-400 light:text-white uppercase py-3 px-4 font-bold whitespace-nowrap">Version</th>
                  <th class="hidden md:table-cell text-left text-xs text-surface-400 light:text-white uppercase py-3 px-4 font-bold whitespace-nowrap">Theme</th>
                  <th class="text-right text-xs text-surface-400 light:text-white uppercase py-3 px-4 font-bold whitespace-nowrap">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="r in (bugReportTab === 'fixed' ? bugReportsFixed : bugReportsOpen)"
                  :key="r.id"
                  class="border-b border-surface-800/20 hover:bg-surface-900/25 transition-colors light:border-[#DD9E59]/25 light:hover:bg-[#F0D8A1]/45"
                >
                  <td class="py-3 px-4 text-surface-500 light:text-slate-700 text-xs whitespace-nowrap">{{ r.timePh }}</td>
                  <td class="hidden sm:table-cell py-3 px-4 text-surface-200 light:text-slate-900 text-xs whitespace-nowrap">{{ r.machineId }}</td>
                  <td class="py-3 px-4 text-amber-300 light:text-[#7A4A1C] text-xs font-extrabold whitespace-nowrap">{{ r.category }}</td>
                  <td class="py-3 px-4 text-surface-200 light:text-slate-900 text-xs whitespace-pre-wrap">{{ r.details }}</td>
                  <td class="hidden md:table-cell py-3 px-4 text-surface-300 light:text-slate-800 text-xs whitespace-nowrap">{{ r.version }}</td>
                  <td class="hidden md:table-cell py-3 px-4 text-surface-300 light:text-slate-800 text-xs whitespace-nowrap">{{ r.theme }}</td>
                  <td class="py-3 px-4 text-right whitespace-nowrap">
                    <button
                      v-if="r.status !== 'fixed'"
                      type="button"
                      class="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-500/15 text-emerald-200 border border-emerald-500/20 hover:bg-emerald-500/25 transition-colors light:bg-[#DCF0C3] light:text-slate-900 light:border-[#DCF0C3]/80 light:hover:bg-[#CBE9AA]"
                      @click="openFixModal(r)"
                    >
                      Fix
                    </button>
                    <span v-else class="text-xs text-surface-500 light:text-slate-700">
                      Fixed
                    </span>
                  </td>
                </tr>
                <tr v-if="(bugReportTab === 'fixed' ? bugReportsFixed.length : bugReportsOpen.length) === 0">
                  <td colspan="7" class="py-10 text-center text-surface-500 light:text-slate-700 text-sm">No reports yet.</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Fix modal -->
          <div v-if="fixingReport" class="fixed inset-0 z-[90]">
            <div class="absolute inset-0 bg-black/30 dark:bg-surface-950/70 backdrop-blur-sm" @click="closeFixModal" />
            <div class="absolute left-0 right-0 top-24 px-4">
              <div class="mx-auto max-w-lg rounded-2xl border border-surface-200/80 dark:border-surface-800/50 bg-white/95 dark:bg-surface-950/95 p-5 shadow-2xl">
                <h4 class="text-sm font-extrabold text-surface-950 dark:text-surface-100">Mark as fixed</h4>
                <p class="text-xs text-surface-700 dark:text-surface-400 mt-1">
                  Category: <span class="text-surface-950 dark:text-surface-200 font-semibold">{{ fixingReport.category }}</span>
                </p>
                <p class="text-xs text-surface-700 dark:text-surface-400 mt-1">
                  Details: <span class="text-surface-950 dark:text-surface-200">{{ fixingReport.details }}</span>
                </p>

                <label class="mt-4 flex items-center gap-2 text-xs text-surface-900 dark:text-surface-200">
                  <input type="checkbox" v-model="fixConfirmed" class="accent-emerald-500" />
                  I confirm this issue is fixed.
                </label>

                <p v-if="fixMsg" class="text-xs text-red-400 mt-2">{{ fixMsg }}</p>

                <div class="mt-5 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    class="px-4 py-2 rounded-xl text-xs font-bold bg-surface-100 text-surface-900 border border-surface-200 hover:bg-surface-200 dark:bg-surface-800/50 dark:text-surface-200 dark:border-surface-700/40 dark:hover:bg-surface-700/60 transition-colors"
                    @click="closeFixModal"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    class="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-500 text-white hover:bg-emerald-400 disabled:opacity-60 disabled:cursor-not-allowed"
                    :disabled="!fixConfirmed || fixBusy"
                    @click="confirmFix"
                  >
                    {{ fixBusy ? 'Fixing…' : 'Confirm fix' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- USER MANAGEMENT SECTION -->
      <div v-else-if="activeSection === 'users'">
        <div class="ios-card rounded-2xl p-4 sm:p-6">
          <p class="text-xs text-surface-500 mb-4 max-w-xl">
            <strong class="text-surface-400">Remove</strong> deletes the saved login on this browser and removes the matching row in Supabase <code class="text-surface-400">emails</code>. Deleting a row only in the Supabase Table Editor does not sign the user out or remove credentials from localStorage.
          </p>
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-lg font-bold text-surface-100">User Management</h3>
            <button
              v-if="isAdmin"
              @click="showUserForm = !showUserForm"
              class="px-4 py-2 rounded-xl text-xs font-bold bg-brand-700 text-white hover:bg-brand-600 transition-colors"
            >
              {{ showUserForm ? 'Cancel' : '+ Add User' }}
            </button>
          </div>

          <!-- Create User Form -->
          <transition name="text-fade">
            <form v-if="showUserForm" @submit.prevent="handleCreateUser" class="ios-card rounded-xl p-5 mb-6 space-y-4">
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label class="block text-xs text-surface-500 uppercase tracking-wider mb-1">Email (@tup.edu.ph)</label>
                  <input v-model="newUser.username" type="email" inputmode="email" autocomplete="email" required placeholder="name@tup.edu.ph"
                    class="w-full px-3 py-2.5 rounded-xl bg-surface-800/40 border border-surface-700/40 text-surface-100 text-sm focus:border-brand-600 focus:outline-none transition-colors" />
                </div>
                <div>
                  <label class="block text-xs text-surface-500 uppercase tracking-wider mb-1">Password</label>
                  <input v-model="newUser.password" type="password" required
                    class="w-full px-3 py-2.5 rounded-xl bg-surface-800/40 border border-surface-700/40 text-surface-100 text-sm focus:border-brand-600 focus:outline-none transition-colors" />
                </div>
                <div>
                  <label class="block text-xs text-surface-500 uppercase tracking-wider mb-1">Role</label>
                  <select v-model="newUser.role"
                    class="w-full px-3 py-2.5 rounded-xl bg-surface-800/40 border border-surface-700/40 text-surface-100 text-sm focus:border-brand-600 focus:outline-none transition-colors">
                    <option value="admin">Admin</option>
                    <option value="staff">Staff</option>
                  </select>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <button type="submit" class="px-5 py-2 rounded-xl text-sm font-bold bg-emerald-500 text-white hover:bg-emerald-400 transition-colors">
                  Create Account
                </button>
                <span v-if="userMsg" class="text-xs" :class="userMsgType === 'success' ? 'text-emerald-400' : 'text-red-400'">{{ userMsg }}</span>
              </div>
            </form>
          </transition>

          <!-- Users List -->
          <div class="space-y-2">
            <div
              v-for="user in allUsers"
              :key="user.username"
              class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-xl bg-surface-800/20 border border-surface-800/20"
            >
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-brand-700/20 flex items-center justify-center text-sm font-bold text-brand-400">
                  {{ user.username[0].toUpperCase() }}
                </div>
                <div>
                  <p class="text-sm font-medium text-surface-200">{{ user.username }}</p>
                  <p class="text-xs text-surface-500 capitalize">{{ user.role }}</p>
                </div>
              </div>
              <button
                v-if="isAdmin"
                @click="handleDeleteUser(user.username)"
                class="text-xs text-red-400 hover:text-red-300 transition-colors px-3 py-1.5 rounded-lg hover:bg-red-400/10"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- CHANGE CREDENTIALS SECTION -->
      <div v-else-if="activeSection === 'credentials'">
        <div class="ios-card rounded-2xl p-4 sm:p-6">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-10 h-10 rounded-xl bg-brand-600/15 flex items-center justify-center">
              <svg class="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-bold text-surface-100">Change Credentials</h3>
              <p class="text-xs text-surface-500">Updates website login and Supabase <code class="text-surface-400">emails</code> password.</p>
            </div>
          </div>

          <form @submit.prevent="handleChangeCredentials" class="max-w-xl space-y-4">
            <div>
              <label class="block text-xs text-surface-500 uppercase tracking-wider mb-1">Current account</label>
              <input
                :value="currentUser?.username || ''"
                disabled
                class="w-full px-3 py-2.5 rounded-xl bg-surface-800/30 border border-surface-700/30 text-surface-300 text-sm"
              />
            </div>
            <div>
              <label class="block text-xs text-surface-500 uppercase tracking-wider mb-1">New password</label>
              <input
                v-model="credentialForm.password"
                type="password"
                required
                minlength="4"
                class="w-full px-3 py-2.5 rounded-xl bg-surface-800/40 border border-surface-700/40 text-surface-100 text-sm focus:border-brand-600 focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label class="block text-xs text-surface-500 uppercase tracking-wider mb-1">Confirm new password</label>
              <input
                v-model="credentialForm.confirmPassword"
                type="password"
                required
                minlength="4"
                class="w-full px-3 py-2.5 rounded-xl bg-surface-800/40 border border-surface-700/40 text-surface-100 text-sm focus:border-brand-600 focus:outline-none transition-colors"
              />
            </div>
            <div class="flex items-center gap-3">
              <button
                type="submit"
                class="px-5 py-2.5 rounded-xl text-sm font-bold bg-brand-700 text-white hover:bg-brand-600 transition-colors"
              >
                Save Password
              </button>
              <span v-if="credentialMsg" class="text-xs" :class="credentialMsgType === 'ok' ? 'text-emerald-400' : 'text-amber-400'">
                {{ credentialMsg }}
              </span>
            </div>
          </form>
        </div>
      </div>

      <!-- PLACEHOLDER SECTIONS -->
      <div v-else>
        <div class="ios-card rounded-2xl p-4 sm:p-6 text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-surface-800/30 flex items-center justify-center">
            <svg class="w-8 h-8 text-surface-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h3 class="text-lg font-bold text-surface-100 mb-2">{{ currentSidebarItem?.label }}</h3>
          <p class="text-sm text-surface-400 max-w-md mx-auto">
            This section mirrors the vending machine's admin panel. Connect to the machine's API to manage {{ currentSidebarItem?.label?.toLowerCase() }} settings in real-time.
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { useRealtimeMachineData } from '../composables/useRealtimeMachineData'
import { supabase } from '../lib/supabaseClient'
let Chart = null
let registerables = null
import { debounce } from '../utils/timing'

async function ensureChartsLoaded() {
  if (Chart && registerables) return
  const mod = await import('chart.js')
  Chart = mod.Chart
  registerables = mod.registerables
  Chart.register(...registerables)
}

const router = useRouter()
const { currentUser, isAdmin, logout, createUser, getUsers, deleteUser, updateCurrentUserPassword } = useAuth()
const machine = useRealtimeMachineData()

const manilaDayFmt = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit' })
const manilaTimeFmt = new Intl.DateTimeFormat('en-PH', {
  timeZone: 'Asia/Manila',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: true,
})
const manilaDateLongFmt = new Intl.DateTimeFormat('en-PH', {
  timeZone: 'Asia/Manila',
  weekday: 'short',
  year: 'numeric',
  month: 'short',
  day: 'numeric',
})

function toManilaYmd(iso) {
  if (!iso) return ''
  return manilaDayFmt.format(new Date(iso))
}

function manilaWeekdaySun0(y, m, d) {
  const iso = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}T12:00:00+08:00`
  const wd = new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Manila', weekday: 'short' })
    .format(new Date(iso))
    .slice(0, 3)
  const map = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }
  return map[wd] ?? 0
}

const phTime = ref('')
const phDate = ref('')
let phTimer = null

function refreshPhClock() {
  const now = new Date()
  phTime.value = manilaTimeFmt.format(now)
  phDate.value = manilaDateLongFmt.format(now)
}

const calYear = ref(new Date().getFullYear())
const calMonth = ref(new Date().getMonth() + 1)
const selectedYmd = ref('') // only set when user clicks a date

// Live feed calendar (same behavior as Sales Calendar)
const feedCalYear = ref(new Date().getFullYear())
const feedCalMonth = ref(new Date().getMonth() + 1)
const feedSelectedYmd = ref('')

const feedCalendarTitle = computed(() => {
  const d = new Date(feedCalYear.value, feedCalMonth.value - 1, 1)
  return d.toLocaleString('en-PH', { month: 'long', year: 'numeric' })
})

const feedCalendarCells = computed(() => {
  const y = feedCalYear.value
  const m = feedCalMonth.value
  const dim = new Date(y, m, 0).getDate()
  const firstWd = manilaWeekdaySun0(y, m, 1)
  const today = manilaDayFmt.format(new Date())
  const cells = []
  for (let i = 0; i < firstWd; i++) cells.push({ day: null, ymd: null })
  for (let d = 1; d <= dim; d++) {
    const ymd = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    cells.push({ day: d, ymd, isToday: ymd === today, isSelected: ymd === feedSelectedYmd.value })
  }
  while (cells.length % 7 !== 0) cells.push({ day: null, ymd: null })
  while (cells.length < 42) cells.push({ day: null, ymd: null })
  return cells.slice(0, 42)
})

function feedCalendarPrevMonth() {
  if (feedCalMonth.value <= 1) {
    feedCalMonth.value = 12
    feedCalYear.value--
  } else {
    feedCalMonth.value--
  }
  feedSelectedYmd.value = ''
}

function feedCalendarNextMonth() {
  if (feedCalMonth.value >= 12) {
    feedCalMonth.value = 1
    feedCalYear.value++
  } else {
    feedCalMonth.value++
  }
  feedSelectedYmd.value = ''
}

function clearFeedSelection() {
  feedSelectedYmd.value = ''
}

async function selectFeedCalendarDay(ymd) {
  // If the user clicks the same date again (common after "Clear selection"),
  // force a refresh by toggling the selection.
  if (feedSelectedYmd.value === ymd) {
    feedSelectedYmd.value = ''
    await nextTick()
    feedSelectedYmd.value = ymd
  } else {
    feedSelectedYmd.value = ymd
  }
  const [y, m] = ymd.split('-').map(Number)
  feedCalYear.value = y
  feedCalMonth.value = m
}

const calendarTitle = computed(() => {
  const d = new Date(calYear.value, calMonth.value - 1, 1)
  return d.toLocaleString('en-PH', { month: 'long', year: 'numeric' })
})

const calendarCells = computed(() => {
  const y = calYear.value
  const m = calMonth.value
  const dim = new Date(y, m, 0).getDate()
  const firstWd = manilaWeekdaySun0(y, m, 1)
  const today = manilaDayFmt.format(new Date())
  const cells = []
  for (let i = 0; i < firstWd; i++) cells.push({ day: null, ymd: null })
  for (let d = 1; d <= dim; d++) {
    const ymd = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    cells.push({ day: d, ymd, isToday: ymd === today, isSelected: ymd === selectedYmd.value })
  }
  while (cells.length % 7 !== 0) cells.push({ day: null, ymd: null })
  while (cells.length < 42) cells.push({ day: null, ymd: null })
  return cells.slice(0, 42)
})

function calendarPrevMonth() {
  if (calMonth.value <= 1) {
    calMonth.value = 12
    calYear.value--
  } else {
    calMonth.value--
  }
  // Changing month should clear selected-day history
  selectedYmd.value = ''
}

function calendarNextMonth() {
  if (calMonth.value >= 12) {
    calMonth.value = 1
    calYear.value++
  } else {
    calMonth.value++
  }
  // Changing month should clear selected-day history
  selectedYmd.value = ''
}

function selectCalendarDay(ymd) {
  selectedYmd.value = ymd
  const [y, m] = ymd.split('-').map(Number)
  calYear.value = y
  calMonth.value = m

  // UX: keep machine-events selection in sync with sales selection
  // so the "Machine events on selected date" table shows data immediately.
  feedSelectedYmd.value = ymd
  feedCalYear.value = y
  feedCalMonth.value = m
}

const salesForSelectedDay = computed(() => {
  const key = selectedYmd.value
  if (!key) return []
  return machine.transactions.value.filter((t) => {
    const ts = t.created_at || t.timestamp
    if (!ts) return false
    return toManilaYmd(ts) === key
  })
})

const liveFeedForSelectedDay = computed(() => {
  // IMPORTANT: This table uses the Machine Events calendar selection, not the Sales calendar.
  const key = feedSelectedYmd.value
  if (!key) return []
  return machine.liveFeed.value.filter((r) => {
    if (!r?.created_at) return false
    return toManilaYmd(r.created_at) === key
  })
})

const liveFeedForSelectedDayRows = computed(() => {
  const tf = new Intl.DateTimeFormat('en-PH', {
    timeZone: 'Asia/Manila',
    dateStyle: 'short',
    timeStyle: 'medium',
  })
  const key = feedSelectedYmd.value
  if (!key) return []

  // Build sale events from `transactions` so the list is always latest + 1 row per transaction.
  // Note: Supabase may still contain legacy duplicates; we dedupe by a sale fingerprint that matches
  // what the UI displays (time-second + slot + product + qty + amount).
  const txSource = (Array.isArray(machine.transactions.value) ? machine.transactions.value : [])
    .filter((t) => {
      const ts = t?.created_at || t?.timestamp
      if (!ts) return false
      return toManilaYmd(ts) === key
    })
  const tx = txSource
    .map((t, i) => {
      const ts = t?.created_at || t?.timestamp
      const sec = ts ? Math.floor(new Date(ts).getTime() / 1000) : 0
      const pid = t?.product_id ?? ''
      const slot = t?.slot_number ?? ''
      const qty = t?.quantity ?? ''
      const amtNum = Number.isFinite(Number(t?.total_amount)) ? Number(t.total_amount) : 0
      const amtCents = Math.round(amtNum * 100)
      const slotTxt = t?.slot_number != null ? `slot ${t.slot_number}` : 'slot ?'

      // Primary: stable machine id. Fallback: sale fingerprint that matches visible UI fields.
      const stableKey =
        t?.source_tx_id != null
          ? `tx:${t.source_tx_id}`
          : `sale:${sec}|${pid}|${slot}|${qty}|${amtCents}`

      return {
        key: stableKey,
        time: ts ? tf.format(new Date(ts)) : '—',
        type: 'sale',
        message: `Sale: ${resolveProductName(t)} · ${slotTxt} · ₱${amtNum}`,
        quantity: t?.quantity ?? '—',
        irBeamSensed: '—',
        totalAmount: amtNum,
        _sortAt: ts ? new Date(ts).getTime() : 0,
        _dedupeKey: `sale:${sec}|${pid}|${slot}|${qty}|${amtCents}`,
      }
    })

  // Collapse legacy duplicates even when they have different Supabase ids.
  const txDeduped = dedupeKeepFirst(tx, (r) => r.key || r._dedupeKey)

  const txKeys = new Set(txDeduped.map((r) => r.key))

  // Also include non-sale or non-transaction events from `live_feed` (deduped).
  const feedRaw = liveFeedForSelectedDay.value.slice()
    .sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0))
  const feedDeduped = dedupeKeepFirst(feedRaw, (r) => {
    const payload = coerceObject(r?.payload)
    const stable = payload?.source_tx_id ?? payload?.transaction_id ?? ''
    if (stable !== '') return `${r?.event_type || 'info'}:tx:${stable}`
    return `${r?.event_type || 'info'}:id:${r?.id ?? ''}:${r?.created_at ?? ''}:${r?.message ?? ''}`
  })
  const feedRows = feedDeduped
    .map((r, i) => {
      const payload = coerceObject(r?.payload)
      const stable = payload?.source_tx_id ?? payload?.transaction_id ?? null
      const key2 = stable != null && stable !== '' ? `tx:${stable}` : `feed:${r?.id ?? i}:${r?.created_at ?? ''}`
      if (stable != null && stable !== '' && txKeys.has(`tx:${stable}`)) return null

      // IMPORTANT: Sales are sourced from `transactions` above (1 row per sale).
      // If we also include sale rows from live_feed, you will see duplicates.
      if ((r?.event_type || payload?.event_type) === 'sale') return null

      const qty = pickFirstFiniteNumber(
        r.quantity, r.qty, r.dispensed_qty, r.dispensedQuantity, r.dispense_qty, r.qty_dispensed,
        payload.quantity, payload.qty, payload.dispensed_qty, payload.dispensedQuantity, payload.dispense_qty, payload.qty_dispensed
      )
      const ir = normalizeBool(
        r.ir_beam_sensed ?? r.irBeamSensed ?? r.beam_sensed ?? r.beamSensed ??
        r.ir_beam ?? r.irBeam ?? r.ir ??
        payload.ir_beam_sensed ?? payload.irBeamSensed ?? payload.beam_sensed ?? payload.beamSensed ??
        payload.ir_beam ?? payload.irBeam ?? payload.ir
      )
      const total = pickFirstFiniteNumber(
        r.total_amount, r.totalAmount,
        payload.total_amount, payload.totalAmount, payload.amount, payload.total
      )

      let message = r.message || ''
      if (!message.trim()) message = '—'

      return {
        key: key2,
        time: r.created_at ? tf.format(new Date(r.created_at)) : '—',
        type: r.event_type || 'info',
        message,
        quantity: qty ?? '—',
        irBeamSensed: ir ?? '—',
        totalAmount: total != null ? Number(total) : null,
        _sortAt: r.created_at ? new Date(r.created_at).getTime() : 0,
      }
    })
    .filter(Boolean)

  // Newest first (so the "latest" sale shows at the top)
  return [...txDeduped, ...feedRows].sort((a, b) => (b._sortAt || 0) - (a._sortAt || 0))
})

const liveFeedForSelectedDayTotals = computed(() => {
  const rows = liveFeedForSelectedDayRows.value
  const totalQty = rows.reduce((sum, r) => sum + (Number.isFinite(Number(r.quantity)) ? Number(r.quantity) : 0), 0)
  const irYes = rows.reduce((sum, r) => sum + (normalizeBool(r.irBeamSensed) === true ? 1 : 0), 0)
  const totalAmount = rows.reduce((sum, r) => sum + (Number.isFinite(Number(r.totalAmount)) ? Number(r.totalAmount) : 0), 0)
  return { count: rows.length, totalQty, irYes, totalAmount: totalAmount.toFixed(2) }
})

const selectedDayTotal = computed(() =>
  salesForSelectedDay.value.reduce((sum, t) => sum + Number(t.total_amount ?? 0), 0)
)

const manilaTimeOnlyFmt = new Intl.DateTimeFormat('en-PH', {
  timeZone: 'Asia/Manila',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: true,
})

const productNameById = computed(() => {
  const map = {}
  const products = Array.isArray(machine.products.value) ? machine.products.value : []
  for (const p of products) {
    if (p?.id == null) continue
    const name = String(p?.name ?? p?.product_name ?? '').trim()
    if (name) map[String(p.id)] = name
  }
  return map
})

const productBySlot = computed(() => {
  const map = {}
  const products = Array.isArray(machine.products.value) ? machine.products.value : []
  for (const p of products) {
    const slot = p?.slot_number
    if (slot == null) continue
    map[String(slot)] = p
  }
  return map
})

function resolveProductName(t) {
  const direct = String(t?.product_name ?? '').trim()
  if (direct) return direct
  const id = t?.product_id
  if (id != null) return productNameById.value[String(id)] || `Product #${id}`
  return 'Product'
}

const salesForSelectedDayRows = computed(() => {
  return salesForSelectedDay.value
    .slice()
    .sort((a, b) => new Date(a.created_at || a.timestamp || 0) - new Date(b.created_at || b.timestamp || 0))
    .map((t, i) => {
    const ts = t.created_at || t.timestamp
    return {
      key: `${t.id ?? i}-${ts}`,
      item: resolveProductName(t),
      timePh: ts ? manilaTimeOnlyFmt.format(new Date(ts)) : '—',
      qty: Number(t.quantity ?? 1),
      amount: Number(t.total_amount ?? 0).toFixed(2),
    }
  })
})

const subscriberEmailRows = computed(() => {
  return machine.subscriberEmails.value.map((r) => ({
    id: r.id,
    email: r.email,
    passwordRaw: r.password != null && String(r.password).length ? String(r.password) : '',
    createdPh: r.created_at ? `${manilaDayFmt.format(new Date(r.created_at))} ${manilaTimeOnlyFmt.format(new Date(r.created_at))}` : '—',
  }))
})

const bugReportRows = computed(() => {
  const tf = new Intl.DateTimeFormat('en-PH', {
    timeZone: 'Asia/Manila',
    dateStyle: 'short',
    timeStyle: 'medium',
  })
  const rows = Array.isArray(machine.bugReports.value) ? machine.bugReports.value : []
  return rows
    .slice()
    .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
    .map((r) => ({
      id: r.id,
      timePh: r.created_at ? tf.format(new Date(r.created_at)) : '—',
      machineId: r.machine_id || '—',
      category: r.category || '—',
      details: String(r.details || '').trim() || '—',
      version: r.version || '—',
      theme: r.theme || '—',
      status: r.status || 'open',
      fixedAt: r.fixed_at || null,
      fixedBy: r.fixed_by || '',
    }))
})

const bugReportTab = ref('open') // open | fixed
const bugReportsOpen = computed(() => bugReportRows.value.filter((r) => String(r.status || 'open') !== 'fixed'))
const bugReportsFixed = computed(() => bugReportRows.value.filter((r) => String(r.status || 'open') === 'fixed'))

const fixingReport = ref(null)
const fixConfirmed = ref(false)
const fixBusy = ref(false)
const fixMsg = ref('')

function openFixModal(row) {
  fixingReport.value = row
  fixConfirmed.value = false
  fixBusy.value = false
  fixMsg.value = ''
}

function closeFixModal() {
  fixingReport.value = null
  fixConfirmed.value = false
  fixBusy.value = false
  fixMsg.value = ''
}

async function confirmFix() {
  const r = fixingReport.value
  if (!r?.id) return
  if (!fixConfirmed.value) return
  fixBusy.value = true
  fixMsg.value = ''
  try {
    const fixedBy = currentUser?.value?.username || currentUser?.username || 'admin'
    const fixedAtIso = new Date().toISOString()
    let { error } = await supabase
      .from('bug_reports')
      .update({ status: 'fixed', fixed_at: fixedAtIso, fixed_by: fixedBy })
      .eq('id', r.id)
    if (error) {
      // If the database migration was applied but PostgREST schema cache isn't refreshed yet,
      // fall back to a minimal update that doesn't reference new columns.
      const msg = String(error?.message || error)
      if (/schema cache|could not find the ['"]fixed_at['"] column/i.test(msg)) {
        ;({ error } = await supabase
          .from('bug_reports')
          .update({ status: 'fixed' })
          .eq('id', r.id))
      }
      if (error) throw error
    }
    closeFixModal()
  } catch (e) {
    fixMsg.value = String(e?.message || e)
  } finally {
    fixBusy.value = false
  }
}

const passHashToast = ref('')
let passHashToastTimer = null
const salesReportMsg = ref('')
const salesReportMsgType = ref('ok')
let salesReportMsgTimer = null

function _bytesToHex(bytes) {
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('')
}

async function copyPasswordHash(raw) {
  if (!raw) return
  try {
    const enc = new TextEncoder().encode(String(raw))
    const digest = await crypto.subtle.digest('SHA-256', enc)
    const hex = _bytesToHex(new Uint8Array(digest))
    await navigator.clipboard.writeText(hex)
    passHashToast.value = `Copied SHA-256: ${hex.slice(0, 10)}…`
  } catch (e) {
    passHashToast.value = 'Could not copy hash (clipboard blocked).'
  } finally {
    if (passHashToastTimer) clearTimeout(passHashToastTimer)
    passHashToastTimer = setTimeout(() => { passHashToast.value = '' }, 1800)
  }
}

function setSalesReportMsg(msg, type = 'ok') {
  salesReportMsg.value = msg
  salesReportMsgType.value = type
  if (salesReportMsgTimer) clearTimeout(salesReportMsgTimer)
  salesReportMsgTimer = setTimeout(() => { salesReportMsg.value = '' }, 2600)
}

function salesReportRows() {
  return machine.transactions.value
    .slice()
    .sort((a, b) => new Date(a.created_at || a.timestamp || 0) - new Date(b.created_at || b.timestamp || 0))
    .map((t) => {
      const ts = t.created_at || t.timestamp
      const dateObj = ts ? new Date(ts) : null
      return {
        date_ph: dateObj ? manilaDayFmt.format(dateObj) : '',
        time_ph: dateObj ? manilaTimeOnlyFmt.format(dateObj) : '',
        product: resolveProductName(t),
        quantity: Number(t.quantity ?? 1),
        total_amount: Number(t.total_amount ?? 0).toFixed(2),
        payment_method: t.payment_method ?? '',
        rfid_user_id: t.rfid_user_id ?? '',
      }
    })
}

function triggerBrowserDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function escCsv(v) {
  const s = String(v ?? '')
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`
  return s
}

function downloadSalesReportCsv() {
  const rows = salesReportRows()
  const totalQty = rows.reduce((s, r) => s + Number(r.quantity ?? 0), 0)
  const totalAmt = rows.reduce((s, r) => s + Number(r.total_amount ?? 0), 0)
  const header = ['Date (PH)', 'Time (PH)', 'Product', 'Quantity', 'Total Amount', 'Payment Method', 'RFID User ID']
  const body = rows.map((r) => [
    r.date_ph,
    r.time_ph,
    r.product,
    r.quantity,
    r.total_amount,
    r.payment_method,
    r.rfid_user_id,
  ])
  body.push(['', '', 'TOTAL SALES', String(totalQty), totalAmt.toFixed(2), '', ''])
  const csv = [header, ...body].map((line) => line.map(escCsv).join(',')).join('\n')
  const stamp = manilaDayFmt.format(new Date()).replaceAll('-', '')
  triggerBrowserDownload(new Blob([csv], { type: 'text/csv;charset=utf-8;' }), `sales_report_${stamp}.csv`)
  setSalesReportMsg(`CSV report downloaded (${rows.length} row(s)). Note: CSV format does not support cell colors.`, 'warn')
}

async function downloadSalesReportXlsx() {
  try {
    const rows = salesReportRows()
    const totalQty = rows.reduce((s, r) => s + Number(r.quantity ?? 0), 0)
    const totalAmt = rows.reduce((s, r) => s + Number(r.total_amount ?? 0), 0)
    const stamp = manilaDayFmt.format(new Date()).replaceAll('-', '')
    const ExcelJS = (await import('exceljs')).default
    const templatePath = '/IC-Annual-Sales-Performance-Report-11538.xlsx'

    const wb = new ExcelJS.Workbook()
    let usedTemplate = false
    try {
      const res = await fetch(templatePath, { cache: 'no-store' })
      if (res.ok) {
        const buf = await res.arrayBuffer()
        await wb.xlsx.load(buf)
        usedTemplate = true
      }
    } catch (_) {
      // fallback below
    }
    const ws = wb.worksheets[0] || wb.addWorksheet('Sales Report')
    if (ws.rowCount > 0) ws.spliceRows(1, ws.rowCount)

    ws.columns = [
      { header: 'Date (PH)', key: 'date_ph', width: 14 },
      { header: 'Time (PH)', key: 'time_ph', width: 14 },
      { header: 'Product', key: 'product', width: 28 },
      { header: 'Quantity', key: 'quantity', width: 12 },
      { header: 'Total Amount', key: 'total_amount', width: 14 },
      { header: 'Payment Method', key: 'payment_method', width: 16 },
      { header: 'RFID User ID', key: 'rfid_user_id', width: 16 },
    ]

    rows.forEach((r) => {
      ws.addRow({
        date_ph: r.date_ph,
        time_ph: r.time_ph,
        product: r.product,
        quantity: Number(r.quantity ?? 0),
        total_amount: Number(r.total_amount ?? 0),
        payment_method: r.payment_method,
        rfid_user_id: r.rfid_user_id,
      })
    })

    ws.addRow({
      date_ph: '',
      time_ph: '',
      product: 'TOTAL SALES',
      quantity: totalQty,
      total_amount: Number(totalAmt.toFixed(2)),
      payment_method: '',
      rfid_user_id: '',
    })

    ws.getRow(1).eachCell((cell) => {
      cell.font = { bold: true, color: { argb: 'FFFFFFFF' } }
      cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1F4E78' } }
      cell.alignment = { vertical: 'middle', horizontal: 'center' }
      cell.border = {
        top: { style: 'thin', color: { argb: 'FFBFC7D5' } },
        left: { style: 'thin', color: { argb: 'FFBFC7D5' } },
        bottom: { style: 'thin', color: { argb: 'FFBFC7D5' } },
        right: { style: 'thin', color: { argb: 'FFBFC7D5' } },
      }
    })

    for (let i = 2; i <= ws.rowCount; i++) {
      const row = ws.getRow(i)
      const isTotal = i === ws.rowCount
      const fillColor = isTotal ? 'FFFFF2CC' : i % 2 === 0 ? 'FFF8FBFF' : 'FFFFFFFF'
      row.eachCell((cell) => {
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: fillColor } }
        cell.border = {
          top: { style: 'thin', color: { argb: 'FFE5EAF2' } },
          left: { style: 'thin', color: { argb: 'FFE5EAF2' } },
          bottom: { style: 'thin', color: { argb: 'FFE5EAF2' } },
          right: { style: 'thin', color: { argb: 'FFE5EAF2' } },
        }
        if (isTotal) {
          cell.font = { bold: true, color: { argb: 'FF7A5600' } }
        }
      })
    }

    const totalRow = ws.getRow(ws.rowCount)
    totalRow.getCell(3).font = { bold: true, color: { argb: 'FF7A5600' } }
    totalRow.getCell(4).font = { bold: true, color: { argb: 'FF7A5600' } }
    totalRow.getCell(5).font = { bold: true, color: { argb: 'FF7A5600' } }

    ws.eachRow((row, rowNum) => {
      if (rowNum > 1) {
        row.getCell(4).alignment = { horizontal: 'right' }
        row.getCell(5).alignment = { horizontal: 'right' }
      }
    })

    const out = await wb.xlsx.writeBuffer()
    triggerBrowserDownload(
      new Blob([out], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
      `sales_report_${stamp}.xlsx`
    )
    setSalesReportMsg(
      usedTemplate
        ? `XLSX report downloaded using template (${rows.length} row(s)).`
        : `XLSX report downloaded (${rows.length} row(s)).`,
      usedTemplate ? 'ok' : 'warn'
    )
  } catch (err) {
    setSalesReportMsg(`Failed to generate XLSX: ${String(err?.message || err)}`, 'warn')
  }
}

const activeSection = ref('overview')
const sidebarOpen = ref(false)

// === TOTAL SALES (clickable categories) ===
const totalSalesMode = ref('overall') // day | week | month | overall
const showSalesModeMenu = ref(false)
const salesModeMenuEl = ref(null)
const salesModeBtnEl = ref(null)
const isCompactUi = ref(false)

const totalSalesModeOptions = [
  { id: 'day', label: 'Per day' },
  { id: 'week', label: 'Per week' },
  { id: 'month', label: 'Per month' },
  { id: 'overall', label: 'Overall' },
]

function toggleSalesModeMenu() {
  showSalesModeMenu.value = !showSalesModeMenu.value
}

function setTotalSalesMode(mode) {
  totalSalesMode.value = mode
  showSalesModeMenu.value = false
}

function closeSalesModeMenu() {
  showSalesModeMenu.value = false
}

function handleDocPointerDown(e) {
  if (!showSalesModeMenu.value) return
  const t = e?.target
  const menu = salesModeMenuEl.value
  const btn = salesModeBtnEl.value
  if (menu && menu.contains(t)) return
  if (btn && btn.contains(t)) return
  closeSalesModeMenu()
}

function updateCompactUi() {
  isCompactUi.value = typeof window !== 'undefined' ? window.innerWidth < 640 : false
}

function startOfManilaDay(d = new Date()) {
  const ymd = manilaDayFmt.format(d) // YYYY-MM-DD in Asia/Manila
  return new Date(`${ymd}T00:00:00+08:00`)
}

function startOfManilaMonth(d = new Date()) {
  const ymd = manilaDayFmt.format(d)
  const [y, m] = ymd.split('-').map(Number)
  return new Date(`${y}-${String(m).padStart(2, '0')}-01T00:00:00+08:00`)
}

function normalizeBool(v) {
  if (v === true || v === false) return v
  if (v == null) return null
  if (typeof v === 'number') return v !== 0
  const s = String(v).trim().toLowerCase()
  if (s === 'true' || s === 'yes' || s === 'y' || s === '1') return true
  if (s === 'false' || s === 'no' || s === 'n' || s === '0') return false
  return null
}

function coerceObject(v) {
  if (!v) return {}
  if (typeof v === 'object') return v
  if (typeof v === 'string') {
    const s = v.trim()
    if (!s) return {}
    try {
      const parsed = JSON.parse(s)
      return parsed && typeof parsed === 'object' ? parsed : {}
    } catch (_) {
      return {}
    }
  }
  return {}
}

function toNumberLoose(v) {
  if (v == null) return NaN
  if (typeof v === 'number') return v
  const s = String(v).replace(/,/g, '').trim()
  if (!s) return NaN
  // handles "₱25.00", "P25", "25.00 PHP"
  const m = s.match(/-?\d+(\.\d+)?/)
  if (!m) return NaN
  return Number(m[0])
}

function pickFirstFiniteNumber(...vals) {
  for (const v of vals) {
    const n = toNumberLoose(v)
    if (Number.isFinite(n)) return n
  }
  return null
}

function formatHourAmPm(hourValue) {
  const hRaw = Number.parseInt(String(hourValue ?? '').trim(), 10)
  if (!Number.isFinite(hRaw)) return String(hourValue ?? '—')
  const h = ((hRaw % 24) + 24) % 24
  const suffix = h >= 12 ? 'PM' : 'AM'
  const h12 = h % 12 || 12
  return `${h12}:00 ${suffix}`
}

const SCHOOL_HOUR_START = 5   // 5:00 AM
const SCHOOL_HOUR_END = 22    // 10:00 PM
function isWithinSchoolHours(hourValue) {
  const h = Number.parseInt(String(hourValue ?? '').trim(), 10)
  return Number.isFinite(h) && h >= SCHOOL_HOUR_START && h <= SCHOOL_HOUR_END
}

const totalSalesValue = computed(() => {
  const tx = machine.transactions.value
  const mode = totalSalesMode.value
  const now = new Date()

  if (mode === 'overall') {
    return tx.reduce((sum, t) => sum + Number(t.total_amount ?? 0), 0)
  }

  const from =
    mode === 'day'
      ? startOfManilaDay(now)
      : mode === 'month'
        ? startOfManilaMonth(now)
        : (() => {
            const start = startOfManilaDay(now)
            start.setDate(start.getDate() - 6) // last 7 days incl today
            return start
          })()

  return tx.reduce((sum, t) => {
    const ts = t.created_at || t.timestamp
    if (!ts) return sum
    const d = new Date(ts)
    if (Number.isNaN(d.getTime())) return sum
    return d >= from ? sum + Number(t.total_amount ?? 0) : sum
  }, 0)
})

const salesModeLabel = computed(() => {
  const id = totalSalesMode.value
  return totalSalesModeOptions.find((o) => o.id === id)?.label ?? 'Overall'
})

// Sidebar items matching the machine's admin panel
const sidebarItems = [
  { id: 'overview', label: 'Overview', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" /></svg>' },
  { id: 'machine-feed', label: 'Live feed', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>' },
  { id: 'sales-reports', label: 'Sales Reports', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>' },
  { id: 'reports', label: 'Reports', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 3h9l3 3v15a2 2 0 01-2 2H6a2 2 0 01-2-2V5a2 2 0 012-2zM7 7h10M7 11h10M7 15h6" /></svg>' },
  { id: 'prediction', label: 'Prediction Analysis', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>' },
  { id: 'users', label: 'Manage Users', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>' },
  { id: 'credentials', label: 'Change Credentials', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>' },
]

const currentSidebarItem = computed(() => sidebarItems.find(i => i.id === activeSection.value))

function handleLogout() {
  logout()
  router.push('/')
}

const adminProfileImage = ref(localStorage.getItem('adminProfileImg') || null)

function handleProfileUpload(e) {
  const file = e.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (ev) => {
      adminProfileImage.value = ev.target.result
      localStorage.setItem('adminProfileImg', ev.target.result)
    }
    reader.readAsDataURL(file)
  }
}

// === LIVE DATA (Supabase Realtime) ===
const overviewStats = computed(() => ([
  { id: 'totalSales', label: 'Total Sales', value: `₱${Number(totalSalesValue.value || 0).toFixed(2)}`, color: 'text-emerald-400' },
  { label: 'Orders', value: String(machine.overview.value.orders || 0), color: 'text-blue-400' },
  { label: 'Active Customers', value: String(machine.overview.value.activeCustomers || 0), color: 'text-purple-400' },
  { label: 'Low-stock Products', value: String(machine.overview.value.lowStock || 0), color: 'text-amber-400' },
]))

const lowStockItems = computed(() => machine.lowStockProducts.value)
const recentTransactions = computed(() => machine.recentTransactions.value)

function _normName(rawName) {
  return String(rawName ?? '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function productKeyByName(rawName) {
  const n = _normName(rawName)
  if (!n) return ''

  // Exact-ish matches first
  if (n === 'alcohol') return 'alcohol'
  if (n === 'soap') return 'soap'
  if (n === 'deodorant' || n === 'deo') return 'deodorant'
  if (n === 'mouthwash' || n === 'mouth wash') return 'mouthwash'
  if (n === 'wet wipes' || n === 'wetwipes' || n === 'wipes') return 'wet_wipes'
  if (n === 'tissue' || n === 'tissues') return 'tissue'
  if (n === 'panty liner' || n === 'panty liners' || n === 'pantyliners' || n === 'panti liner') return 'panty_liner'
  if (n === 'all night pads' || n === 'all night pad' || n === 'all nightpads') return 'all_night_pads'
  if (n === 'regular with wings' || n === 'regular with wings pads' || n === 'regular w wings pads') return 'regular_with_wings'
  if (n === 'non wing pad' || n === 'non wing pads' || n === 'non wings pad' || n === 'non wings pads') return 'non_wing_pad'

  // Fuzzy matches for common variants coming from UI/DB
  if (n.includes('panty') && n.includes('liner')) return 'panty_liner'
  if (n.includes('all') && n.includes('night') && n.includes('pad')) return 'all_night_pads'
  if (n.includes('mouth') && n.includes('wash')) return 'mouthwash'
  if (n.includes('wet') && n.includes('wipe')) return 'wet_wipes'
  if (n.includes('tissue')) return 'tissue'
  if (n.includes('deodor')) return 'deodorant'
  if (n.includes('alcohol')) return 'alcohol'
  if (n.includes('soap')) return 'soap'
  if (n.includes('regular') && n.includes('wing')) return 'regular_with_wings'
  if (n.includes('non') && n.includes('wing') && n.includes('pad')) return 'non_wing_pad'

  return ''
}

function lowStockThresholdByName(rawName) {
  const key = productKeyByName(rawName)
  // Total Low Stocks Product provided by you
  if (key === 'alcohol') return 1
  if (key === 'soap') return 3
  if (key === 'deodorant') return 3
  if (key === 'mouthwash') return 3
  if (key === 'wet_wipes') return 1
  if (key === 'tissue') return 1
  if (key === 'panty_liner') return 3
  if (key === 'all_night_pads') return 2
  if (key === 'regular_with_wings') return 3
  if (key === 'non_wing_pad') return 3
  return 3
}

function capacityByName(rawName) {
  const key = productKeyByName(rawName)
  // Total Stocks Product (capacity) provided by you
  if (key === 'alcohol') return 3
  if (key === 'soap') return 7
  if (key === 'deodorant') return 9
  if (key === 'mouthwash') return 7
  if (key === 'wet_wipes') return 3
  if (key === 'tissue') return 3
  if (key === 'panty_liner') return 8
  if (key === 'all_night_pads') return 6
  if (key === 'regular_with_wings') return 7
  if (key === 'non_wing_pad') return 7
  return 0
}

const stockStatusRows = computed(() => {
  const products = Array.isArray(machine.products.value) ? machine.products.value : []

  return products
    .slice()
    .sort((a, b) => Number(a.slot_number ?? a.slot ?? 0) - Number(b.slot_number ?? b.slot ?? 0))
    .map((p, idx) => {
      const slot = p.slot_number ?? p.slot ?? idx + 1
      const stockRaw = Number(p.current_stock ?? p.stock ?? p.quantity ?? 0)
      const capFallback = capacityByName(p.name ?? p.product_name)
      const capRaw = Number(p.capacity ?? p.max_stock ?? 0)
      // If the product is one of the known items, use the provided capacity as source-of-truth.
      // Otherwise, fall back to DB capacity.
      const capacity =
        capFallback > 0
          ? capFallback
          : Math.max(1, (Number.isFinite(capRaw) && capRaw > 0 ? capRaw : 1))
      const priceNum = Number(p.price ?? p.unit_price ?? 0)
      // Clamp stock for display/ratio so old DB values (e.g. 10) don't exceed real capacity (e.g. 3).
      const stock = Math.max(0, Math.min(stockRaw, capacity))
      const ratioPct = Math.round((stock / capacity) * 100)
      const threshold = lowStockThresholdByName(p.name ?? p.product_name)

      const status =
        stock <= 0 ? 'Empty'
        : stock >= capacity ? 'Full'
        : stock <= threshold ? 'Low'
        : 'In Stock'

      const statusClass =
        status === 'Full'
          ? 'bg-emerald-400/15 text-emerald-300 border-emerald-400/25'
          : status === 'In Stock'
            ? 'bg-emerald-400/10 text-emerald-300 border-emerald-400/20'
            : status === 'Low'
              ? 'bg-amber-400/15 text-amber-300 border-amber-400/25'
              : 'bg-red-400/15 text-red-300 border-red-400/25'

      return {
        key: String(p.id ?? `${slot}-${p.name ?? p.product_name ?? 'product'}`),
        slot: String(slot),
        product: p.name ?? p.product_name ?? '—',
        price: Number.isFinite(priceNum) ? priceNum.toFixed(2) : '0.00',
        ratio: `${stock}/${capacity} (${Math.min(100, Math.max(0, ratioPct))}%)`,
        status,
        statusClass,
        isLow: stock <= threshold,
      }
    })
})

const lowStockTableRows = computed(() => {
  const rows = Array.isArray(machine.lowStockProducts.value) ? machine.lowStockProducts.value : []
  if (rows.length === 0) {
    // Fallback: if the materialized Supabase table is empty/not yet refreshed,
    // render from realtime `products` so UI never appears blank.
    return stockStatusRows.value
  }
  return rows
    .slice()
    .sort((a, b) => Number(a.slot_number ?? 0) - Number(b.slot_number ?? 0))
    .map((r, idx) => {
      const stock = Number(r.current_stock ?? 0)
      const cap = Math.max(1, Number(r.capacity ?? 1))
      const ratioPct = Math.round((stock / cap) * 100)
      const status = String(r.status ?? '').trim() || (stock <= 0 ? 'Empty' : 'Low')
      const statusClass =
        status === 'Full'
          ? 'bg-emerald-400/15 text-emerald-300 border-emerald-400/25'
          : status === 'In Stock'
            ? 'bg-emerald-400/10 text-emerald-300 border-emerald-400/20'
            : status === 'Empty'
          ? 'bg-red-400/15 text-red-300 border-red-400/25'
          : 'bg-amber-400/15 text-amber-300 border-amber-400/25'

      return {
        key: String(r.product_id ?? `${r.slot_number ?? idx}-${r.name ?? 'product'}`),
        slot: String(r.slot_number ?? ''),
        product: r.name ?? '—',
        price: Number.isFinite(Number(r.price)) ? Number(r.price).toFixed(2) : '0.00',
        ratio: `${stock}/${cap} (${Math.min(100, Math.max(0, ratioPct))}%)`,
        status,
        statusClass,
      }
    })
})

const machineSummaryLine = computed(() => {
  const p = machine.products.value.length
  const t = machine.transactions.value.length
  const f = machine.liveFeed.value.length
  return `Synced from Supabase: ${p} product row(s) · ${t} transaction row(s) loaded · ${f} live_feed event(s). Charts update automatically.`
})

const liveFeedRange = ref('day') // day | week | month (overview preview only)
const liveFeedRangeOptions = [
  { id: 'day', label: 'Day' },
  { id: 'week', label: '1 Week' },
  { id: 'month', label: 'Month' },
]

function toEpochSeconds(iso) {
  if (!iso) return null
  try {
    const ms = Date.parse(String(iso))
    if (!Number.isNaN(ms)) return Math.floor(ms / 1000)
  } catch (_) {
    // ignore
  }
  return null
}

function stableLiveFeedIdentity(raw) {
  const payload = coerceObject(raw?.payload)
  const stable = payload?.source_tx_id ?? payload?.transaction_id ?? raw?.source_tx_id
  if (stable != null && stable !== '') return `tx:${stable}`

  const sec = toEpochSeconds(raw?.created_at) ?? 'na'
  const qty = pickFirstFiniteNumber(raw?.quantity, payload?.quantity) ?? ''
  const amt = pickFirstFiniteNumber(raw?.total_amount, payload?.total_amount, payload?.amount, payload?.total) ?? ''
  const type = raw?.event_type || ''

  // Avoid using the full message (it can vary by whitespace/format); extract slot + product when possible.
  const msg = String(raw?.message || payload?.message || '')
  const slot = (msg.match(/slot\s*([0-9]+)/i) || [])[1] || ''
  const product = (msg.match(/^Sale:\s*(.*?)\s*[•\-|]/i) || [])[1] || ''

  return `fp:${sec}|${type}|${slot}|${product}|${qty}|${amt}`
}

function dedupeKeepFirst(list, keyFn) {
  const seen = new Set()
  const out = []
  for (const item of Array.isArray(list) ? list : []) {
    const k = keyFn(item)
    if (seen.has(k)) continue
    seen.add(k)
    out.push(item)
  }
  return out
}

function liveFeedInRange(iso, range) {
  if (!iso) return false
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return false
  const now = new Date()
  const deltaMs = now.getTime() - d.getTime()
  const dayMs = 24 * 60 * 60 * 1000
  if (range === 'day') return deltaMs <= dayMs
  if (range === 'week') return deltaMs <= 7 * dayMs
  return deltaMs <= 31 * dayMs
}

// IMPORTANT: For "1 row per transaction", build the sale feed from `transactions`
// (which has stable ids via `source_tx_id`), not from `live_feed` (append-only and may contain duplicates).
const liveFeedRowsAll = computed(() => {
  const tf = new Intl.DateTimeFormat('en-PH', {
    timeZone: 'Asia/Manila',
    dateStyle: 'short',
    timeStyle: 'medium',
  })
  const tx = Array.isArray(machine.transactions.value) ? machine.transactions.value : []
  const rows = tx.map((t) => {
    const name = resolveProductName(t)
    const slotTxt = t?.slot_number != null ? `slot ${t.slot_number}` : 'slot ?'
    const amt = Number.isFinite(Number(t?.total_amount)) ? Number(t.total_amount) : 0
    return {
      id: t?.id,
      key: `tx:${t?.source_tx_id ?? t?.id}`,
      time: t?.created_at ? tf.format(new Date(t.created_at)) : '—',
      type: 'sale',
      message: `Sale: ${name} · ${slotTxt} · ₱${amt}`,
      quantity: t?.quantity ?? null,
      irBeamSensed: null,
      totalAmount: amt,
      _createdAt: t?.created_at ?? null,
    }
  })
  // If Supabase has duplicate transaction rows, collapse by source_tx_id first.
  return dedupeKeepFirst(rows, (r) => r.key)
})

const liveFeedRows = computed(() => {
  const range = liveFeedRange.value
  return liveFeedRowsAll.value.filter((r) => liveFeedInRange(r._createdAt, range))
})

const liveFeedPreview = computed(() => liveFeedRows.value.slice(0, 10))

const liveFeedRowsForSelectedDay = computed(() => {
  const key = feedSelectedYmd.value
  if (!key) return []
  return liveFeedRowsAll.value.filter((r) => r._createdAt && toManilaYmd(r._createdAt) === key)
})

const liveFeedPreviewTotals = computed(() => {
  const rows = liveFeedPreview.value
  const totalQty = rows.reduce((sum, r) => sum + (Number.isFinite(Number(r.quantity)) ? Number(r.quantity) : 0), 0)
  const irYes = rows.reduce((sum, r) => sum + (normalizeBool(r.irBeamSensed) === true ? 1 : 0), 0)
  const totalAmount = rows.reduce((sum, r) => sum + (Number.isFinite(Number(r.totalAmount)) ? Number(r.totalAmount) : 0), 0)
  return { count: rows.length, totalQty, irYes, totalAmount: totalAmount.toFixed(2) }
})

const liveFeedTotals = computed(() => {
  const rows = liveFeedRows.value
  const totalQty = rows.reduce((sum, r) => sum + (Number.isFinite(Number(r.quantity)) ? Number(r.quantity) : 0), 0)
  const irYes = rows.reduce((sum, r) => sum + (normalizeBool(r.irBeamSensed) === true ? 1 : 0), 0)
  const totalAmount = rows.reduce((sum, r) => sum + (Number.isFinite(Number(r.totalAmount)) ? Number(r.totalAmount) : 0), 0)
  return { count: rows.length, totalQty, irYes, totalAmount: totalAmount.toFixed(2) }
})

const liveFeedSelectedTotals = computed(() => {
  const rows = liveFeedRowsForSelectedDay.value
  const totalQty = rows.reduce((sum, r) => sum + (Number.isFinite(Number(r.quantity)) ? Number(r.quantity) : 0), 0)
  const irYes = rows.reduce((sum, r) => sum + (normalizeBool(r.irBeamSensed) === true ? 1 : 0), 0)
  const totalAmount = rows.reduce((sum, r) => sum + (Number.isFinite(Number(r.totalAmount)) ? Number(r.totalAmount) : 0), 0)
  return { count: rows.length, totalQty, irYes, totalAmount: totalAmount.toFixed(2) }
})

// === CHARTS ===
const salesTrendChart = ref(null)
const monthlySalesChart = ref(null)
const topProductsChart = ref(null)
const predictionRestockChart = ref(null)
const predictionSplitChart = ref(null)
const predictionPeakHoursChart = ref(null)
const predictionWeekdaysChart = ref(null)

let chartInstances = {}

// Chart ranges
const salesTrendRange = ref('15d') // 15d | 7d | 6m | 1y
const monthlyRange = ref('6m') // 1m | 3m | 6m

const salesRangeOptions = [
  { id: '15d', label: '15 Days' },
  { id: '7d', label: '7 Days' },
  { id: '6m', label: '1–6 Mo' },
  { id: '1y', label: '1 Year' },
]

const monthlyRangeOptions = [
  { id: '1m', label: '1 Month' },
  { id: '3m', label: '3 Months' },
  { id: '6m', label: '6 Months' },
]

function glow3dPlugin() {
  // Soft shadow behind datasets to fake a subtle "3D" depth.
  return {
    id: 'glow3d',
    beforeDatasetDraw(chart) {
      const ctx = chart.ctx
      ctx.save()
      ctx.shadowColor = 'rgba(0, 0, 0, 0.45)'
      ctx.shadowBlur = 12
      ctx.shadowOffsetY = 6
    },
    afterDatasetDraw(chart) {
      chart.ctx.restore()
    },
  }
}

function getChartColors() {
  return {
    grid: 'rgba(148, 163, 184, 0.08)',
    text: '#94a3b8',
    line: '#10b981',
    bar1: '#42A5F5',
    bar2: '#7E57C2',
  }
}

function buildDailyTrend(transactions, days) {
  const fmtMd = new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Manila', month: 'numeric', day: 'numeric' })
  const labels = []
  const keys = []
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - (days - 1 - i))
    keys.push(manilaDayFmt.format(d))
    labels.push(fmtMd.format(d))
  }
  const sums = Object.fromEntries(keys.map((k) => [k, 0]))
  for (const t of transactions) {
    if (!t.created_at) continue
    const k = manilaDayFmt.format(new Date(t.created_at))
    if (sums[k] !== undefined) sums[k] += Number(t.total_amount ?? 0)
  }
  return { labels, data: keys.map((k) => Number(sums[k].toFixed(2))) }
}

function buildMonthlyTrend(transactions, months) {
  const labels = []
  const keys = []
  for (let i = months - 1; i >= 0; i--) {
    const d = new Date()
    d.setMonth(d.getMonth() - (months - 1 - i))
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    keys.push(`${y}-${m}`)
    labels.push(d.toLocaleString('en-PH', { month: 'short', year: '2-digit' }))
  }
  const monthFmt = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit' })
  const sums = Object.fromEntries(keys.map((k) => [k, 0]))
  for (const t of transactions) {
    if (!t.created_at) continue
    const k = monthFmt.format(new Date(t.created_at))
    if (sums[k] !== undefined) sums[k] += Number(t.total_amount ?? 0)
  }
  return { labels, data: keys.map((k) => Number(sums[k].toFixed(2))) }
}

function buildCurrentMonthDailySales(transactions) {
  // 1-month view: show totals per day for the CURRENT month (all days, even if zero).
  const now = new Date()
  // Anchor in Manila to avoid month rollover issues.
  const manilaNow = new Date(
    new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Manila',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(now) + 'T12:00:00+08:00'
  )
  const y = manilaNow.getFullYear()
  const m = manilaNow.getMonth() + 1
  const daysInMonth = new Date(y, m, 0).getDate()

  const labels = []
  const keys = []
  for (let day = 1; day <= daysInMonth; day++) {
    const iso = `${y}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}T12:00:00+08:00`
    const d = new Date(iso)
    keys.push(manilaDayFmt.format(d))
    labels.push(String(day))
  }

  const sums = Object.fromEntries(keys.map((k) => [k, 0]))
  for (const t of transactions) {
    const ts = t.created_at || t.timestamp
    if (!ts) continue
    const k = manilaDayFmt.format(new Date(ts))
    if (sums[k] !== undefined) sums[k] += Number(t.total_amount ?? 0)
  }
  return { labels, data: keys.map((k) => Number(sums[k].toFixed(2))) }
}

function buildSalesByCreated(transactions, mode) {
  if (mode === '7d') return buildDailyTrend(transactions, 7)
  if (mode === '15d') return buildDailyTrend(transactions, 15)
  if (mode === '1y') return buildMonthlyTrend(transactions, 12)
  // "1–6 Mo"
  return buildMonthlyTrend(transactions, 6)
}

function buildTopProductsFromTx(transactions, products) {
  const byId = {}
  const bySlot = {}
  for (const p of Array.isArray(products) ? products : []) {
    if (p?.id != null) byId[String(p.id)] = String(p.name ?? p.product_name ?? '').trim()
    if (p?.slot_number != null) bySlot[String(p.slot_number)] = String(p.name ?? p.product_name ?? '').trim()
  }

  const qtyBy = {}
  for (const t of transactions) {
    let name = (t.product_name && String(t.product_name).trim()) || ''
    if (!name && t.product_id != null) name = byId[String(t.product_id)] || ''
    if (!name && t.slot_number != null) name = bySlot[String(t.slot_number)] || ''
    if (!name && t.product_id != null) name = `Product #${t.product_id}`
    if (!name) name = 'Product'
    qtyBy[name] = (qtyBy[name] || 0) + Number(t.quantity ?? 1)
  }
  const entries = Object.entries(qtyBy).sort((a, b) => b[1] - a[1])
  if (entries.length === 0 && products.length) {
    return {
      labels: products.slice(0, 6).map((p) => p.name || `Slot ${p.slot_number}`),
      data: products.slice(0, 6).map(() => 0),
    }
  }
  const top = entries.slice(0, 8)
  return {
    labels: top.map((e) => e[0]),
    data: top.map((e) => e[1]),
  }
}

function updateChartsFromMachine() {
  const colors = getChartColors()
  const glow3d = glow3dPlugin()
  const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: { bottom: 18 },
    },
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: {
        grid: { color: colors.grid },
        ticks: { color: colors.text, font: { size: 10 }, padding: 8 },
      },
      y: {
        position: 'right',
        grid: { color: colors.grid },
        ticks: { color: colors.text, font: { size: 10 }, padding: 6 },
        beginAtZero: true,
      },
    },
  }

  const tx = machine.transactions.value
  const prod = machine.products.value
  const trend = buildSalesByCreated(tx, salesTrendRange.value)
  const monthly =
    monthlyRange.value === '1m'
      ? buildCurrentMonthDailySales(tx)
      : buildMonthlyTrend(tx, monthlyRange.value === '3m' ? 3 : 6)
  const topP = buildTopProductsFromTx(tx, prod)

  if (!Chart) return

  if (salesTrendChart.value) {
    if (chartInstances.salesTrend) chartInstances.salesTrend.destroy()
    const ctx = salesTrendChart.value.getContext('2d')
    const gradient = ctx.createLinearGradient(0, 0, 0, salesTrendChart.value.height || 240)
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.45)')
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.03)')
    chartInstances.salesTrend = new Chart(salesTrendChart.value, {
      type: 'line',
      data: {
        labels: trend.labels,
        datasets: [{
          data: trend.data,
          borderColor: colors.line,
          backgroundColor: gradient,
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: colors.line,
          borderWidth: 2,
        }],
      },
      options: {
        ...chartDefaults,
        plugins: {
          ...chartDefaults.plugins,
          tooltip: {
            enabled: true,
            callbacks: {
              label: (ctx) => `₱${Number(ctx.parsed.y ?? 0).toFixed(2)}`,
            },
          },
        },
      },
      plugins: [glow3d],
    })
  }

  if (monthlySalesChart.value) {
    if (chartInstances.monthly) chartInstances.monthly.destroy()
    const ctx = monthlySalesChart.value.getContext('2d')
    const barGrad = ctx.createLinearGradient(0, 0, 0, monthlySalesChart.value.height || 240)
    barGrad.addColorStop(0, 'rgba(66, 165, 245, 0.95)')
    barGrad.addColorStop(1, 'rgba(66, 165, 245, 0.25)')
    chartInstances.monthly = new Chart(monthlySalesChart.value, {
      type: 'bar',
      data: {
        labels: monthly.labels,
        datasets: [{
          data: monthly.data,
          backgroundColor: barGrad,
          borderRadius: 10,
          borderSkipped: false,
          maxBarThickness: monthlyRange.value === '1m' ? 18 : 48,
        }],
      },
      options: {
        ...chartDefaults,
        plugins: {
          ...chartDefaults.plugins,
          tooltip: {
            callbacks: {
              label: (ctx) => `₱${Number(ctx.parsed.y ?? 0).toFixed(2)}`,
            },
          },
        },
      },
      plugins: [glow3d],
    })
  }

  if (topProductsChart.value) {
    if (chartInstances.topProducts) chartInstances.topProducts.destroy()
    const ctx = topProductsChart.value.getContext('2d')
    const topGrad = ctx.createLinearGradient(0, 0, topProductsChart.value.width || 360, 0)
    topGrad.addColorStop(0, 'rgba(126, 87, 194, 0.25)')
    topGrad.addColorStop(1, 'rgba(126, 87, 194, 0.95)')
    chartInstances.topProducts = new Chart(topProductsChart.value, {
      type: 'bar',
      data: {
        labels: topP.labels.length ? topP.labels : ['No sales yet'],
        datasets: [{
          data: topP.data.length ? topP.data : [0],
          backgroundColor: topGrad,
          borderRadius: 10,
          borderSkipped: false,
          maxBarThickness: 28,
        }],
      },
      options: {
        ...chartDefaults,
        indexAxis: 'y',
        scales: {
          x: {
            position: 'right',
            grid: { color: colors.grid },
            ticks: { color: colors.text, font: { size: 10 } },
            beginAtZero: true,
          },
          y: {
            position: 'left',
            grid: { display: false },
            ticks: { color: colors.text, font: { size: 10 } },
          },
        },
        plugins: {
          ...chartDefaults.plugins,
          tooltip: {
            callbacks: {
              label: (ctx) => `${Number(ctx.parsed.x ?? 0)} sold`,
            },
          },
        },
      },
      plugins: [glow3d],
    })
  }
}

// === USER MANAGEMENT ===
const showUserForm = ref(false)
const newUser = ref({ username: '', password: '', role: 'staff' })
const userMsg = ref('')
const userMsgType = ref('success')
const allUsers = ref(getUsers())
const credentialForm = ref({ password: '', confirmPassword: '' })
const credentialMsg = ref('')
const credentialMsgType = ref('ok')

function handleCreateUser() {
  userMsg.value = ''
  const result = createUser(newUser.value.username, newUser.value.password, newUser.value.role)
  if (result.success) {
    userMsg.value = 'Account created!'
    userMsgType.value = 'success'
    allUsers.value = getUsers()
    newUser.value = { username: '', password: '', role: 'staff' }
    setTimeout(() => { showUserForm.value = false; userMsg.value = '' }, 1500)
  } else {
    userMsg.value = result.message
    userMsgType.value = 'error'
  }
}

async function handleDeleteUser(username) {
  const result = deleteUser(username)
  if (result.success) {
    allUsers.value = getUsers()
    await machine.reload()
  }
}

async function handleChangeCredentials() {
  credentialMsg.value = ''
  const pwd = String(credentialForm.value.password || '')
  const confirm = String(credentialForm.value.confirmPassword || '')
  if (!pwd || !confirm) {
    credentialMsgType.value = 'warn'
    credentialMsg.value = 'Password fields are required.'
    return
  }
  if (pwd !== confirm) {
    credentialMsgType.value = 'warn'
    credentialMsg.value = 'Passwords do not match.'
    return
  }
  const res = await updateCurrentUserPassword(pwd)
  credentialMsgType.value = res.success ? 'ok' : 'warn'
  credentialMsg.value = res.message || (res.success ? 'Password updated.' : 'Could not update password.')
  if (res.success) {
    credentialForm.value = { password: '', confirmPassword: '' }
    await machine.reload()
  }
}

// Charts: refresh when machine data or overview tab changes
const debouncedUpdateCharts = debounce(() => {
  if (activeSection.value !== 'overview') return
  updateChartsFromMachine()
}, 180)

watch(activeSection, async (val) => {
  if (val === 'overview') {
    await nextTick()
    debouncedUpdateCharts()
  }
})

watch(
  () => [
    machine.loading.value,
    machine.transactions.value.length,
    machine.products.value.length,
    salesTrendRange.value,
    monthlyRange.value,
  ],
  async () => {
    await nextTick()
    if (activeSection.value === 'overview') debouncedUpdateCharts()
  }
)

onMounted(async () => {
  updateCompactUi()
  refreshPhClock()
  phTimer = setInterval(refreshPhClock, 1000)
  const today = manilaDayFmt.format(new Date())
  const [y, m] = today.split('-').map(Number)
  calYear.value = y
  calMonth.value = m
  await nextTick()
  await ensureChartsLoaded()
  debouncedUpdateCharts()
  document.addEventListener('pointerdown', handleDocPointerDown, { capture: true })
  window.addEventListener('resize', updateCompactUi, { passive: true })
})

onBeforeUnmount(() => {
  if (phTimer) clearInterval(phTimer)
  if (salesReportMsgTimer) clearTimeout(salesReportMsgTimer)
  document.removeEventListener('pointerdown', handleDocPointerDown, { capture: true })
  window.removeEventListener('resize', updateCompactUi)
})

// === PREDICTION ANALYSIS ===
const predictionRan = ref(false)
const predictionLoading = ref(false)
const predictionResults = ref([])
const predictionInsights = ref(null)
const predictionModelLabel = ref('')

function buildPredictionCharts() {
  const colors = getChartColors()
  const glow3d = glow3dPlugin()

  if (!Chart) return

  if (predictionRestockChart.value) {
    if (chartInstances.predRestock) chartInstances.predRestock.destroy()
    const rows = predictionResults.value
      .slice()
      .sort((a, b) => Number(b.recommended_restock_qty ?? 0) - Number(a.recommended_restock_qty ?? 0))
      .slice(0, 8)
    const ctx = predictionRestockChart.value.getContext('2d')
    const grad = ctx.createLinearGradient(0, 0, predictionRestockChart.value.width || 360, 0)
    grad.addColorStop(0, 'rgba(245, 158, 11, 0.18)')
    grad.addColorStop(1, 'rgba(245, 158, 11, 0.95)')
    chartInstances.predRestock = new Chart(predictionRestockChart.value, {
      type: 'bar',
      data: {
        labels: rows.map((r) => r.product_name),
        datasets: [{
          data: rows.map((r) => Number(r.recommended_restock_qty ?? 0)),
          backgroundColor: grad,
          borderRadius: 10,
          borderSkipped: false,
          maxBarThickness: 26,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (c) => `Restock: ${Number(c.parsed.x ?? 0)}` } },
        },
        scales: {
          x: { position: 'right', grid: { color: colors.grid }, ticks: { color: colors.text, font: { size: 10 } }, beginAtZero: true },
          y: { grid: { display: false }, ticks: { color: colors.text, font: { size: 10 } } },
        },
      },
      plugins: [glow3d],
    })
  }

  if (predictionSplitChart.value) {
    if (chartInstances.predSplit) chartInstances.predSplit.destroy()
    const yes = predictionResults.value.filter((r) => Number(r.recommended_restock_qty ?? 0) > 0).length
    const no = Math.max(0, predictionResults.value.length - yes)
    chartInstances.predSplit = new Chart(predictionSplitChart.value, {
      type: 'doughnut',
      data: {
        labels: ['Restock needed', 'No restock'],
        datasets: [{
          data: [yes, no],
          backgroundColor: ['rgba(245, 158, 11, 0.85)', 'rgba(16, 185, 129, 0.55)'],
          borderColor: ['rgba(245, 158, 11, 0.2)', 'rgba(16, 185, 129, 0.2)'],
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '62%',
        plugins: {
          legend: { position: 'bottom', labels: { color: colors.text, boxWidth: 10, padding: 14 } },
          tooltip: { callbacks: { label: (c) => `${c.label}: ${c.parsed}` } },
        },
      },
      plugins: [glow3d],
    })
  }

  if (predictionInsights.value?.peakHours?.length && predictionPeakHoursChart.value) {
    if (chartInstances.predPeakHours) chartInstances.predPeakHours.destroy()
    const rows = predictionInsights.value.peakHours.slice().sort((a, b) => Number(a.hour) - Number(b.hour)).slice(0, 12)
    const ctx = predictionPeakHoursChart.value.getContext('2d')
    const grad = ctx.createLinearGradient(0, 0, 0, predictionPeakHoursChart.value.height || 220)
    grad.addColorStop(0, 'rgba(56, 189, 248, 0.9)')
    grad.addColorStop(1, 'rgba(56, 189, 248, 0.18)')
    chartInstances.predPeakHours = new Chart(predictionPeakHoursChart.value, {
      type: 'bar',
      data: {
        labels: rows.map((r) => formatHourAmPm(r.hour)),
        datasets: [{
          data: rows.map((r) => Number(r.qty ?? 0)),
          backgroundColor: grad,
          borderRadius: 10,
          borderSkipped: false,
          maxBarThickness: 28,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (c) => `${Number(c.parsed.y ?? 0)} items` } },
        },
        scales: {
          x: { grid: { color: colors.grid }, ticks: { color: colors.text, font: { size: 10 } } },
          y: { position: 'right', grid: { color: colors.grid }, ticks: { color: colors.text, font: { size: 10 } }, beginAtZero: true },
        },
      },
      plugins: [glow3d],
    })
  }

  if (predictionInsights.value?.weekdays?.length && predictionWeekdaysChart.value) {
    if (chartInstances.predWeekdays) chartInstances.predWeekdays.destroy()
    const rows = predictionInsights.value.weekdays.slice()
    chartInstances.predWeekdays = new Chart(predictionWeekdaysChart.value, {
      type: 'pie',
      data: {
        labels: rows.map((r) => r.day),
        datasets: [{
          data: rows.map((r) => Number(r.qty ?? 0)),
          backgroundColor: [
            'rgba(99, 102, 241, 0.85)',
            'rgba(16, 185, 129, 0.75)',
            'rgba(245, 158, 11, 0.78)',
            'rgba(236, 72, 153, 0.72)',
            'rgba(56, 189, 248, 0.72)',
            'rgba(168, 85, 247, 0.7)',
            'rgba(244, 63, 94, 0.68)',
          ],
          borderColor: 'rgba(15, 23, 42, 0.7)',
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: colors.text, boxWidth: 10, padding: 14 } },
          tooltip: { callbacks: { label: (c) => `${c.label}: ${c.parsed} items` } },
        },
      },
      plugins: [glow3d],
    })
  }
}

async function runPrediction() {
  if (predictionRan.value) return
  predictionLoading.value = true

  try {
    // Preferred: deep-learning (MLP) output produced by predictionAnalysis/run_all.py
    const res = await fetch('/prediction/forecast_next_day_deep.json', { cache: 'no-store' })
    if (res.ok) {
      const data = await res.json()
      if (Array.isArray(data) && data.length) {
        predictionResults.value = data
          .map((r) => ({
            product_name: r.product_name,
            predicted_sales_tomorrow: Number(r.predicted_sales_tomorrow ?? 0),
            current_stock: Number(r.current_stock ?? 0),
            capacity: Number(r.capacity ?? 0),
            recommended_restock_qty: Number(r.recommended_restock_qty ?? 0),
          }))
          .sort((a, b) => b.predicted_sales_tomorrow - a.predicted_sales_tomorrow)
        predictionModelLabel.value = 'Deep (MLP)'
      }
    }
  } catch (_) {
    // ignore and fallback below
  }

  // Load insights (peak hours + busiest days)
  try {
    const insRes = await fetch('/prediction/insights.json', { cache: 'no-store' })
    if (insRes.ok) {
      const ins = await insRes.json()
      if (ins && typeof ins === 'object') {
        predictionInsights.value = {
          topProducts: Array.isArray(ins.top_products) ? ins.top_products.map((r) => ({ name: r.name, qty: Number(r.qty ?? 0) })) : [],
          peakHours: Array.isArray(ins.peak_hours)
            ? ins.peak_hours
                .map((r) => ({ hour: String(r.hour).padStart(2, '0'), qty: Number(r.qty ?? 0) }))
                .filter((r) => isWithinSchoolHours(r.hour))
            : [],
          weekdays: Array.isArray(ins.weekdays) ? ins.weekdays.map((r) => ({ day: r.day, qty: Number(r.qty ?? 0) })) : [],
        }
      }
    }
  } catch (_) {
    // ignore
  }

  // Fallback: lightweight realtime estimate from currently loaded transactions (no server required).
  if (!predictionResults.value.length) {
    const products = Array.isArray(machine.products.value) ? machine.products.value : []
    const tx = Array.isArray(machine.transactions.value) ? machine.transactions.value : []

    // Build catalog keyed by normalized product key.
    const catalogByKey = {}
    const catalogById = {}
    for (const p of products) {
      const key = productKeyByName(p.name ?? p.product_name)
      const cap = Math.max(0, Number(p.capacity ?? p.max_stock ?? 0))
      const stockRaw = Math.max(0, Number(p.current_stock ?? p.stock ?? p.quantity ?? 0))
      const stock = cap > 0 ? Math.min(stockRaw, cap) : stockRaw
      const entry = {
        product_name: p.name ?? p.product_name ?? `Slot ${p.slot_number ?? ''}`.trim(),
        current_stock: stock,
        capacity: cap,
      }
      if (key) catalogByKey[key] = entry
      if (p.id != null) catalogById[String(p.id)] = key || ''
    }

    const qtyByKey = {}
    const since = new Date()
    since.setDate(since.getDate() - 14) // 14-day moving average for tomorrow estimate

    for (const t of tx) {
      const ts = t.created_at || t.timestamp
      if (!ts) continue
      const d = new Date(ts)
      if (Number.isNaN(d.getTime()) || d < since) continue
      const qty = Math.max(0, Number(t.quantity ?? 1))
      let key = ''
      if (t.product_id != null) key = catalogById[String(t.product_id)] || ''
      if (!key) key = productKeyByName(t.product_name)
      if (!key) continue
      qtyByKey[key] = (qtyByKey[key] || 0) + qty
    }

    predictionResults.value = Object.entries(catalogByKey)
      .map(([key, c]) => {
        const sold14 = Number(qtyByKey[key] || 0)
        const predTomorrow = sold14 / 14
        const recommended = Math.max(0, Math.ceil(predTomorrow) - Number(c.current_stock || 0))
        return {
          product_name: c.product_name,
          predicted_sales_tomorrow: Number(predTomorrow.toFixed(2)),
          current_stock: Number(c.current_stock || 0),
          capacity: Number(c.capacity || 0),
          recommended_restock_qty: recommended,
        }
      })
      .sort((a, b) => b.predicted_sales_tomorrow - a.predicted_sales_tomorrow)

    predictionModelLabel.value = 'Realtime (heuristic fallback)'
  }

  // Fallback insights from currently loaded transactions.
  if (!predictionInsights.value) {
    const tx = Array.isArray(machine.transactions.value) ? machine.transactions.value : []
    const topBy = {}
    const hourBy = {}
    const dayBy = {}
    for (const t of tx) {
      const qty = Math.max(0, Number(t.quantity ?? 1))
      const name = String(t.product_name || '').trim()
      if (name) topBy[name] = (topBy[name] || 0) + qty
      const ts = t.created_at || t.timestamp
      if (!ts) continue
      const d = new Date(ts)
      if (Number.isNaN(d.getTime())) continue
      const hour = new Intl.DateTimeFormat('en-PH', { timeZone: 'Asia/Manila', hour: '2-digit', hour12: false }).format(d)
      if (!isWithinSchoolHours(hour)) continue
      const day = new Intl.DateTimeFormat('en-PH', { timeZone: 'Asia/Manila', weekday: 'short' }).format(d)
      hourBy[hour] = (hourBy[hour] || 0) + qty
      dayBy[day] = (dayBy[day] || 0) + qty
    }
    predictionInsights.value = {
      topProducts: Object.entries(topBy).sort((a, b) => b[1] - a[1]).map(([name, qty]) => ({ name, qty })),
      peakHours: Object.entries(hourBy).sort((a, b) => Number(b[1]) - Number(a[1])).map(([hour, qty]) => ({ hour, qty })),
      weekdays: Object.entries(dayBy).sort((a, b) => Number(b[1]) - Number(a[1])).map(([day, qty]) => ({ day, qty })),
    }
  }

  await nextTick()
  buildPredictionCharts()
  predictionLoading.value = false
  predictionRan.value = true
}
</script>

<style scoped>
.ios-card {
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(148, 163, 184, 0.08);
}

html.light .ios-card {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(148, 163, 184, 0.22);
  box-shadow: 0 10px 30px rgba(2, 6, 23, 0.08);
}

.text-fade-enter-active { transition: all 0.3s ease-out; }
.text-fade-leave-active { transition: all 0.2s ease-in; }
.text-fade-enter-from { opacity: 0; transform: translateY(8px); }
.text-fade-leave-to { opacity: 0; transform: translateY(-8px); }

/* Mobile: momentum scrolling for overflow areas */
.overflow-y-auto {
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

/* Total Sales popover */
.sales-pop-enter-active,
.sales-pop-leave-active {
  transition: opacity 160ms ease, transform 160ms ease;
}
.sales-pop-enter-from,
.sales-pop-leave-to {
  opacity: 0;
  transform: translateY(6px) scale(0.98);
}

.sales-menu-scroll::-webkit-scrollbar { width: 6px; }
.sales-menu-scroll::-webkit-scrollbar-track { background: transparent; }
.sales-menu-scroll::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.28);
  border-radius: 999px;
}
.sales-menu-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.42);
}

html.light .sales-menu-scroll::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.22);
}
html.light .sales-menu-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.34);
}

/* Mobile bottom sheet */
.sales-sheet-enter-active,
.sales-sheet-leave-active {
  transition: opacity 180ms ease;
}
.sales-sheet-enter-from,
.sales-sheet-leave-to {
  opacity: 0;
}
</style>
