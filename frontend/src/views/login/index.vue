<template>
  <div class="login-container">
    <div class="background-light"></div>
    <div class="mask-layer"></div>

    <div class="theme-logo">
      <div class="logo-icon-wrapper">
        <div class="logo-icon">
          <i class="el-icon-safety"></i>
        </div>
        <div class="icon-glow"></div>
      </div>

      <div class="logo-title-group">
        <div class="logo-title">智慧溯源</div>
        <div class="logo-subtitle">多源化工园区气体监测系统</div>
        <div class="logo-desc">监测 · 溯源 · 预警 · 园区管控</div>
      </div>
    </div>

    <div class="login-box">
      <div class="login-header">
        <div class="login-title">
          <span>系统登录</span>
        </div>
        <div class="login-subtitle">欢迎使用化工园区气体监测系统</div>
      </div>

      <el-form ref="loginForms" :rules="rules" :model="loginForm" class="login-form">
        <el-form-item prop="username" class="form-item">
          <div class="input-label">账号</div>
          <el-input
            size="large"
            v-model="loginForm.username"
            :prefix-icon="User"
            placeholder="请输入账号"
            class="login-input"
            :class="{ 'input-focus': isUsernameFocus }"
            @focus="isUsernameFocus = true"
            @blur="isUsernameFocus = false"
          />
        </el-form-item>

        <el-form-item prop="password" class="form-item">
          <div class="input-label">密码</div>
          <el-input
            show-password
            size="large"
            v-model="loginForm.password"
            :prefix-icon="Lock"
            placeholder="请输入密码"
            class="login-input"
            :class="{ 'input-focus': isPasswordFocus }"
            @focus="isPasswordFocus = true"
            @blur="isPasswordFocus = false"
          />
        </el-form-item>

        <el-form-item class="login-btn-item">
          <el-button
            type="primary"
            size="large"
            style="width:100%"
            @click="login"
            class="login-btn"
            :loading="loading"
          >
            登录
          </el-button>
        </el-form-item>

        <div class="register-tip">
          还没有账号？<a @click="goRegister">立即注册</a>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts" name="Login">
import { User, Lock } from '@element-plus/icons-vue'
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElNotification } from 'element-plus'
import useUserStore from '@/store/modules/user'

const userStore = useUserStore()

const getTime = () => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜间好'
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
}

const loginForms = ref()
const $router = useRouter()
const $route = useRoute()

const loading = ref(false)
const isUsernameFocus = ref(false)
const isPasswordFocus = ref(false)

interface LoginForm {
  username: string
  password: string
}

const loginForm = reactive<LoginForm>({
  username: '',
  password: '',
})

const validatorUserName = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if (value.length >= 5) {
    callback()
  } else {
    callback(new Error('账号长度不能少于 5 位'))
  }
}

const validatorPassword = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if (value.length >= 6) {
    callback()
  } else {
    callback(new Error('密码长度不能少于 6 位'))
  }
}

const rules = {
  username: [{ trigger: 'change', validator: validatorUserName }],
  password: [{ trigger: 'change', validator: validatorPassword }],
}

const login = async () => {
  try {
    await loginForms.value.validate()
  } catch (error) {
    ElNotification({
      type: 'warning',
      message: '请检查账号和密码',
      title: '校验未通过',
    })
    return
  }

  loading.value = true

  try {
    await userStore.userLogin(loginForm)
    ElNotification({
      type: 'success',
      message: '登录成功，正在进入系统...',
      title: getTime(),
    })
    const redirect = $route.query.redirect as string | undefined
    $router.push({ path: redirect || '/home' })
  } catch (error: any) {
    ElNotification.error(error?.message || '登录失败')
  } finally {
    loading.value = false
  }
}

const goRegister = () => {
  $router.push({ path: '/register' })
}
</script>
<style scoped>
.login-container {
  height: 100vh;
  overflow: hidden;
  background-image: url("/%E7%99%BB%E5%BD%95%E8%83%8C%E6%99%AF%E5%9B%BE.png");
  background-size: cover;
  background-position: center center;
  background-repeat: no-repeat;
  position: relative;
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
}

.background-light {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 30% 40%, rgba(64, 224, 208, 0.1) 0%, rgba(10, 92, 173, 0.05) 60%, transparent 100%);
  z-index: 0;
  animation: lightMove 15s ease-in-out infinite alternate;
}

@keyframes lightMove {
  0% {
    background-position: 0% 0%;
  }
  100% {
    background-position: 100% 100%;
  }
}

.mask-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 28, 58, 0.7);
  backdrop-filter: blur(2px);
  z-index: 1;
}

/* ====================== 左侧主题区 全新美化 ====================== */
.theme-logo {
  position: absolute;
  z-index: 2;
  left: 10%;
  top: 50%;
  transform: translateY(-50%);
  color: #ffffff;
  max-width: 580px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 30px;
}

.logo-icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon {
  font-size: 70px;
  color: #00eaff;
  filter: drop-shadow(0 0 15px rgba(0, 234, 255, 0.6));
  position: relative;
  z-index: 2;
  animation: iconFloat 3s ease-in-out infinite;
}

.icon-glow {
  position: absolute;
  width: 90px;
  height: 90px;
  background: radial-gradient(circle, rgba(0, 234, 255, 0.25) 0%, transparent 70%);
  border-radius: 50%;
  z-index: 1;
  animation: glowPulse 3s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

@keyframes glowPulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.2); opacity: 0.3; }
}

.logo-title-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.logo-title {
  font-size: 52px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: 4px;
  line-height: 1.2;
  text-shadow: 0 0 25px rgba(0, 234, 255, 0.5), 0 2px 10px rgba(0,0,0,0.3);
}

.logo-subtitle {
  font-size: 22px;
  color: #00eaff;
  font-weight: 500;
  letter-spacing: 1.5px;
  opacity: 0.95;
  text-shadow: 0 0 10px rgba(0, 234, 255, 0.3);
}

.logo-desc {
  font-size: 17px;
  color: #b8e8e4;
  opacity: 0.85;
  letter-spacing: 1px;
  padding-top: 8px;
  border-left: 3px solid #00eaff;
  padding-left: 15px;
}

/* ====================== 登录框样式 ====================== */
.login-box {
  position: absolute;
  z-index: 2;
  top: 50%;
  right: 10%;
  transform: translateY(-50%);
  width: 420px;
  background-color: rgba(10, 25, 50, 0.65);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-radius: 20px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5), inset 0 0 1px rgba(255, 255, 255, 0.2);
  padding: 50px 40px;
  box-sizing: border-box;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #40e0d0;
  margin-bottom: 8px;
  text-shadow: 0 0 10px rgba(64, 224, 208, 0.4);
}

.login-subtitle {
  font-size: 14px;
  color: #b8e8e4;
  opacity: 0.8;
}

.login-form {
  width: 100%;
}

.form-item {
  margin-bottom: 25px;
}

.input-label {
  font-size: 15px;
  font-weight: 600;
  color: #e0e6ed;
  margin-bottom: 8px;
  display: block;
}

.login-input {
  width: 100%;
  height: 52px;
  border-radius: 10px;
  border: none;
  padding: 0 15px;
  font-size: 15px;
  transition: all 0.3s ease;
  background-color: transparent;
}

:deep(.el-input__wrapper) {
  background-color: rgba(0, 0, 0, 0.2) !important;
  border-radius: 10px;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:focus-within) {
  border-color: #40e0d0;
  box-shadow: 0 0 0 3px rgba(64, 224, 208, 0.1) !important;
}

:deep(.el-input__inner) {
  color: #fff !important;
}

:deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.5) !important;
}

:deep(.el-input__prefix) {
  color: #40e0d0;
}

.login-btn-item {
  margin-bottom: 15px;
}

.login-btn {
  background: linear-gradient(135deg, #0a5cad 0%, #084b8a 100%);
  border: none;
  font-weight: 600;
  height: 52px;
  font-size: 16px;
  border-radius: 10px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(10, 92, 173, 0.3);
}

.login-btn:hover {
  background: linear-gradient(135deg, #084b8a 0%, #063e70 100%);
  box-shadow: 0 6px 20px rgba(10, 92, 173, 0.4);
  transform: translateY(-2px);
}

.login-btn:active {
  transform: translateY(0);
}

.register-tip {
  text-align: center;
  font-size: 14px;
  color: #b8e8e4;
  margin-top: 10px;
}

.register-tip a {
  color: #40e0d0;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: pointer;
}

.register-tip a:hover {
  color: #fff;
  text-shadow: 0 0 5px #40e0d0;
  text-decoration: none;
}

@media (max-width: 1200px) {
  .theme-logo {
    display: none;
  }
  .login-box {
    right: 50%;
    transform: translate(50%, -50%);
  }
}

@media (max-width: 480px) {
  .login-box {
    width: 90%;
    padding: 40px 25px;
    border-radius: 15px;
  }
  .login-title {
    font-size: 24px;
  }
}
</style>
