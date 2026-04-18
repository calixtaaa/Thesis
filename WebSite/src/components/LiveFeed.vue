<template>
  <div class="ios-card rounded-2xl p-5 sm:p-6">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-sm font-bold text-surface-200 mb-0.5">Live Feed</h3>
        <p class="text-xs text-surface-500">Real-time transactions</p>
      </div>
      <span class="text-[11px] px-2 py-1 rounded-lg bg-emerald-400/10 text-emerald-400 font-bold">LIVE</span>
    </div>

    <div v-if="configError" class="px-4 py-3 rounded-xl bg-amber-400/10 border border-amber-400/20 text-amber-300 text-xs">
      {{ configError }}
    </div>

    <div v-else class="space-y-2 max-h-72 overflow-auto pr-1">
      <div
        v-for="a in activities"
        :key="a._key"
        class="p-3 rounded-xl bg-surface-800/20 border border-surface-800/20 animate-fade-in-down"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-xs sm:text-sm text-surface-200 font-medium truncate">
              {{ a.title || a.item || 'Transaction' }}
            </p>
            <p class="text-[11px] text-surface-500 mt-0.5 truncate">
              {{ a.subtitle || a.slot || a.user || '' }}
            </p>
          </div>
          <div class="text-right shrink-0">
            <p class="text-xs font-bold text-emerald-400">
              {{ formatPhp(a.amount ?? a.price ?? a.total) }}
            </p>
            <p class="text-[11px] text-surface-500 mt-0.5">
              {{ formatTime(a.ts || a.createdAt) }}
            </p>
          </div>
        </div>
      </div>

      <p v-if="activities.length === 0" class="text-xs text-surface-500 text-center py-8">
        Waiting for live activity…
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { supabase, isSupabaseConfigured } from '../utils/supabase'

const activities = ref([])
const configError = ref('')

let channel = null
const seenKeys = new Set()

function rowToActivity(row) {
  if (!row) return null
  const ts = row.ts ?? (row.created_at ? new Date(row.created_at).getTime() : null)
  return {
    _key: row.id,
    title: row.title,
    item: row.item,
    subtitle: row.subtitle,
    slot: row.slot,
    user: row.user,
    amount: row.amount,
    price: row.price,
    total: row.total,
    ts,
    createdAt: row.created_at,
  }
}

function formatTime(ts) {
  if (ts == null || ts === '') return ''
  if (typeof ts === 'string' && Number.isNaN(Number(ts))) {
    const d = new Date(ts)
    return Number.isNaN(d.getTime()) ? '' : d.toLocaleString()
  }
  const d = new Date(Number(ts))
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString()
}

function formatPhp(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return ''
  return n.toLocaleString('en-PH', { style: 'currency', currency: 'PHP' })
}

onMounted(async () => {
  if (!isSupabaseConfigured()) {
    configError.value =
      'Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY to WebSite/.env.local and restart Vite.'
    return
  }

  const { data, error } = await supabase
    .from('live_feed')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(30)

  if (error) {
    configError.value = `Could not load live feed: ${error.message}`
    return
  }

  const rows = (data || []).map(rowToActivity).filter(Boolean)
  activities.value = rows
  activities.value.forEach((a) => seenKeys.add(a._key))

  channel = supabase
    .channel('live_feed_inserts')
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'live_feed' },
      (payload) => {
        const item = rowToActivity(payload.new)
        if (!item) return
        if (!seenKeys.has(item._key)) {
          activities.value.unshift(item)
          seenKeys.add(item._key)
        }
        activities.value = activities.value.slice(0, 30)
      }
    )
    .subscribe()
})

onBeforeUnmount(() => {
  if (channel) {
    supabase.removeChannel(channel)
    channel = null
  }
})
</script>

