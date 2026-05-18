import { createRouter, createWebHashHistory } from 'vue-router'
import { constantRoute } from './routes'

const router = createRouter({
  history: createWebHashHistory(),
  routes: constantRoute,
  scrollBehavior() {
    return { left: 0, top: 0 }
  },
})

// 路由守卫：未登录时强制跳转登录页
const whiteList = ['/login', '/register']
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (token) {
    next()
  } else if (whiteList.includes(to.path)) {
    next()
  } else {
    next('/login')
  }
})

export default router
