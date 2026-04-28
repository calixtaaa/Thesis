import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { supabase } from '../lib/supabaseClient'

export function useRealtimeMachineData() {
  const products = ref([])
  const transactions = ref([])
  const liveFeed = ref([])
  const subscriberEmails = ref([])
  const loading = ref(true)
  const error = ref('')

  let channel = null

  async function loadInitial() {
    loading.value = true
    error.value = ''

    const [prodRes, txRes, feedRes, mailRes] = await Promise.all([
      supabase.from('products').select('*').order('slot_number', { ascending: true }),
      supabase
        .from('transactions')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(3000),
      supabase.from('live_feed').select('*').order('created_at', { ascending: false }).limit(100),
      supabase.from('emails').select('id, email, created_at, password').order('created_at', { ascending: false }).limit(500),
    ])

    const { data: prod, error: prodErr } = prodRes
    const { data: tx, error: txErr } = txRes
    const { data: feed, error: feedErr } = feedRes
    const { data: mails, error: mailErr } = mailRes

    if (prodErr) error.value = prodErr.message
    if (txErr) error.value = error.value ? `${error.value}; ${txErr.message}` : txErr.message
    if (feedErr) {
      const msg = feedErr.message || String(feedErr)
      if (!/relation|does not exist|not find/i.test(msg)) {
        error.value = error.value ? `${error.value}; ${msg}` : msg
      }
      liveFeed.value = []
    } else {
      liveFeed.value = Array.isArray(feed) ? feed : []
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

    products.value = Array.isArray(prod) ? prod : []
    transactions.value = Array.isArray(tx) ? tx : []
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
          if (eventType === 'DELETE') removeLocal(transactions, rowOld, 'id')
          else if (rowNew) upsertLocal(transactions, rowNew, 'id')

          if (transactions.value.length > 3000) transactions.value = transactions.value.slice(0, 3000)
        }
      )
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'live_feed' },
        (payload) => {
          const { eventType, new: rowNew, old: rowOld } = payload || {}
          if (eventType === 'DELETE') removeLocal(liveFeed, rowOld, 'id')
          else if (rowNew) upsertLocal(liveFeed, rowNew, 'id')
          if (liveFeed.value.length > 100) liveFeed.value = liveFeed.value.slice(0, 100)
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
      .subscribe((status, err) => {
        if (status === 'SUBSCRIBED') return
        if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          const msg = err?.message ? `Realtime: ${err.message}` : `Realtime channel ${status}`
          error.value = error.value ? `${error.value}; ${msg}` : msg
        }
      })
  }

  const overview = computed(() => {
    const lowStock = products.value.filter((p) => {
      const stock = Number(p.current_stock ?? 0)
      const name = String(p.name ?? '').trim().toLowerCase()
      const threshold =
        name === 'alcohol' ? 1
          : (name === 'wipes' || name === 'wet wipes' || name === 'wetwipes') ? 1
            : (name === 'tissue' || name === 'tissues') ? 1
              : (name === 'all night pads' || name === 'all-night pads') ? 2
                : (name === 'deo' || name === 'deodorant') ? 3
                  : (name === 'soap') ? 3
                    : (name === 'mouth wash' || name === 'mouthwash') ? 3
                      : (name === 'panty liner' || name === 'panty liners' || name === 'pantyliners' || name === 'panti liner') ? 3
                        : (name === 'regular with wings' || name === 'regular w/ wings pads' || name === 'regular with wings pads') ? 3
                          : (name === 'non wing pad' || name === 'non-wing pads' || name === 'non wing pads' || name === 'non-wing pad') ? 3
                            : 3
      return stock <= threshold
    }).length
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
    subscriberEmails,
    loading,
    error,
    overview,
    lowStockItems,
    recentTransactions,
    reload: loadInitial,
  }
}

