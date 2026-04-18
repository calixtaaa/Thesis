import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../views/HomePage.vue'
import TeamPage from '../views/TeamPage.vue'
import AdviserPage from '../views/AdviserPage.vue'
import DashboardPage from '../views/DashboardPage.vue'
import LoginPage from '../views/LoginPage.vue'
import { supabase, isSupabaseConfigured } from '../utils/supabase'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomePage,
    meta: { title: 'Home — Syntax Error' }
  },
  {
    path: '/team',
    name: 'Team',
    component: TeamPage,
    meta: { title: 'Our Team — Syntax Error' }
  },
  {
    path: '/adviser',
    name: 'Adviser',
    component: AdviserPage,
    meta: { title: 'Adviser — Syntax Error' }
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: { title: 'Login — Syntax Error' }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardPage,
    meta: { title: 'Dashboard — Syntax Error', requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach(async (to) => {
  document.title = to.meta.title || 'Syntax Error — Capstone Project'

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  if (!requiresAuth) return

  if (!isSupabaseConfigured()) {
    return { name: 'Login', query: { reason: 'supabase-env' } }
  }

  const { data: { session } } = await supabase.auth.getSession()
  if (!session) return { name: 'Login' }
})

export default router
