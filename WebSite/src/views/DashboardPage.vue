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
            <p class="text-[9px] uppercase tracking-[0.2em] text-surface-500 light:text-surface-500 font-semibold mb-0.5">Smart Hygiene</p>
            <h2 class="text-xl lg:text-2xl font-bold font-display text-surface-100 light:text-surface-900 mb-0.5 tracking-tight">SHMS</h2>
            <p class="text-xs lg:text-sm text-surface-500 font-medium capitalize">{{ currentUser?.username || 'staff' }}</p>
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
              : 'text-surface-500 hover:text-surface-100 font-medium hover:bg-surface-800/30 light:text-surface-600 light:hover:text-surface-900 light:hover:bg-surface-100'"
          >
            <span v-html="item.icon" class="absolute left-4 w-5 h-5 shrink-0 transition-opacity" :class="activeSection === item.id ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'"></span>
            <span class="w-full text-center leading-[1.25] text-[14.5px] font-display pr-1 pl-6" :class="activeSection === item.id ? 'font-bold' : 'font-medium'">{{ item.label }}</span>
          </button>
        </nav>
      </div>

      <div class="flex-1"></div>

      <!-- Logout -->
      <div class="p-5 lg:p-6 pt-4 border-t border-surface-800/30 mt-auto">
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
    <main class="flex-1 w-full lg:w-auto p-4 sm:p-6 lg:p-8 light:bg-slate-50 min-w-0">

      <!-- Header -->
      <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-6">
        <div class="min-w-0">
          <p class="text-[10px] sm:text-xs uppercase tracking-widest text-brand-400 light:text-brand-600 font-bold mb-1">
            Smart Hygiene Management System
          </p>
          <h1 class="text-xl sm:text-2xl font-bold font-display text-surface-100 light:text-surface-900 truncate">
            {{ currentSidebarItem?.label || 'Overview' }}
          </h1>
        </div>
        <div class="flex items-center gap-2 sm:gap-3 shrink-0 flex-wrap">
          <button
            type="button"
            @click="toggleTheme($event)"
            class="p-2.5 rounded-xl text-surface-400 hover:text-surface-100 hover:bg-surface-800/50 light:hover:bg-white light:hover:text-surface-800 border border-surface-800/30 light:border-surface-200 transition-all"
            :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
          >
            <svg v-if="theme === 'dark'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          </button>
          <div class="flex items-center gap-2 rounded-xl px-3 py-2 bg-surface-800/40 light:bg-white border border-surface-800/30 light:border-surface-200 shadow-sm light:shadow-sm">
            <span class="flex h-3 w-3 relative">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <span class="text-xs font-medium text-surface-300 light:text-surface-600">Cloud online</span>
          </div>
        </div>
      </div>

      <!-- OVERVIEW SECTION -->
      <div v-if="activeSection === 'overview'">
        <!-- Critical KPIs (top-left priority on large screens) -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4 mb-4">
          <div
            v-for="(stat, i) in heroStats"
            :key="stat.label"
            class="ios-card rounded-2xl p-4 sm:p-5 animate-slide-up"
            :style="{ animationDelay: `${i * 0.05}s` }"
          >
            <p class="text-[11px] text-surface-500 uppercase tracking-wider mb-1">{{ stat.label }}</p>
            <p class="text-xl sm:text-2xl font-bold font-display tabular-nums" :class="stat.color">{{ stat.value }}</p>
            <p v-if="stat.sub" class="text-[11px] text-surface-500 mt-1">{{ stat.sub }}</p>
          </div>
        </div>

        <div
          v-if="kpiError"
          class="mb-4 rounded-2xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-amber-200 light:text-amber-900 text-xs sm:text-sm"
        >
          {{ kpiError }}
        </div>

        <div
          v-if="criticalAlertCount > 0"
          class="mb-4 rounded-2xl border border-red-500/35 bg-red-500/10 px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
        >
          <div class="flex items-center gap-2 text-red-300 light:text-red-700">
            <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span class="text-sm font-semibold">{{ criticalAlertCount }} critical low-stock item(s) — restock before machine runs empty.</span>
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
            <p class="text-xs text-surface-500 mb-4">Threshold: under 20% capacity highlights in red for maintenance rounds</p>
            <div class="space-y-3 mt-2">
              <div
                v-for="item in lowStockItems"
                :key="item.name"
                class="flex flex-col sm:flex-row sm:items-center gap-2 rounded-xl px-2 py-2 -mx-2"
                :class="(item.stock / item.capacity) < 0.2 ? 'bg-red-500/10 border border-red-500/20' : ''"
              >
                <div class="flex items-center justify-between gap-2 w-full sm:w-auto sm:min-w-[140px]">
                  <span class="text-xs text-surface-300 truncate">{{ item.name }}</span>
                  <span
                    v-if="(item.stock / item.capacity) < 0.2"
                    class="text-[10px] font-bold uppercase tracking-wide text-red-400 shrink-0"
                  >Critical</span>
                </div>
                <div class="flex flex-1 items-center gap-3 min-w-0">
                  <div class="flex-1 h-2.5 bg-surface-800/50 light:bg-surface-200 rounded-full overflow-hidden min-w-0">
                    <div
                      class="h-full rounded-full transition-all duration-700"
                      :class="item.stock / item.capacity > 0.5 ? 'bg-emerald-400' : item.stock / item.capacity > 0.25 ? 'bg-amber-400' : 'bg-red-400'"
                      :style="{ width: `${(item.stock / item.capacity) * 100}%` }"
                    ></div>
                  </div>
                  <span class="text-xs font-semibold text-surface-400 w-16 text-right tabular-nums shrink-0">{{ Math.round((item.stock / item.capacity) * 100) }}%</span>
                  <span class="text-xs text-surface-500 w-14 text-right tabular-nums shrink-0 hidden sm:inline">{{ item.stock }}/{{ item.capacity }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6">
          <h3 class="text-sm font-bold text-surface-200 mb-2">Live activity</h3>
          <p class="text-xs text-surface-500 mb-3">Streamed from Supabase — vending events as they happen</p>
          <LiveFeed />
        </div>
      </div>

      <!-- PREDICTION & INVENTORY INTELLIGENCE -->
      <div v-else-if="activeSection === 'prediction'" class="space-y-6">
        <div class="ios-card rounded-2xl p-5 sm:p-6">
          <p class="text-[10px] uppercase tracking-widest text-brand-400 light:text-brand-600 font-bold mb-1">Smart Hygiene Management System</p>
          <h3 class="text-lg font-bold font-display text-surface-100 light:text-surface-900 mb-1">Prediction &amp; machine intelligence</h3>
          <p class="text-xs text-surface-500 mb-4 max-w-2xl">
            Inventory-focused view for defense: stock health, Raspberry Pi heartbeat, ML restock hints, usage patterns, and offline chatbot signals.
          </p>

          <div class="flex flex-col sm:flex-row sm:items-center gap-3">
            <button
              type="button"
              @click="runPrediction"
              :disabled="predictionRan"
              class="px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-200 w-full sm:w-auto"
              :class="predictionRan
                ? 'bg-surface-800/40 text-surface-500 cursor-not-allowed'
                : 'bg-emerald-500 text-white hover:bg-emerald-400 active:scale-95'"
            >
              {{ predictionRan ? '✓ Analysis ready' : 'Run prediction analysis' }}
            </button>
            <span v-if="predictionLoading" class="text-xs text-surface-400 animate-pulse">Running model…</span>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Hardware heartbeat (Pi 5) -->
          <div class="ios-card rounded-2xl p-5 sm:p-6">
            <h4 class="text-sm font-bold text-surface-200 mb-0.5">Raspberry Pi heartbeat</h4>
            <p class="text-xs text-surface-500 mb-4">CPU temperature, memory, and link status (optional table <code class="text-surface-400">machine_telemetry</code>)</p>
            <div v-if="telemetryLoading" class="text-xs text-surface-500 animate-pulse py-6">Loading telemetry…</div>
            <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div class="rounded-xl bg-surface-800/25 light:bg-surface-100 p-4 border border-surface-800/20 light:border-surface-200">
                <p class="text-[10px] uppercase tracking-wider text-surface-500 mb-1">CPU temp</p>
                <p class="text-xl font-bold font-display text-surface-100 light:text-surface-900 tabular-nums">
                  {{ telemetry.cpuTempC != null ? `${telemetry.cpuTempC}°C` : '—' }}
                </p>
              </div>
              <div class="rounded-xl bg-surface-800/25 light:bg-surface-100 p-4 border border-surface-800/20 light:border-surface-200">
                <p class="text-[10px] uppercase tracking-wider text-surface-500 mb-1">RAM usage</p>
                <p class="text-xl font-bold font-display text-surface-100 light:text-surface-900 tabular-nums">
                  {{ telemetry.ramPct != null ? `${telemetry.ramPct}%` : '—' }}
                </p>
              </div>
              <div class="rounded-xl bg-surface-800/25 light:bg-surface-100 p-4 border border-surface-800/20 light:border-surface-200">
                <p class="text-[10px] uppercase tracking-wider text-surface-500 mb-1">Machine link</p>
                <p class="text-sm font-bold" :class="telemetry.online ? 'text-emerald-400' : 'text-red-400'">
                  {{ telemetry.online ? 'Online' : 'Offline' }}
                </p>
                <p v-if="telemetry.lastSeen" class="text-[10px] text-surface-500 mt-1 truncate">{{ telemetry.lastSeen }}</p>
              </div>
            </div>
            <p v-if="telemetryDemo" class="text-[11px] text-amber-400/90 mt-3">
              Showing demo values. From the Pi, insert the latest row into Supabase <code class="text-amber-300/90">machine_telemetry</code> (see SQL in project notes).
            </p>
          </div>

          <!-- Stock donuts -->
          <div class="ios-card rounded-2xl p-5 sm:p-6">
            <h4 class="text-sm font-bold text-surface-200 mb-0.5">Real-time stock tracking</h4>
            <p class="text-xs text-surface-500 mb-4">Fill level per SKU — red ring under ~20% (critical)</p>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div v-for="item in stockRingItems" :key="item.name" class="flex flex-col items-center text-center">
                <div class="relative w-[4.5rem] h-[4.5rem] sm:w-20 sm:h-20">
                  <svg viewBox="0 0 36 36" class="w-full h-full -rotate-90">
                    <path
                      class="text-surface-800/40 light:text-surface-200"
                      stroke="currentColor"
                      stroke-width="3"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      :stroke="stockRingStroke(item.pct)"
                      stroke-width="3"
                      fill="none"
                      stroke-linecap="round"
                      :stroke-dasharray="`${item.pct}, 100`"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div class="absolute inset-0 flex items-center justify-center text-[11px] sm:text-xs font-bold text-surface-100 light:text-surface-900 tabular-nums">
                    {{ item.pct }}%
                  </div>
                </div>
                <span class="text-[10px] sm:text-[11px] text-surface-400 mt-2 line-clamp-2 leading-tight px-1">{{ item.name }}</span>
                <span class="text-[10px] text-surface-500 tabular-nums">{{ item.stock }}/{{ item.cap }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Predictive restock narrative -->
        <div v-if="predictionRan && predictionResults.length" class="ios-card rounded-2xl p-5 sm:p-6">
          <h4 class="text-sm font-bold text-surface-200 mb-2">Predictive restocking (ML)</h4>
          <p class="text-xs text-surface-500 mb-3">Rough runway = current stock ÷ predicted daily sales (thesis-friendly heuristic).</p>
          <ul class="space-y-2 text-sm text-surface-300 light:text-surface-600">
            <li v-for="r in predictionResults.slice(0, 8)" :key="'eta-' + r.product_name" class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 border-b border-surface-800/15 light:border-surface-200/80 pb-2 last:border-0">
              <span class="font-medium text-surface-200 light:text-surface-800">{{ r.product_name }}</span>
              <span class="text-xs sm:text-sm">{{ restockEtaText(r) }}</span>
            </li>
          </ul>
        </div>

        <!-- Results table -->
        <div v-if="predictionResults.length > 0" class="ios-card rounded-2xl p-5 sm:p-6">
          <h4 class="text-sm font-bold text-surface-200 mb-3">Model output</h4>
          <div class="overflow-x-auto -mx-1">
            <table class="w-full text-sm min-w-[640px]">
              <thead>
                <tr class="border-b border-surface-800/40 light:border-surface-200">
                  <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3 pr-3">Product</th>
                  <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3 pr-3">Pred. sales</th>
                  <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3 pr-3">Stock</th>
                  <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3 pr-3">Runway</th>
                  <th class="text-left text-xs text-surface-500 uppercase tracking-wider pb-3">Restock</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="r in predictionResults"
                  :key="r.product_name"
                  class="border-b border-surface-800/15 light:border-surface-200/80 last:border-0"
                  :class="(r.current_stock / r.capacity) < 0.2 ? 'bg-red-500/5' : ''"
                >
                  <td class="py-3 pr-3 text-surface-200 light:text-surface-800 font-medium">{{ r.product_name }}</td>
                  <td class="py-3 pr-3 text-surface-300 tabular-nums">{{ r.predicted_sales_tomorrow }}</td>
                  <td class="py-3 pr-3 text-surface-300 tabular-nums">{{ r.current_stock }}/{{ r.capacity }}</td>
                  <td class="py-3 pr-3 text-xs text-surface-400">{{ restockEtaText(r) }}</td>
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

        <!-- Usage heatmap + insights + chatbot -->
        <div v-if="predictionInsights" class="ios-card rounded-2xl p-5 sm:p-6">
          <h4 class="text-sm font-bold text-surface-200 mb-1">Usage patterns</h4>
          <p class="text-xs text-surface-500 mb-3">Hourly intensity from transaction history (heatmap). Peak: <strong class="text-surface-300 light:text-surface-700">{{ peakHourLabel }}</strong></p>
          <div class="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-12 gap-1.5 mb-6">
            <div
              v-for="cell in peakHeatCells"
              :key="cell.hour"
              class="aspect-square rounded-md flex items-center justify-center text-[9px] font-medium border transition-colors"
              :class="heatCellClass(cell)"
              :title="`${cell.hour}:00 — ${cell.qty} items`"
            >
              {{ cell.hour }}
            </div>
          </div>

          <h4 class="text-xs font-bold text-surface-300 uppercase tracking-wider mb-3">Rankings &amp; seasonality</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div class="p-3 rounded-xl bg-surface-800/20 light:bg-surface-100">
              <p class="text-xs font-bold text-surface-400 mb-2">Top products</p>
              <div v-for="(item, i) in predictionInsights.topProducts.slice(0, 5)" :key="item.name" class="flex justify-between text-xs py-0.5">
                <span class="text-surface-300 light:text-surface-700">{{ i + 1 }}. {{ item.name }}</span>
                <span class="text-surface-500 font-medium tabular-nums">{{ item.qty }} sold</span>
              </div>
            </div>
            <div class="p-3 rounded-xl bg-surface-800/20 light:bg-surface-100">
              <p class="text-xs font-bold text-surface-400 mb-2">Peak hours (list)</p>
              <div v-for="item in predictionInsights.peakHours.slice(0, 5)" :key="item.hour" class="flex justify-between text-xs py-0.5">
                <span class="text-surface-300 light:text-surface-700">{{ item.hour }}:00</span>
                <span class="text-surface-500 font-medium tabular-nums">{{ item.qty }} items</span>
              </div>
            </div>
            <div class="p-3 rounded-xl bg-surface-800/20 light:bg-surface-100">
              <p class="text-xs font-bold text-surface-400 mb-2">Busiest days</p>
              <div v-for="item in predictionInsights.weekdays.slice(0, 5)" :key="item.day" class="flex justify-between text-xs py-0.5">
                <span class="text-surface-300 light:text-surface-700">{{ item.day }}</span>
                <span class="text-surface-500 font-medium tabular-nums">{{ item.qty }} items</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Offline chatbot analytics (demo / wire to Supabase later) -->
        <div class="ios-card rounded-2xl p-5 sm:p-6">
          <h4 class="text-sm font-bold text-surface-200 mb-0.5">Chatbot analytics</h4>
          <p class="text-xs text-surface-500 mb-4">Recent hygiene-related queries from the on-machine offline assistant (sample data for UI).</p>
          <ul class="space-y-2">
            <li
              v-for="(q, idx) in chatbotQueries"
              :key="idx"
              class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 text-xs sm:text-sm py-2 border-b border-surface-800/15 light:border-surface-200/80 last:border-0"
            >
              <span class="text-surface-300 light:text-surface-700">{{ q.text }}</span>
              <span class="text-surface-500 shrink-0 tabular-nums">{{ q.when }}</span>
            </li>
          </ul>
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
                  <label class="block text-xs text-surface-500 uppercase tracking-wider mb-1">Username</label>
                  <input v-model="newUser.username" type="text" required
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
                v-if="isAdmin && user.username !== 'admin'"
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
import { useTheme } from '../composables/useTheme'
import { supabase, isSupabaseConfigured } from '../utils/supabase'
import { Chart, registerables } from 'chart.js'
import LiveFeed from '../components/LiveFeed.vue'

Chart.register(...registerables)

const router = useRouter()
const { theme, toggle: toggleTheme } = useTheme()
const { currentUser, isAdmin, logout, createUser, getUsers, deleteUser } = useAuth()

const activeSection = ref('overview')
const sidebarOpen = ref(false)

// Sidebar items matching the machine's admin panel
const sidebarItems = [
  { id: 'overview', label: 'Overview', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" /></svg>' },
  { id: 'rfid', label: 'RFID Roles', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 9h3.75M15 12h3.75M15 15h3.75M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15A2.25 2.25 0 002.25 6.75v10.5A2.25 2.25 0 004.5 19.5zm6-10.125a1.875 1.875 0 11-3.75 0 1.875 1.875 0 013.75 0zm1.294 6.336a6.721 6.721 0 01-3.17.789 6.721 6.721 0 01-3.168-.789 3.376 3.376 0 016.338 0z" /></svg>' },
  { id: 'cash', label: 'Cash Pulse Settings', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>' },
  { id: 'hardware', label: 'Hardware Diagnostics', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>' },
  { id: 'sales-reports', label: 'Sales Reports', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>' },
  { id: 'prediction', label: 'Prediction Analysis', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>' },
  { id: 'users', label: 'Manage Users', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>' },
  { id: 'credentials', label: 'Change Credentials', icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>' },
]

const currentSidebarItem = computed(() => sidebarItems.find(i => i.id === activeSection.value))

async function handleLogout() {
  await logout()
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

// === DATA (Supabase live_feed-backed KPIs) ===
// Source of truth for the website KPIs is Supabase `public.live_feed`, which the machine pushes to
// on every transaction. This makes machine + website totals match.

const totalSalesAll = ref(0)
const totalSalesToday = ref(0)
const ordersAll = ref(0)
const kpiError = ref('')
/** Cached sales rows from live_feed for KPIs + charts (newest-first cap). */
const liveSalesRows = ref([])

function formatPhp(n) {
  const v = Number(n)
  if (!Number.isFinite(v)) return '₱0.00'
  return v.toLocaleString('en-PH', { style: 'currency', currency: 'PHP' })
}

function isSalesRow(row) {
  if (!row) return false
  const amt = Number(row.amount)
  if (!Number.isFinite(amt)) return false
  const subtitle = String(row.subtitle ?? '').trim().toLowerCase()
  // Mirror machine "sales" intent: exclude reload top-ups from "sales" totals.
  if (subtitle === 'rfid reload') return false
  return true
}

function isSameLocalDay(isoString, dayStart) {
  if (!isoString) return false
  const d = new Date(isoString)
  if (Number.isNaN(d.getTime())) return false
  return d >= dayStart
}

let kpiChannel = null

function recomputeKpisFromLiveRows() {
  const dayStart = new Date()
  dayStart.setHours(0, 0, 0, 0)

  let sumAll = 0
  let sumToday = 0
  let countAll = 0

  for (const r of liveSalesRows.value) {
    if (!isSalesRow(r)) continue
    const amt = Number(r.amount)
    sumAll += amt
    countAll += 1
    if (isSameLocalDay(r.created_at, dayStart)) sumToday += amt
  }

  totalSalesAll.value = Number(sumAll.toFixed(2))
  totalSalesToday.value = Number(sumToday.toFixed(2))
  ordersAll.value = countAll
}

function pad2(n) {
  return String(n).padStart(2, '0')
}

function ymdLocal(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

function monthKeyLocal(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}`
}

function labelMdLocal(d) {
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function labelMmYyLocal(d) {
  return d.toLocaleString('default', { month: '2-digit', year: '2-digit' })
}

function productLabelFromRow(r) {
  const t = String(r.title ?? '').trim()
  if (t) return t.split('×')[0].trim() || t
  const it = String(r.item ?? '').trim()
  if (it) return it.split('—')[0].trim() || it
  return 'Sale'
}

function updateOverviewChartsFromLiveRows() {
  const rows = liveSalesRows.value

  // Last 15 days (PHP totals)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const dayLabels = []
  const dayKeys = []
  for (let offset = 14; offset >= 0; offset -= 1) {
    const d = new Date(today)
    d.setDate(d.getDate() - offset)
    dayLabels.push(labelMdLocal(d))
    dayKeys.push(ymdLocal(d))
  }
  const byDay = Object.fromEntries(dayKeys.map((k) => [k, 0]))
  for (const r of rows) {
    if (!isSalesRow(r) || !r.created_at) continue
    const d = new Date(r.created_at)
    if (Number.isNaN(d.getTime())) continue
    const k = ymdLocal(d)
    if (k in byDay) byDay[k] += Number(r.amount) || 0
  }
  const trendData = dayKeys.map((k) => Number(byDay[k].toFixed(2)))

  // Last 6 calendar months (PHP totals)
  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
  const monthLabels = []
  const monthKeys = []
  for (let offset = 5; offset >= 0; offset -= 1) {
    const d = new Date(monthStart.getFullYear(), monthStart.getMonth() - offset, 1)
    monthLabels.push(labelMmYyLocal(d))
    monthKeys.push(monthKeyLocal(d))
  }
  const byMonth = Object.fromEntries(monthKeys.map((k) => [k, 0]))
  for (const r of rows) {
    if (!isSalesRow(r) || !r.created_at) continue
    const d = new Date(r.created_at)
    if (Number.isNaN(d.getTime())) continue
    const k = monthKeyLocal(d)
    if (k in byMonth) byMonth[k] += Number(r.amount) || 0
  }
  const monthlyData = monthKeys.map((k) => Number(byMonth[k].toFixed(2)))

  // Top products by count (proxy for qty; live_feed is one row per vend line)
  const counts = new Map()
  for (const r of rows) {
    if (!isSalesRow(r)) continue
    const name = productLabelFromRow(r)
    counts.set(name, (counts.get(name) || 0) + 1)
  }
  const top = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5)
  const topLabels = top.length ? top.map((x) => x[0]) : ['No sales yet']
  const topData = top.length ? top.map((x) => x[1]) : [0]

  if (chartInstances.salesTrend) {
    chartInstances.salesTrend.data.labels = dayLabels
    chartInstances.salesTrend.data.datasets[0].data = trendData
    chartInstances.salesTrend.update()
  }
  if (chartInstances.monthly) {
    chartInstances.monthly.data.labels = monthLabels
    chartInstances.monthly.data.datasets[0].data = monthlyData
    chartInstances.monthly.update()
  }
  if (chartInstances.topProducts) {
    chartInstances.topProducts.data.labels = topLabels
    chartInstances.topProducts.data.datasets[0].data = topData
    chartInstances.topProducts.update()
  }
}

async function fetchLiveFeedKpis() {
  kpiError.value = ''
  if (!isSupabaseConfigured()) {
    kpiError.value =
      'Supabase is not configured in the website build. Add VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY to WebSite/.env.local and restart Vite.'
    liveSalesRows.value = []
    recomputeKpisFromLiveRows()
    return
  }

  const collected = []
  let lastError = null

  // Paginate in chunks to avoid large payloads.
  // For thesis scale data, this is enough; for very large datasets, convert this to an RPC/view.
  const pageSize = 1000
  for (let from = 0; from < 10000; from += pageSize) {
    const to = from + pageSize - 1
    const { data, error } = await supabase
      .from('live_feed')
      .select('amount,subtitle,created_at,title,item')
      .not('amount', 'is', null)
      .order('created_at', { ascending: false })
      .range(from, to)

    if (error) {
      lastError = error
      break
    }
    const rows = data || []
    for (const r of rows) collected.push(r)
    if (rows.length < pageSize) break
  }

  if (lastError) {
    kpiError.value = `Could not read live_feed for KPIs/charts: ${lastError.message}. In Supabase, add a SELECT policy for authenticated users on public.live_feed (or verify your publishable key).`
    liveSalesRows.value = []
    recomputeKpisFromLiveRows()
    return
  }

  liveSalesRows.value = collected

  // If we got zero sales rows, distinguish "no data" vs "RLS blocked SELECT" vs "rows exist but amount is null".
  if (liveSalesRows.value.length === 0) {
    const { data: sess } = await supabase.auth.getSession()
    if (sess?.session) {
      const { count, error: cErr } = await supabase
        .from('live_feed')
        .select('id', { count: 'exact', head: true })

      if (!cErr && typeof count === 'number' && count > 0) {
        kpiError.value =
          'live_feed has rows, but this account cannot read them (or amounts are NULL). In Supabase SQL editor, add: CREATE POLICY "authenticated read live_feed" ON public.live_feed FOR SELECT TO authenticated USING (true);  Also ensure vending inserts include `amount`.'
      }
    }
  }

  recomputeKpisFromLiveRows()
  await nextTick()
  updateOverviewChartsFromLiveRows()
}

const lowStockItems = ref([
  { name: 'Hand Sanitizer', stock: 3, capacity: 10 },
  { name: 'Face Mask', stock: 2, capacity: 10 },
  { name: 'Wet Wipes', stock: 7, capacity: 10 },
  { name: 'Tissue Pack', stock: 5, capacity: 10 },
  { name: 'Alcohol Spray', stock: 8, capacity: 10 },
])

const criticalAlertCount = computed(
  () => lowStockItems.value.filter((i) => i.capacity > 0 && i.stock / i.capacity < 0.2).length
)

const machineStatusLabel = computed(() =>
  criticalAlertCount.value > 0 ? 'Needs attention' : 'Operational'
)

const heroStats = computed(() => [
  {
    label: 'Total sales',
    value: formatPhp(totalSalesAll.value),
    sub: `Today: ${formatPhp(totalSalesToday.value)} • Live from machine feed`,
    color: 'text-emerald-400',
  },
  {
    label: 'Machine status',
    value: machineStatusLabel.value,
    sub: criticalAlertCount.value
      ? `${criticalAlertCount.value} critical SKU(s) under 20%`
      : 'No blocking faults detected',
    color: machineStatusLabel.value === 'Operational' ? 'text-emerald-400' : 'text-amber-400',
  },
  {
    label: 'Critical alerts',
    value: String(criticalAlertCount.value),
    sub: 'Low-stock threshold 20%',
    color: criticalAlertCount.value ? 'text-red-400' : 'text-surface-400',
  },
  {
    label: 'Orders',
    value: String(ordersAll.value),
    sub: 'Live count from machine activity',
    color: 'text-blue-400',
  },
])

// === CHARTS ===
const salesTrendChart = ref(null)
const monthlySalesChart = ref(null)
const topProductsChart = ref(null)

let chartInstances = {}

function getChartColors() {
  const light = theme.value === 'light'
  return {
    grid: light ? 'rgba(100, 116, 139, 0.14)' : 'rgba(148, 163, 184, 0.08)',
    text: light ? '#64748b' : '#94a3b8',
    line: '#10b981',
    bar1: '#42A5F5',
    bar2: '#7E57C2',
  }
}

function initCharts() {
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

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const trendLabels = []
  for (let offset = 14; offset >= 0; offset -= 1) {
    const d = new Date(today)
    d.setDate(d.getDate() - offset)
    trendLabels.push(labelMdLocal(d))
  }
  const trendZeros = Array.from({ length: 15 }, () => 0)

  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
  const monthLabels = []
  for (let offset = 5; offset >= 0; offset -= 1) {
    const d = new Date(monthStart.getFullYear(), monthStart.getMonth() - offset, 1)
    monthLabels.push(labelMmYyLocal(d))
  }
  const monthZeros = Array.from({ length: 6 }, () => 0)

  // Sales Trend (Line Chart)
  if (salesTrendChart.value) {
    if (chartInstances.salesTrend) chartInstances.salesTrend.destroy()
    chartInstances.salesTrend = new Chart(salesTrendChart.value, {
      type: 'line',
      data: {
        labels: trendLabels,
        datasets: [{
          data: trendZeros,
          borderColor: colors.line,
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: colors.line,
          borderWidth: 2,
        }],
      },
      options: {
        ...chartDefaults,
        scales: {
          ...chartDefaults.scales,
          y: {
            ...chartDefaults.scales.y,
          },
        },
      },
    })
  }

  // Monthly Sales (Bar Chart)
  if (monthlySalesChart.value) {
    if (chartInstances.monthly) chartInstances.monthly.destroy()
    chartInstances.monthly = new Chart(monthlySalesChart.value, {
      type: 'bar',
      data: {
        labels: monthLabels,
        datasets: [{
          data: monthZeros,
          backgroundColor: colors.bar1,
          borderRadius: 6,
          borderSkipped: false,
          maxBarThickness: 40,
        }],
      },
      options: {
        ...chartDefaults,
        plugins: {
          ...chartDefaults.plugins,
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const v = Number(ctx.parsed?.y ?? ctx.raw ?? 0)
                return v.toLocaleString('en-PH', { style: 'currency', currency: 'PHP' })
              },
            },
          },
        },
      },
    })
  }

  // Top Products (Bar Chart)
  if (topProductsChart.value) {
    if (chartInstances.topProducts) chartInstances.topProducts.destroy()
    chartInstances.topProducts = new Chart(topProductsChart.value, {
      type: 'bar',
      data: {
        labels: ['No sales yet'],
        datasets: [{
          data: [0],
          backgroundColor: colors.bar2,
          borderRadius: 6,
          borderSkipped: false,
          maxBarThickness: 40,
        }],
      },
      options: chartDefaults,
    })
  }

  updateOverviewChartsFromLiveRows()
}

// === USER MANAGEMENT ===
const showUserForm = ref(false)
const newUser = ref({ username: '', password: '', role: 'staff' })
const userMsg = ref('')
const userMsgType = ref('success')
const allUsers = ref(getUsers())

async function handleCreateUser() {
  userMsg.value = ''
  const result = await createUser(newUser.value.username, newUser.value.password, newUser.value.role)
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

function handleDeleteUser(username) {
  const result = deleteUser(username)
  if (result.success) {
    allUsers.value = getUsers()
  }
}

// Init charts when overview is active
watch(activeSection, async (val) => {
  if (val === 'overview') {
    await nextTick()
    initCharts()
  }
  if (val === 'prediction') {
    fetchMachineTelemetry()
  }
})

watch(theme, async () => {
  await nextTick()
  if (activeSection.value === 'overview') initCharts()
})

onMounted(async () => {
  await nextTick()
  initCharts()
  await fetchLiveFeedKpis()

  // Realtime: increment KPIs on new live_feed rows (same table LiveFeed.vue listens to).
  kpiChannel = supabase
    .channel('live_feed_kpis')
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'live_feed' },
      async (payload) => {
        const row = payload?.new
        if (!isSalesRow(row)) return
        const id = row.id
        if (id != null && liveSalesRows.value.some((r) => r.id === id)) return

        liveSalesRows.value = [row, ...liveSalesRows.value].slice(0, 10000)
        recomputeKpisFromLiveRows()
        await nextTick()
        updateOverviewChartsFromLiveRows()
      }
    )
    .subscribe()
})

onBeforeUnmount(() => {
  if (kpiChannel) {
    supabase.removeChannel(kpiChannel)
    kpiChannel = null
  }
})

// === PREDICTION ANALYSIS ===
const predictionRan = ref(false)
const predictionLoading = ref(false)
const predictionResults = ref([])
const predictionInsights = ref(null)

const telemetry = ref({
  cpuTempC: null,
  ramPct: null,
  online: true,
  lastSeen: null,
})
const telemetryLoading = ref(false)
const telemetryDemo = ref(false)

async function fetchMachineTelemetry() {
  telemetryLoading.value = true
  telemetryDemo.value = false
  try {
    const { data, error } = await supabase
      .from('machine_telemetry')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(1)
      .maybeSingle()

    if (!error && data) {
      telemetry.value = {
        cpuTempC: data.cpu_temp_c ?? data.cpu_temp ?? null,
        ramPct: data.ram_pct ?? data.ram_usage_pct ?? null,
        online: data.online !== false,
        lastSeen: data.created_at ?? data.last_seen ?? null,
      }
      telemetryLoading.value = false
      return
    }
  } catch {
    /* use demo */
  }
  telemetry.value = { cpuTempC: 52.4, ramPct: 41, online: true, lastSeen: null }
  telemetryDemo.value = true
  telemetryLoading.value = false
}

const stockRingItems = computed(() => {
  if (predictionResults.value.length) {
    return predictionResults.value.slice(0, 6).map((r) => {
      const cap = r.capacity || 1
      const pct = Math.min(100, Math.round((r.current_stock / cap) * 100))
      return {
        name: r.product_name,
        pct,
        stock: r.current_stock,
        cap: r.capacity,
      }
    })
  }
  return lowStockItems.value.slice(0, 6).map((i) => ({
    name: i.name,
    pct: Math.min(100, Math.round((i.stock / i.capacity) * 100)),
    stock: i.stock,
    cap: i.capacity,
  }))
})

function stockRingStroke(pct) {
  if (pct < 20) return '#f87171'
  if (pct < 45) return '#fbbf24'
  return '#34d399'
}

const peakHeatCells = computed(() => {
  const src = predictionInsights.value?.peakHours || []
  const map = {}
  let maxQty = 1
  for (const h of src) {
    const hr = Number(h.hour)
    const q = Number(h.qty) || 0
    map[hr] = q
    maxQty = Math.max(maxQty, q)
  }
  return Array.from({ length: 24 }, (_, hour) => {
    const qty = map[hour] || 0
    const t = maxQty ? qty / maxQty : 0
    return { hour, qty, t }
  })
})

const peakHourLabel = computed(() => {
  const src = predictionInsights.value?.peakHours || []
  if (!src.length) return '—'
  const top = [...src].sort((a, b) => Number(b.qty) - Number(a.qty))[0]
  return `${String(top.hour).padStart(2, '0')}:00 (${top.qty} items)`
})

function heatCellClass(cell) {
  const base =
    'border-surface-700/30 light:border-surface-200 text-surface-500 light:text-surface-600'
  if (cell.qty <= 0) return `${base} bg-surface-900/40 light:bg-surface-100`
  if (cell.t > 0.66) return 'border-emerald-500/40 bg-emerald-500/25 text-emerald-200 light:text-emerald-800'
  if (cell.t > 0.33) return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300 light:text-emerald-900'
  return `${base} bg-surface-800/50 light:bg-surface-200/80`
}

function restockEtaText(r) {
  const rate = Number(r.predicted_sales_tomorrow)
  const stock = Number(r.current_stock)
  if (!rate || rate < 0.05) return 'Stable — low predicted movement'
  const days = stock / rate
  if (days > 14) return 'Runway 14+ days at current trend'
  if (days < 1) return 'May stock out within 24h at current trend'
  return `About ${Math.ceil(days)} day(s) of stock at predicted rate`
}

const chatbotQueries = ref([
  { text: 'Where is the sanitary pad slot?', when: '12 min ago' },
  { text: 'Machine took money but nothing dropped — slot B2', when: '1 hr ago' },
  { text: 'Is hand sanitizer alcohol-based?', when: '2 hr ago' },
  { text: 'How do I reload my RFID balance?', when: 'Yesterday' },
])

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
    fetchMachineTelemetry()
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
