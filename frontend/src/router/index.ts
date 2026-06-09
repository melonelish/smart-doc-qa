import { createRouter, createWebHistory } from 'vue-router'
import DomainHome from '../views/DomainHome.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: DomainHome,
    },
    {
      path: '/kb/:kbId',
      name: 'knowledgeBase',
      component: () => import('../views/KnowledgeBaseView.vue'),
    },
    {
      path: '/doc/:docId',
      name: 'document',
      component: () => import('../views/DocumentView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const publicPaths = ['/login']
  const token = localStorage.getItem('smartdocqa_token')
  if (!token && !publicPaths.includes(to.path)) {
    next('/login')
  } else if (token && to.path === '/login') {
    next('/')
  } else {
    next()
  }
})

export default router
