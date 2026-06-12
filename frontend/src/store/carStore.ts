import { defineStore } from 'pinia'
import axios from 'axios'

// 完整小车数据接口（包含坐标，用于管理页）
export interface CarItem {
  id: number
  x: number
  y: number
  status: 'normal' | 'warning'
}

// 状态接口（保留）
export interface CarStatusItem {
  id: number
  status: 'normal' | 'warning'
}

interface GasThreshold {
  [key: number]: {
    threshold: number | [number, number]
    unit: string
  }
}

// 后端接口地址
const API_BASE = (import.meta.env.VITE_APP_BASE_API || '/api') + '/car'

export const useCarStore = defineStore('car', {
  state: (): {
    carList: CarItem[]; // 管理页用（含坐标）
    carStatusList: CarStatusItem[]; // Home/Detail 页用
    gasThreshold: GasThreshold
  } => ({
    // 管理页完整数据（初始值）
    carList: [
      { id: 1, x: 150, y: 200, status: 'normal' },
      { id: 2, x: 480, y: 280, status: 'normal' },
      { id: 3, x: 250, y: 250, status: 'warning' },
      { id: 4, x: 150, y: 330, status: 'normal' }
    ],
    // 状态列表（供 Home/Detail 使用）
    carStatusList: [
      { id: 1, status: 'normal' },
      { id: 2, status: 'normal' },
      { id: 3, status: 'warning' },
      { id: 4, status: 'normal' }
    ],
    gasThreshold: {
      1: { threshold: 25, unit: '%LEL' },
      2: { threshold: 10, unit: 'ppm' },
      3: { threshold: 20, unit: 'ppm' },
      4: { threshold: [19.5, 23.5], unit: '%VOL' }
    }
  }),
  actions: {
    // 核心：从后端加载所有小车数据（含坐标+状态）
    async fetchCarDataFromDB() {
      try {
        const res = await axios.get(`${API_BASE}/getAllCars`)
        if (res.data.code === 200) {
          // 格式化后端数据为前端结构
          const formatCarList: CarItem[] = res.data.data.map((item: { carId: number; x: number; y: number; warning: number }) => ({
            id: item.carId,
            x: item.x,
            y: item.y,
            status: item.warning === 1 ? 'warning' : 'normal'
          }))
          // 更新 carList（管理页）和 carStatusList（Home/Detail）
          this.carList = formatCarList
          this.carStatusList = formatCarList.map(car => ({ id: car.id, status: car.status }))
          console.log('成功从数据库加载小车数据：', formatCarList)
        }
      } catch (error) {
        console.error('加载数据库数据失败，使用本地默认：', error)
        // 失败时保留本地默认值，保证页面能渲染
      }
    },

    // 手动设置异常（同步后端+更新本地状态）
    async setCarWarning(carId: number): Promise<void> {
      try {
        // 1. 同步到后端
        await axios.post(`${API_BASE}/setWarning`, { carId })
        // 2. 更新本地状态
        const car = this.carList.find(item => item.id === carId)
        const statusItem = this.carStatusList.find(item => item.id === carId)
        if (car) car.status = 'warning'
        if (statusItem) statusItem.status = 'warning'
      } catch (error) {
        console.error(`设置小车${carId}异常失败：`, error)
        throw error // 抛出错误让组件层提示
      }
    },

    // 重置状态（同步后端+更新本地状态）
    async resetCarStatus(carId: number): Promise<void> {
      try {
        // 1. 同步到后端
        await axios.post(`${API_BASE}/resetStatus`, { carId })
        // 2. 更新本地状态
        const car = this.carList.find(item => item.id === carId)
        const statusItem = this.carStatusList.find(item => item.id === carId)
        if (car) car.status = 'normal'
        if (statusItem) statusItem.status = 'normal'
      } catch (error) {
        console.error(`重置小车${carId}状态失败：`, error)
        throw error
      }
    },

    // 同步状态（兼容原有逻辑）
    syncCarStatusList(cars: CarStatusItem[]): void {
      this.carStatusList = cars
    }
  },
  getters: {
    // 获取指定小车状态（全局通用）
    getCarStatus: (state) => (carId: number): 'normal' | 'warning' => {
      const car = state.carStatusList.find(item => item.id === carId)
      return car ? car.status : 'normal'
    }
  }
})