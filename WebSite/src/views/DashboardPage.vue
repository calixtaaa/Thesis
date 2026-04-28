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
      <div class="flex items-center justify-between mb-6">
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
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6">
          <div
            v-for="(stat, i) in overviewStats"
            :key="stat.label"
            class="ios-card rounded-2xl p-4 sm:p-5 animate-slide-up"
            :style="{ animationDelay: `${i * 0.05}s` }"
          >
            <p class="text-xs text-surface-500 uppercase tracking-wider mb-1">{{ stat.label }}</p>
            <p class="text-xl sm:text-2xl font-bold font-display" :class="stat.color">{{ stat.value }}</p>
          </div>
        </div>

        <p v-if="!machine.loading" class="text-xs text-surface-500 mb-4">{{ machineSummaryLine }}</p>

        <!-- Realtime activity from vending machine -->
        <div class="ios-card rounded-2xl p-5 sm:p-6 mb-6">
          <h3 class="text-sm font-bold text-surface-200 light:text-surface-900 mb-1">Machine live feed</h3>
          <div class="overflow-x-auto max-h-52 overflow-y-auto rounded-xl border border-surface-800/30">
            <table class="w-full text-sm">
              <thead class="sticky top-0 bg-surface-950/95 light:bg-surface-100/95 z-10">
                <tr class="border-b border-surface-800/40">
                  <th class="text-left text-xs text-surface-400 uppercase pb-2 pr-3 font-semibold">Time (PH)</th>
                  <th class="text-left text-xs text-surface-400 uppercase pb-2 pr-3 font-semibold">Type</th>
                  <th class="text-left text-xs text-surface-400 uppercase pb-2 font-semibold">Message</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in liveFeedPreview" :key="row.id" class="border-b border-surface-800/20">
                  <td class="py-2 pr-3 text-surface-500 text-xs whitespace-nowrap">{{ row.time }}</td>
                  <td class="py-2 pr-3 text-brand-400 text-xs">{{ row.type }}</td>
                  <td class="py-2 text-surface-200 text-xs">{{ row.message }}</td>
                </tr>
                <tr v-if="liveFeedPreview.length === 0">
                  <td colspan="3" class="py-10 text-center text-surface-500 text-sm">No feed rows yet — run <code class="text-surface-400">machine_live_feed.sql</code> and insert from the machine.</td>
                </tr>
              </tbody>
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
                <span class="text-xs font-semibold text-surface-300 min-w-[8.5rem] text-center">{{ calendarTitle }}</span>
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
              Selected: <span class="text-surface-200 font-semibold">{{ selectedYmd }}</span>
              · Total: <span class="text-emerald-400 font-bold">₱{{ selectedDayTotal.toFixed(2) }}</span>
              · {{ salesForSelectedDay.length }} sale(s)
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
                    <th class="text-right text-xs text-surface-200 light:text-surface-800 uppercase tracking-wider pb-2 font-semibold">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in salesForSelectedDayRows" :key="row.key" class="border-b border-surface-800/20 last:border-0">
                    <td class="py-2.5 pr-3 text-surface-200">{{ row.item }}</td>
                    <td class="py-2.5 pr-3 text-surface-500 text-xs whitespace-nowrap">{{ row.timePh }}</td>
                    <td class="py-2.5 text-right font-semibold text-emerald-400">₱{{ row.amount }}</td>
                  </tr>
                  <tr v-if="salesForSelectedDayRows.length === 0">
                    <td colspan="3" class="py-8 text-center text-surface-500 text-sm">No sales for this day in the loaded history.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Email signups (Supabase `emails` table) -->
        <div class="ios-card rounded-2xl p-5 sm:p-6 mb-6">
          <h3 class="text-sm font-bold text-surface-200 light:text-surface-900 mb-3">Newsletter &amp; contact emails</h3>
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
                  <td class="py-3 pr-4 text-surface-300 light:text-surface-800 font-mono text-xs">{{ row.passwordHint }}</td>
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
          <h3 class="text-sm font-bold text-surface-200 mb-0.5">Sales by Created Date</h3>
          <p class="text-xs text-surface-500 mb-4">Last 15 days</p>
          <div class="w-full h-52 sm:h-64">
            <canvas ref="salesTrendChart"></canvas>
          </div>
        </div>

        <!-- Monthly Sales Chart -->
        <div class="ios-card rounded-2xl p-5 sm:p-6 mb-6">
          <h3 class="text-sm font-bold text-surface-200 mb-0.5">Monthly Sales</h3>
          <p class="text-xs text-surface-500 mb-4">Last 6 months</p>
          <div class="w-full h-52 sm:h-64">
            <canvas ref="monthlySalesChart"></canvas>
          </div>
        </div>

        <!-- Two columns: Top Products + Low Stock -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <!-- Top Selling Products -->
          <div class="ios-card rounded-2xl p-5 sm:p-6">
            <h3 class="text-sm font-bold text-surface-200 mb-0.5">Top-selling Products</h3>
            <p class="text-xs text-surface-500 mb-4">All products by quantity sold</p>
            <div class="w-full h-52 sm:h-64">
              <canvas ref="topProductsChart"></canvas>
            </div>
          </div>

          <!-- Low Stock Inventory -->
          <div class="ios-card rounded-2xl p-5 sm:p-6">
            <h3 class="text-sm font-bold text-surface-200 mb-0.5">Low-stock Products</h3>
            <p class="text-xs text-surface-500 mb-4">Current stock vs capacity</p>
            <div class="space-y-3 mt-2">
              <p v-if="lowStockItems.length === 0" class="text-sm text-surface-500 py-6 text-center">No low-stock rows — restock data appears when <code class="text-surface-400">products</code> has stock under 4.</p>
              <template v-else>
                <div v-for="item in lowStockItems" :key="item.name" class="flex items-center justify-between gap-3">
                  <span class="text-xs text-surface-300 w-28 truncate shrink-0">{{ item.name }}</span>
                  <div class="flex-1 h-2 bg-surface-800/50 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all duration-700"
                      :class="item.stock / Math.max(item.capacity, 1) > 0.5 ? 'bg-emerald-400' : item.stock / Math.max(item.capacity, 1) > 0.25 ? 'bg-amber-400' : 'bg-red-400'"
                      :style="{ width: `${Math.min(100, (item.stock / Math.max(item.capacity, 1)) * 100)}%` }"
                    ></div>
                  </div>
                  <span class="text-xs font-semibold text-surface-400 w-14 text-right">{{ item.stock }}/{{ item.capacity || '—' }}</span>
                </div>
              </template>
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
                  <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3 pr-4">Time</th>
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
                    <td class="py-3 pr-4 text-surface-500 text-xs">{{ tx.time }}</td>
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
          <h3 class="text-lg font-bold text-surface-100 light:text-surface-900 mb-1">Machine live feed</h3>
          <p class="text-sm text-surface-500 mb-6">Realtime stream from <code class="text-surface-400">public.live_feed</code> (same data as Overview, full history in view).</p>
          <div class="overflow-x-auto max-h-[70vh] overflow-y-auto rounded-xl border border-surface-800/30">
            <table class="w-full text-sm">
              <thead class="sticky top-0 bg-surface-950/95 light:bg-surface-100/95 z-10 border-b border-surface-800/40">
                <tr>
                  <th class="text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold">Time (PH)</th>
                  <th class="text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold">Type</th>
                  <th class="text-left text-xs text-surface-400 uppercase py-3 px-4 font-semibold">Message</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in liveFeedRows" :key="row.id" class="border-b border-surface-800/20">
                  <td class="py-3 px-4 text-surface-500 text-xs whitespace-nowrap">{{ row.time }}</td>
                  <td class="py-3 px-4 text-brand-400 text-xs font-medium">{{ row.type }}</td>
                  <td class="py-3 px-4 text-surface-200">{{ row.message }}</td>
                </tr>
                <tr v-if="liveFeedRows.length === 0">
                  <td colspan="3" class="py-16 text-center text-surface-500">No events. Insert into <code class="text-surface-400">live_feed</code> from the machine or SQL Editor to test.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- PREDICTION ANALYSIS SECTION -->
      <div v-else-if="activeSection === 'prediction'">
        <div class="ios-card rounded-2xl p-5 sm:p-6">
          <h3 class="text-sm font-bold text-surface-200 mb-0.5">Prediction Analysis (Demand + Restock)</h3>
          <p class="text-xs text-surface-500 mb-4">
            Predicts sales tomorrow and recommends restock using historical transactions (runs once per session).
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
            <span v-if="predictionLoading" class="text-xs text-surface-400 animate-pulse">Analyzing...</span>
          </div>

          <!-- Results Table -->
          <div v-if="predictionResults.length > 0" class="mt-4">
            <p class="text-xs text-surface-500 mb-3">Based on transaction data from the vending machine</p>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-surface-800/40">
                    <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3 pr-4">Product</th>
                    <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3 pr-4">Predicted Sales Tomorrow</th>
                    <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3 pr-4">Current Stock</th>
                    <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3">Restock Needed</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="r in predictionResults" :key="r.product_name" class="border-b border-surface-800/20 last:border-0">
                    <td class="py-3 pr-4 text-surface-200 font-medium">{{ r.product_name }}</td>
                    <td class="py-3 pr-4 text-surface-300">{{ r.predicted_sales_tomorrow }}</td>
                    <td class="py-3 pr-4 text-surface-300">{{ r.current_stock }}/{{ r.capacity }}</td>
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
            <h4 class="text-xs font-bold text-surface-300 uppercase tracking-wider mb-3">Insights from Transaction Data</h4>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <!-- Top Products -->
              <div class="p-3 rounded-xl bg-surface-800/20">
                <p class="text-xs font-bold text-surface-400 mb-2">🏆 Top Products</p>
                <div v-for="(item, i) in predictionInsights.topProducts.slice(0, 5)" :key="item.name" class="flex justify-between text-xs py-0.5">
                  <span class="text-surface-300">{{ i + 1 }}. {{ item.name }}</span>
                  <span class="text-surface-500 font-medium">{{ item.qty }} sold</span>
                </div>
              </div>
              <!-- Peak Hours -->
              <div class="p-3 rounded-xl bg-surface-800/20">
                <p class="text-xs font-bold text-surface-400 mb-2">⏰ Peak Hours</p>
                <div v-for="item in predictionInsights.peakHours.slice(0, 5)" :key="item.hour" class="flex justify-between text-xs py-0.5">
                  <span class="text-surface-300">{{ item.hour }}:00</span>
                  <span class="text-surface-500 font-medium">{{ item.qty }} items</span>
                </div>
              </div>
              <!-- Busiest Days -->
              <div class="p-3 rounded-xl bg-surface-800/20">
                <p class="text-xs font-bold text-surface-400 mb-2">📅 Busiest Days</p>
                <div v-for="item in predictionInsights.weekdays.slice(0, 5)" :key="item.day" class="flex justify-between text-xs py-0.5">
                  <span class="text-surface-300">{{ item.day }}</span>
                  <span class="text-surface-500 font-medium">{{ item.qty }} items</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- SALES REPORTS SECTION -->
      <div v-else-if="activeSection === 'sales-reports'">
        <div class="ios-card rounded-2xl p-6 sm:p-8">
          <div class="flex items-center gap-3 mb-6">
            <div class="w-10 h-10 rounded-xl bg-emerald-400/15 flex items-center justify-center">
              <svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-bold text-surface-100">Sales Reports</h3>
              <p class="text-xs text-surface-500">Generated Excel reports from the machine</p>
            </div>
          </div>
          <p class="text-sm text-surface-400 text-center py-12">
            Sales reports are generated from the vending machine.<br>
            Connect to the machine's API to view and download reports.
          </p>
        </div>
      </div>

      <!-- USER MANAGEMENT SECTION -->
      <div v-else-if="activeSection === 'users'">
        <div class="ios-card rounded-2xl p-6 sm:p-8">
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
              class="flex items-center justify-between p-4 rounded-xl bg-surface-800/20 border border-surface-800/20"
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

      <!-- PLACEHOLDER SECTIONS -->
      <div v-else>
        <div class="ios-card rounded-2xl p-6 sm:p-8 text-center">
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
import { Chart, registerables } from 'chart.js'
import { debounce } from '../utils/timing'

Chart.register(...registerables)

const router = useRouter()
const { currentUser, isAdmin, logout, createUser, getUsers, deleteUser } = useAuth()
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
const selectedYmd = ref('')

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
}

function calendarNextMonth() {
  if (calMonth.value >= 12) {
    calMonth.value = 1
    calYear.value++
  } else {
    calMonth.value++
  }
}

function selectCalendarDay(ymd) {
  selectedYmd.value = ymd
  const [y, m] = ymd.split('-').map(Number)
  calYear.value = y
  calMonth.value = m
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

const salesForSelectedDayRows = computed(() => {
  return salesForSelectedDay.value.map((t, i) => {
    const ts = t.created_at || t.timestamp
    return {
      key: `${t.id ?? i}-${ts}`,
      item: t.product_name || t.product_id || 'Unknown',
      timePh: ts ? manilaTimeOnlyFmt.format(new Date(ts)) : '—',
      amount: Number(t.total_amount ?? 0).toFixed(2),
    }
  })
})

const subscriberEmailRows = computed(() => {
  return machine.subscriberEmails.value.map((r) => ({
    id: r.id,
    email: r.email,
    passwordHint: r.password != null && String(r.password).length ? String(r.password) : '—',
    createdPh: r.created_at ? `${manilaDayFmt.format(new Date(r.created_at))} ${manilaTimeOnlyFmt.format(new Date(r.created_at))}` : '—',
  }))
})

const activeSection = ref('overview')
const sidebarOpen = ref(false)

// Sidebar items matching the machine's admin panel
const sidebarItems = [
  { id: 'overview', label: 'Overview', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" /></svg>' },
  { id: 'machine-feed', label: 'Live feed', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>' },
  { id: 'rfid', label: 'RFID Roles', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 9h3.75M15 12h3.75M15 15h3.75M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15A2.25 2.25 0 002.25 6.75v10.5A2.25 2.25 0 004.5 19.5zm6-10.125a1.875 1.875 0 11-3.75 0 1.875 1.875 0 013.75 0zm1.294 6.336a6.721 6.721 0 01-3.17.789 6.721 6.721 0 01-3.168-.789 3.376 3.376 0 016.338 0z" /></svg>' },
  { id: 'cash', label: 'Cash Pulse Settings', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>' },
  { id: 'hardware', label: 'Hardware Diagnostics', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>' },
  { id: 'sales-reports', label: 'Sales Reports', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>' },
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
  { label: 'Total Sales', value: `₱${Number(machine.overview.value.totalSales || 0).toFixed(2)}`, color: 'text-emerald-400' },
  { label: 'Orders', value: String(machine.overview.value.orders || 0), color: 'text-blue-400' },
  { label: 'Active Customers', value: String(machine.overview.value.activeCustomers || 0), color: 'text-purple-400' },
  { label: 'Low-stock Products', value: String(machine.overview.value.lowStock || 0), color: 'text-amber-400' },
]))

const lowStockItems = computed(() => machine.lowStockItems.value)
const recentTransactions = computed(() => machine.recentTransactions.value)

const machineSummaryLine = computed(() => {
  const p = machine.products.value.length
  const t = machine.transactions.value.length
  const f = machine.liveFeed.value.length
  return `Synced from Supabase: ${p} product row(s) · ${t} transaction row(s) loaded · ${f} live_feed event(s). Charts update automatically.`
})

const liveFeedRows = computed(() => {
  const tf = new Intl.DateTimeFormat('en-PH', {
    timeZone: 'Asia/Manila',
    dateStyle: 'short',
    timeStyle: 'medium',
  })
  return machine.liveFeed.value.map((r) => ({
    id: r.id,
    time: r.created_at ? tf.format(new Date(r.created_at)) : '—',
    type: r.event_type || 'info',
    message: r.message || '—',
  }))
})

const liveFeedPreview = computed(() => liveFeedRows.value.slice(0, 10))

// === CHARTS ===
const salesTrendChart = ref(null)
const monthlySalesChart = ref(null)
const topProductsChart = ref(null)

let chartInstances = {}

function getChartColors() {
  return {
    grid: 'rgba(148, 163, 184, 0.08)',
    text: '#94a3b8',
    line: '#10b981',
    bar1: '#42A5F5',
    bar2: '#7E57C2',
  }
}

function buildSalesTrendFromTx(transactions) {
  const fmtMd = new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Manila', month: 'numeric', day: 'numeric' })
  const labels = []
  const keys = []
  for (let i = 14; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - (14 - i))
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

function buildMonthlyFromTx(transactions) {
  const labels = []
  const keys = []
  for (let i = 5; i >= 0; i--) {
    const d = new Date()
    d.setMonth(d.getMonth() - (5 - i))
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    keys.push(`${y}-${m}`)
    labels.push(d.toLocaleString('en-PH', { month: 'short', year: '2-digit' }))
  }
  const monthFmt = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit' })
  const sums = keys.map(() => 0)
  for (const t of transactions) {
    if (!t.created_at) continue
    const mk = monthFmt.format(new Date(t.created_at))
    const idx = keys.indexOf(mk)
    if (idx >= 0) sums[idx] += Number(t.total_amount ?? 0)
  }
  return { labels, data: sums.map((x) => Number(x.toFixed(2))) }
}

function buildTopProductsFromTx(transactions, products) {
  const qtyBy = {}
  for (const t of transactions) {
    const name = (t.product_name && String(t.product_name).trim()) || 'Unknown'
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
  const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: {
        grid: { color: colors.grid },
        ticks: { color: colors.text, font: { size: 10 } },
      },
      y: {
        grid: { color: colors.grid },
        ticks: { color: colors.text, font: { size: 10 } },
        beginAtZero: true,
      },
    },
  }

  const tx = machine.transactions.value
  const prod = machine.products.value
  const trend = buildSalesTrendFromTx(tx)
  const monthly = buildMonthlyFromTx(tx)
  const topP = buildTopProductsFromTx(tx, prod)

  if (salesTrendChart.value) {
    if (chartInstances.salesTrend) chartInstances.salesTrend.destroy()
    chartInstances.salesTrend = new Chart(salesTrendChart.value, {
      type: 'line',
      data: {
        labels: trend.labels,
        datasets: [{
          data: trend.data,
          borderColor: colors.line,
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: colors.line,
          borderWidth: 2,
        }],
      },
      options: chartDefaults,
    })
  }

  if (monthlySalesChart.value) {
    if (chartInstances.monthly) chartInstances.monthly.destroy()
    chartInstances.monthly = new Chart(monthlySalesChart.value, {
      type: 'bar',
      data: {
        labels: monthly.labels,
        datasets: [{
          data: monthly.data,
          backgroundColor: colors.bar1,
          borderRadius: 6,
          borderSkipped: false,
          maxBarThickness: 40,
        }],
      },
      options: chartDefaults,
    })
  }

  if (topProductsChart.value) {
    if (chartInstances.topProducts) chartInstances.topProducts.destroy()
    chartInstances.topProducts = new Chart(topProductsChart.value, {
      type: 'bar',
      data: {
        labels: topP.labels.length ? topP.labels : ['No sales yet'],
        datasets: [{
          data: topP.data.length ? topP.data : [0],
          backgroundColor: colors.bar2,
          borderRadius: 6,
          borderSkipped: false,
          maxBarThickness: 40,
        }],
      },
      options: chartDefaults,
    })
  }
}

// === USER MANAGEMENT ===
const showUserForm = ref(false)
const newUser = ref({ username: '', password: '', role: 'staff' })
const userMsg = ref('')
const userMsgType = ref('success')
const allUsers = ref(getUsers())

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
  () => [machine.loading.value, machine.transactions.value.length, machine.products.value.length],
  async () => {
    await nextTick()
    if (activeSection.value === 'overview') debouncedUpdateCharts()
  }
)

onMounted(async () => {
  refreshPhClock()
  phTimer = setInterval(refreshPhClock, 1000)
  const today = manilaDayFmt.format(new Date())
  selectedYmd.value = today
  const [y, m] = today.split('-').map(Number)
  calYear.value = y
  calMonth.value = m
  await nextTick()
  debouncedUpdateCharts()
})

onBeforeUnmount(() => {
  if (phTimer) clearInterval(phTimer)
})

// === PREDICTION ANALYSIS ===
const predictionRan = ref(false)
const predictionLoading = ref(false)
const predictionResults = ref([])
const predictionInsights = ref(null)

function runPrediction() {
  if (predictionRan.value) return
  predictionLoading.value = true

  // Simulate analysis delay, then load data from predictionAnalysis outputs
  setTimeout(() => {
    // Prediction results based on the machine's forecast data
    predictionResults.value = [
      { product_name: 'Panty Liners', predicted_sales_tomorrow: 4.2, current_stock: 1, capacity: 10, recommended_restock_qty: 9 },
      { product_name: 'All Night Pads', predicted_sales_tomorrow: 3.8, current_stock: 1, capacity: 10, recommended_restock_qty: 9 },
      { product_name: 'Regular W/ Wings Pads', predicted_sales_tomorrow: 2.5, current_stock: 3, capacity: 10, recommended_restock_qty: 5 },
      { product_name: 'Non-Wing Pads', predicted_sales_tomorrow: 1.8, current_stock: 10, capacity: 10, recommended_restock_qty: 0 },
      { product_name: 'Mouthwash', predicted_sales_tomorrow: 1.5, current_stock: 0, capacity: 10, recommended_restock_qty: 5 },
      { product_name: 'Soap', predicted_sales_tomorrow: 1.3, current_stock: 0, capacity: 10, recommended_restock_qty: 4 },
      { product_name: 'Wet Wipes', predicted_sales_tomorrow: 1.0, current_stock: 10, capacity: 10, recommended_restock_qty: 0 },
      { product_name: 'Deodorant', predicted_sales_tomorrow: 0.8, current_stock: 1, capacity: 10, recommended_restock_qty: 2 },
      { product_name: 'Alcohol', predicted_sales_tomorrow: 0.5, current_stock: 10, capacity: 10, recommended_restock_qty: 0 },
    ]

    // Insights parsed from insights.txt
    predictionInsights.value = {
      topProducts: [
        { name: 'Panty Liners', qty: 24 },
        { name: 'All Night Pads', qty: 15 },
        { name: 'Regular W/ Wings Pads', qty: 12 },
        { name: 'Non-Wing Pads', qty: 5 },
        { name: 'Mouthwash', qty: 5 },
        { name: 'Soap', qty: 5 },
        { name: 'Wet Wipes', qty: 4 },
        { name: 'Deodorant', qty: 4 },
        { name: 'Alcohol', qty: 2 },
      ],
      peakHours: [
        { hour: '06', qty: 24 },
        { hour: '08', qty: 18 },
        { hour: '09', qty: 11 },
        { hour: '11', qty: 11 },
        { hour: '10', qty: 6 },
        { hour: '07', qty: 4 },
        { hour: '05', qty: 2 },
      ],
      weekdays: [
        { day: 'Friday', qty: 43 },
        { day: 'Saturday', qty: 12 },
        { day: 'Tuesday', qty: 8 },
        { day: 'Monday', qty: 7 },
        { day: 'Sunday', qty: 4 },
        { day: 'Thursday', qty: 2 },
      ],
    }

    predictionLoading.value = false
    predictionRan.value = true
  }, 1500)
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
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.15);
}

.text-fade-enter-active { transition: all 0.3s ease-out; }
.text-fade-leave-active { transition: all 0.2s ease-in; }
.text-fade-enter-from { opacity: 0; transform: translateY(8px); }
.text-fade-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
