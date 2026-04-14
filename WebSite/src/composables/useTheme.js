import { ref, watch } from 'vue'

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
  if (t === 'light') {
    root.classList.add('light')
    root.classList.remove('dark')
  } else {
    root.classList.remove('light')
    root.classList.add('dark')
  }
}

// Apply on load
if (typeof window !== 'undefined') {
  applyTheme(theme.value)
}

watch(theme, (val) => {
  localStorage.setItem(THEME_KEY, val)
  applyTheme(val)
})

export function useTheme() {
  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  return {
    theme,
    toggle,
    isDark: () => theme.value === 'dark',
  }
}
