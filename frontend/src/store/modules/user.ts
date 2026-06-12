// 用户信息相关的仓库
import { defineStore } from 'pinia'
import { reqLogin, reqUserInfo } from '@/api/user'
import type { loginFormData } from '@/api/user/type'
import { ElMessage } from 'element-plus'

// 引入常量路由
import { constantRoute } from '@/router/routes'
// 引入 token 本地存储工具（全项目统一的单一数据源，key 为 'TOKEN'）
import { GET_TOKEN, SET_TOKEN, REMOVE_TOKEN } from '@/utils/token'

const useUserStore = defineStore('user', {
  state: () => {
    return {
      // 初始化时从本地存储恢复登录态，保证刷新后仍保持登录
      token: GET_TOKEN() || '',
      menuRoutes: constantRoute,
      username: '',
      avatar: '',
    }
  },
  actions: {
    // 用户登录
    async userLogin(data: loginFormData) {
      const result = await reqLogin(data)
      // 登录成功：同时写入内存(store)与本地存储
      if (result.code === 200) {
        this.token = result.data
        SET_TOKEN(result.data)
        return 'ok'
      } else {
        return Promise.reject(new Error(result.message))
      }
    },
    // 退出登录：清除内存与本地存储中的登录态
    logout() {
      this.token = ''
      this.username = ''
      this.avatar = ''
      REMOVE_TOKEN()
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