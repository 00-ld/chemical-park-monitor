// 用户信息相关的仓库
import { defineStore } from 'pinia'
import { reqLogin, reqUserInfo } from '@/api/user'
import type { loginFormData } from '@/api/user/type'
import { ElMessage } from 'element-plus'

// 引入常量路由
import { constantRoute } from '@/router/routes'

const useUserStore = defineStore('user', {
  state: () => {
    return {
      token: '',
      menuRoutes: constantRoute,
      username: '',
      avatar: '',
    }
  },
  actions: {
    // 用户登录
    async userLogin(data: loginFormData) {
      const result = await reqLogin(data)
      // 登录成功：存储token
      if (result.code === 200) {
        this.token = result.data
        return 'ok'
      } else {
        return Promise.reject(new Error(result.message))
      }
    },
    // 获取用户信息
    async userInfo() {
      const result = await reqUserInfo()
      // 如果获取用户信息成功，存储用户信息
      if (result.code === 200) {
        this.username = result.data.name
        this.avatar = result.data.avatar
        return 'ok'
      } else {
        return Promise.reject(new Error(result.message))
      }
    },
  },
  getters: {},
})

export default useUserStore