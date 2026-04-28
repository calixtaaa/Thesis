import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const HomePage = () => import('../views/HomePage.vue')
const TeamPage = () => import('../views/TeamPage.vue')
const AdviserPage = () => import('../views/AdviserPage.vue')
const LoginPage = () => import('../views/LoginPage.vue')
const DashboardPage = () => import('../views/DashboardPage.vue')

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

router.beforeEach((to) => {
  document.title = to.meta.title || 'Syntax Error — Capstone Project'

  if (to.meta.requiresAuth) {
    const { isLoggedIn } = useAuth()
    if (!isLoggedIn.value) {
      return { name: 'Login' }
    }
  }
})

export default router
