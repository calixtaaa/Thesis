export function debounce(fn, wait = 250) {
  let t = null
  return (...args) => {
    if (t) clearTimeout(t)
    t = setTimeout(() => fn(...args), wait)
  }
}

export function throttle(fn, wait = 150) {
  let last = 0
  let t = null
  return (...args) => {
    const now = Date.now()
    const remaining = wait - (now - last)
    if (remaining <= 0) {
      last = now
      fn(...args)
      return
    }
    if (!t) {
      t = setTimeout(() => {
        t = null
        last = Date.now()
        fn(...args)
      }, remaining)
    }
  }
}

// Best for scroll/resize handlers: once per animation frame.
export function rafThrottle(fn) {
  let scheduled = false
  let lastArgs = null
  return (...args) => {
    lastArgs = args
    if (scheduled) return
    scheduled = true
    requestAnimationFrame(() => {
      scheduled = false
      fn(...(lastArgs || []))
    })
  }
}

