import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { supabase } from '../lib/supabaseClient'

export function useRealtimeMachineData() {
  const products = ref([])
  const transactions = ref([])
  const loading = ref(true)
  const error = ref('')

  let channel = null

  async function loadInitial() {
    loading.value = true
    error.value = ''

    const [{ data: prod, error: prodErr }, { data: tx, error: txErr }] = await Promise.all([
      supabase.from('products').select('*').order('slot_number', { ascending: true }),
      supabase.from('transactions').select('*').order('created_at', { ascending: false }).limit(25),
    ])

    if (prodErr) error.value = prodErr.message
    if (txErr) error.value = error.value ? `${error.value}; ${txErr.message}` : txErr.message

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

          // Keep list small
          if (transactions.value.length > 50) transactions.value = transactions.value.slice(0, 50)
        }
      )
      .subscribe()
  }

  const overview = computed(() => {
    const lowStock = products.value.filter((p) => Number(p.current_stock ?? 0) < 4).length
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
      }))
      .filter((p) => p.stock < 4)
      .sort((a, b) => a.stock - b.stock)
      .slice(0, 10)
  })

  const recentTransactions = computed(() => {
    return transactions.value.slice(0, 8).map((t) => ({
      item: t.product_name || t.product_id || 'Unknown',
      time: t.created_at || t.timestamp || '',
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
    loading,
    error,
    overview,
    lowStockItems,
    recentTransactions,
    reload: loadInitial,
  }
}

