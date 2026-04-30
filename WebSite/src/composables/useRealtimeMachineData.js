import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { supabase } from '../lib/supabaseClient'

export function useRealtimeMachineData() {
  const products = ref([])
  const transactions = ref([])
  const liveFeed = ref([])
  const lowStockProducts = ref([])
  const subscriberEmails = ref([])
  const bugReports = ref([])
  const loading = ref(true)
  const error = ref('')

  let channel = null

  // Batch expensive normalize work to avoid UI stutter on frequent realtime updates.
  let txNormalizeQueued = false
  let feedNormalizeQueued = false
  function queueMicrotaskSafe(fn) {
    try {
      if (typeof queueMicrotask === 'function') return queueMicrotask(fn)
    } catch (_) {
      // ignore
    }
    return Promise.resolve().then(fn)
  }
  function scheduleTxNormalize() {
    if (txNormalizeQueued) return
    txNormalizeQueued = true
    queueMicrotaskSafe(() => {
      txNormalizeQueued = false
      transactions.value = dedupeBy(transactions.value, txKey)
      if (transactions.value.length > 3000) transactions.value = transactions.value.slice(0, 3000)
    })
  }
  function scheduleFeedNormalize() {
    if (feedNormalizeQueued) return
    feedNormalizeQueued = true
    queueMicrotaskSafe(() => {
      feedNormalizeQueued = false
      liveFeed.value = dedupeBy(liveFeed.value, feedKey)
      if (liveFeed.value.length > 1000) liveFeed.value = liveFeed.value.slice(0, 1000)
    })
  }

  function txKey(row) {
    return row?.source_tx_id ?? row?.id
  }

  function feedKey(row) {
    const payload = row?.payload || {}
    const stable = payload?.source_tx_id ?? payload?.transaction_id
    if (stable != null && stable !== '') return `tx:${stable}`

    // Normalize created_at to seconds (different string formats can represent same moment)
    const rawCa = row?.created_at ?? ''
    let sec = ''
    try {
      const ms = Date.parse(rawCa)
      if (!Number.isNaN(ms)) sec = String(Math.floor(ms / 1000))
      else if (typeof rawCa === 'string') sec = rawCa.slice(0, 19) // 'YYYY-MM-DDTHH:MM:SS'
    } catch (_) {
      // ignore
    }

    const et = String(row?.event_type ?? '')

    // For sale events: dedupe by what the UI cares about (time-second + slot/product + qty + amount).
    if (et === 'sale') {
      const slot = payload?.slot_number ?? payload?.slot ?? ''
      const pid = payload?.product_id ?? ''
      const qty = payload?.quantity ?? row?.quantity ?? ''
      const amtNum = Number.isFinite(Number(payload?.total_amount ?? row?.total_amount))
        ? Number(payload?.total_amount ?? row?.total_amount)
        : 0
      const amtCents = Math.round(amtNum * 100)
      return `sale:${sec}|${pid}|${slot}|${qty}|${amtCents}`
    }

    // Other events: fallback fingerprint (keep message to avoid collapsing distinct events).
    const msg = String(row?.message ?? '')
    const qty2 = String(row?.quantity ?? '')
    const amt2 = String(row?.total_amount ?? '')
    const fp = `${sec}|${et}|${msg}|${qty2}|${amt2}`
    return fp !== '||||' ? fp : row?.id
  }

  function dedupeBy(list, keyFn) {
    const seen = new Set()
    const out = []
    for (const item of Array.isArray(list) ? list : []) {
      const k = keyFn(item)
      if (k === undefined || k === null) {
        out.push(item)
        continue
      }
      if (seen.has(k)) continue
      seen.add(k)
      out.push(item)
    }
    return out
  }

  async function loadInitial() {
    loading.value = true
    error.value = ''

    const [prodRes, txRes, feedRes, lowRes, mailRes, bugRes] = await Promise.all([
      supabase.from('products').select('*').order('slot_number', { ascending: true }),
      supabase
        .from('transactions')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(3000),
      supabase.from('live_feed').select('*').order('created_at', { ascending: false }).limit(1000),
      supabase.from('low_stock_products').select('*').order('slot_number', { ascending: true }).limit(200),
      supabase.from('emails').select('id, email, created_at, password').order('created_at', { ascending: false }).limit(500),
      supabase.from('bug_reports').select('*').order('created_at', { ascending: false }).limit(500),
    ])

    const { data: prod, error: prodErr } = prodRes
    const { data: tx, error: txErr } = txRes
    const { data: feed, error: feedErr } = feedRes
    const { data: low, error: lowErr } = lowRes
    const { data: mails, error: mailErr } = mailRes
    const { data: bugs, error: bugErr } = bugRes

    if (prodErr) error.value = prodErr.message
    if (txErr) error.value = error.value ? `${error.value}; ${txErr.message}` : txErr.message
    if (feedErr) {
      const msg = feedErr.message || String(feedErr)
      if (!/relation|does not exist|not find/i.test(msg)) {
        error.value = error.value ? `${error.value}; ${msg}` : msg
      }
      liveFeed.value = []
    } else {
      liveFeed.value = dedupeBy(Array.isArray(feed) ? feed : [], feedKey)
    }

    if (lowErr) {
      const msg = lowErr.message || String(lowErr)
      if (!/relation|does not exist|not find/i.test(msg)) {
        error.value = error.value ? `${error.value}; ${msg}` : msg
      }
      lowStockProducts.value = []
    } else {
      lowStockProducts.value = Array.isArray(low) ? low : []
    }
    if (mailErr) {
      // Missing table or RLS: keep dashboard usable; surface message once
      const msg = mailErr.message || String(mailErr)
      if (!/relation|does not exist|not find/i.test(msg)) {
        error.value = error.value ? `${error.value}; ${msg}` : msg
      }
      subscriberEmails.value = []
    } else {
      subscriberEmails.value = Array.isArray(mails) ? mails : []
    }

    if (bugErr) {
      const msg = bugErr.message || String(bugErr)
      if (!/relation|does not exist|not find/i.test(msg)) {
        error.value = error.value ? `${error.value}; ${msg}` : msg
      }
      bugReports.value = []
    } else {
      bugReports.value = Array.isArray(bugs) ? bugs : []
    }

    products.value = Array.isArray(prod) ? prod : []
    transactions.value = dedupeBy(Array.isArray(tx) ? tx : [], txKey)
    loading.value = false
  }

  function upsertLocal(listRef, row, key = 'id') {
    const idx = listRef.value.findIndex((r) => r?.[key] === row?.[key])
    if (idx >= 0) listRef.value.splice(idx, 1, row)
    else listRef.value.unshift(row)
  }

  function removeLocal(listRef, row, key = 'id') {
    const idx = listRef.value.findIndex((r) => r?.[key] === row?.[key])
    if (idx >= 0) listRef.value.splice(idx, 1)
  }

  function subscribeRealtime() {
    if (channel) return

    channel = supabase
      .channel('machine-realtime')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'products' },
        (payload) => {
          const { eventType, new: rowNew, old: rowOld } = payload || {}
          if (eventType === 'DELETE') removeLocal(products, rowOld, 'id')
          else if (rowNew) upsertLocal(products, rowNew, 'id')
        }
      )
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'transactions' },
        (payload) => {
          const { eventType, new: rowNew, old: rowOld } = payload || {}
          if (eventType === 'DELETE') {
            removeLocal(transactions, rowOld, rowOld?.source_tx_id != null ? 'source_tx_id' : 'id')
          } else if (rowNew) {
            upsertLocal(transactions, rowNew, rowNew?.source_tx_id != null ? 'source_tx_id' : 'id')
          }
          // Defensive: dedupe to avoid repeated rows if the backend replays.
          // Batched to keep UI responsive on mobile.
          scheduleTxNormalize()
        }
      )
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'live_feed' },
        (payload) => {
          const { eventType, new: rowNew, old: rowOld } = payload || {}
          if (eventType === 'DELETE') removeLocal(liveFeed, rowOld, 'id')
          else if (rowNew) upsertLocal(liveFeed, rowNew, 'id')
          scheduleFeedNormalize()
        }
      )
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'low_stock_products' },
        (payload) => {
          const { eventType, new: rowNew, old: rowOld } = payload || {}
          if (eventType === 'DELETE') removeLocal(lowStockProducts, rowOld, 'product_id')
          else if (rowNew) upsertLocal(lowStockProducts, rowNew, 'product_id')
          // keep small; table only contains low/empty rows
          if (lowStockProducts.value.length > 500) lowStockProducts.value = lowStockProducts.value.slice(0, 500)
        }
      )
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'emails' },
        (payload) => {
          const { eventType, new: rowNew, old: rowOld } = payload || {}
          if (eventType === 'DELETE') removeLocal(subscriberEmails, rowOld, 'id')
          else if (rowNew) upsertLocal(subscriberEmails, rowNew, 'id')
          if (subscriberEmails.value.length > 500) subscriberEmails.value = subscriberEmails.value.slice(0, 500)
        }
      )
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'bug_reports' },
        (payload) => {
          const { eventType, new: rowNew, old: rowOld } = payload || {}
          if (eventType === 'DELETE') removeLocal(bugReports, rowOld, 'id')
          else if (rowNew) upsertLocal(bugReports, rowNew, 'id')
          if (bugReports.value.length > 500) bugReports.value = bugReports.value.slice(0, 500)
        }
      )
      .subscribe((status, err) => {
        if (status === 'SUBSCRIBED') return
        if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          const msg = err?.message ? `Realtime: ${err.message}` : `Realtime channel ${status}`
          error.value = error.value ? `${error.value}; ${msg}` : msg
        }
      })
  }

  const overview = computed(() => {
    // Prefer server-side low_stock_products when available; otherwise compute from products.
    const computedLow = products.value
      .map((p) => {
        const name = String(p?.name ?? '').trim().toLowerCase()
        const stock = Number(p?.current_stock ?? 0)
        const threshold = (() => {
          if (name === 'alcohol') return 1
          if (name === 'wipes' || name === 'wet wipes' || name === 'wetwipes') return 1
          if (name === 'tissue' || name === 'tissues') return 1
          if (name === 'all night pads' || name === 'all-night pads') return 2
          return 3
        })()
        return stock <= threshold ? 1 : 0
      })
      .reduce((s, v) => s + v, 0)
    const lowStock = lowStockProducts.value.length > 0 ? lowStockProducts.value.length : computedLow
    const totalSales = transactions.value.reduce((sum, t) => sum + Number(t.total_amount ?? 0), 0)
    const orders = transactions.value.length
    const activeCustomers = new Set(
      transactions.value.map((t) => t.rfid_user_id).filter((x) => x !== null && x !== undefined)
    ).size

    return { totalSales, orders, activeCustomers, lowStock }
  })

  const lowStockItems = computed(() => {
    return products.value
      .map((p) => ({
        name: p.name,
        stock: Number(p.current_stock ?? 0),
        capacity: Number(p.capacity ?? 0),
        threshold: (() => {
          const name = String(p.name ?? '').trim().toLowerCase()
          if (name === 'alcohol') return 1
          if (name === 'wipes' || name === 'wet wipes' || name === 'wetwipes') return 1
          if (name === 'tissue' || name === 'tissues') return 1
          if (name === 'all night pads' || name === 'all-night pads') return 2
          if (name === 'deo' || name === 'deodorant') return 3
          if (name === 'soap') return 3
          if (name === 'mouth wash' || name === 'mouthwash') return 3
          if (name === 'panty liner' || name === 'panty liners' || name === 'pantyliners' || name === 'panti liner') return 3
          if (name === 'regular with wings' || name === 'regular w/ wings pads' || name === 'regular with wings pads') return 3
          if (name === 'non wing pad' || name === 'non-wing pads' || name === 'non wing pads' || name === 'non-wing pad') return 3
          return 3
        })(),
      }))
      .filter((p) => p.stock <= p.threshold)
      .sort((a, b) => (a.stock - a.threshold) - (b.stock - b.threshold))
      .slice(0, 10)
  })

  const recentTransactions = computed(() => {
    const tf = new Intl.DateTimeFormat('en-PH', {
      timeZone: 'Asia/Manila',
      dateStyle: 'short',
      timeStyle: 'medium',
    })
    return transactions.value.slice(0, 12).map((t) => ({
      id: t.id,
      item: t.product_name || (t.product_id != null ? `Product #${t.product_id}` : 'Unknown'),
      time: t.created_at ? tf.format(new Date(t.created_at)) : '—',
      amount: Number(t.total_amount ?? 0).toFixed(2),
    }))
  })

  onMounted(async () => {
    await loadInitial()
    subscribeRealtime()
  })

  onBeforeUnmount(() => {
    if (channel) {
      supabase.removeChannel(channel)
      channel = null
    }
  })

  return {
    products,
    transactions,
    liveFeed,
    lowStockProducts,
    subscriberEmails,
    bugReports,
    loading,
    error,
    overview,
    lowStockItems,
    recentTransactions,
    reload: loadInitial,
  }
}

