import { ref, watch, nextTick } from 'vue'

const THEME_KEY = 'syntax-error-theme'

function getInitialTheme() {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved) return saved
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
  }
  return 'dark'
}

const theme = ref(getInitialTheme())

function applyTheme(t) {
  const root = document.documentElement
  // Ensure we never end up with both classes at once.
  root.classList.remove('light', 'dark')
  root.classList.add(t === 'light' ? 'light' : 'dark')
}

// Apply on load
if (typeof window !== 'undefined') {
  applyTheme(theme.value)
}

watch(theme, (val) => {
  localStorage.setItem(THEME_KEY, val)
  // applyTheme(val) is also called here just in case, but we handle it in toggle for transitions
  applyTheme(val)
})

export function useTheme() {
  function toggle(event) {
    const isDark = theme.value === 'dark'
    const newTheme = isDark ? 'light' : 'dark'

    // Fallback if View Transitions API is not supported
    if (!document.startViewTransition) {
      theme.value = newTheme
      return
    }

    const x = event?.clientX ?? window.innerWidth / 2
    const y = event?.clientY ?? window.innerHeight / 2
    const endRadius = Math.hypot(
      Math.max(x, window.innerWidth - x),
      Math.max(y, window.innerHeight - y)
    )

    const transition = document.startViewTransition(async () => {
      theme.value = newTheme
      applyTheme(newTheme)
      await nextTick()
    })

    transition.ready.then(() => {
      const clipPath = [
        `circle(0px at ${x}px ${y}px)`,
        `circle(${endRadius}px at ${x}px ${y}px)`
      ]
      
      document.documentElement.animate(
        {
          clipPath: clipPath,
        },
        {
          duration: 500,
          easing: 'ease-out',
          pseudoElement: '::view-transition-new(root)',
        }
      )
    })
  }

  return {
    theme,
    toggle,
    isDark: () => theme.value === 'dark',
  }
}

