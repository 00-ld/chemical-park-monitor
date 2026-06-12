<template>
  <div class="register-container">
    <!-- 背景动态光效层 -->
    <div class="background-light"></div>
    <!-- 背景遮罩层 -->
    <div class="mask-layer"></div>

    <!-- 左侧主题标识（已美化） -->
    <div class="theme-logo">
      <div class="logo-icon-wrapper">
        <div class="logo-icon">
          <i class="el-icon-user-plus"></i>
        </div>
        <div class="icon-glow"></div>
      </div>

      <div class="logo-title-group">
        <div class="logo-title">智监溯源</div>
        <div class="logo-subtitle">多源多模态化工园区气体监控与溯源系统</div>
        <div class="logo-desc">
          智能监测 · 精准溯源 · 安全预警 · 全域管控
        </div>
      </div>
    </div>

    <!-- 右侧注册框 -->
    <div class="register-box">
      <div class="register-header">
        <div class="register-title">
          <span>账号注册</span>
        </div>
        <div class="register-subtitle">填写信息完成注册，即可使用系统功能</div>
      </div>

      <el-form ref="registerForms" :rules="rules" :model="registerForm" class="register-form">
        <el-form-item prop="username" class="form-item">
          <div class="input-label">登录账号</div>
          <el-input
              size="large"
              v-model="registerForm.username"
              :prefix-icon="User"
              placeholder="请输入登录账号"
              class="register-input"
              :class="{ 'input-focus': isUsernameFocus }"
              @focus="isUsernameFocus = true"
              @blur="isUsernameFocus = false"
          />
        </el-form-item>

        <el-form-item prop="no" class="form-item">
          <div class="input-label">员工工号</div>
          <el-input
              size="large"
              v-model="registerForm.no"
              prefix-icon="el-icon-idcard"
              placeholder="请输入员工工号"
              class="register-input"
              :class="{ 'input-focus': isNoFocus }"
              @focus="isNoFocus = true"
              @blur="isNoFocus = false"
          />
        </el-form-item>

        <el-form-item prop="password" class="form-item">
          <div class="input-label">设置密码</div>
          <el-input
              show-password
              size="large"
              v-model="registerForm.password"
              :prefix-icon="Lock"
              placeholder="请设置登录密码"
              class="register-input"
              :class="{ 'input-focus': isPwdFocus }"
              @focus="isPwdFocus = true"
              @blur="isPwdFocus = false"
          />
        </el-form-item>

        <el-form-item prop="confirmPassword" class="form-item">
          <div class="input-label">确认密码</div>
          <el-input
              show-password
              size="large"
              v-model="registerForm.confirmPassword"
              :prefix-icon="Lock"
              placeholder="请再次输入密码"
              class="register-input"
              :class="{ 'input-focus': isConfirmPwdFocus }"
              @focus="isConfirmPwdFocus = true"
              @blur="isConfirmPwdFocus = false"
          />
        </el-form-item>

        <el-form-item class="register-btn-item">
          <el-button
              type="primary"
              size="large"
              style="width:100%"
              @click="register"
              class="register-btn"
              :loading="loading"
          >
            完成注册
          </el-button>
        </el-form-item>

        <div class="login-tip">
          已有账号？请<a @click="goToLogin">立即登录</a>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts" name="Register">
import { User, Lock } from '@element-plus/icons-vue';
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElNotification } from 'element-plus';
import { reqRegister } from '@/api/user';

const $router = useRouter();
const loading = ref(false);
const registerForms = ref();

const isUsernameFocus = ref(false)
const isNoFocus = ref(false)
const isPwdFocus = ref(false)
const isConfirmPwdFocus = ref(false)

// 清空所有默认值，无任何预设账号密码
const registerForm = reactive({
  username: '',
  no: '',
  password: '',
  confirmPassword: ''
});

// 密码一致性校验
const validatePass = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if (!value) {
    callback(new Error('请确认密码'))
  } else if (value !== registerForm.password) {
    callback(new Error("两次输入的密码不匹配"))
  } else {
    callback()
  }
}

// 账号验证
const validatorUserName = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if(!value){
    callback(new Error('请输入登录账号'));
  }else if (value.length >= 5) {
    callback();
  } else {
    callback(new Error('账号长度至少五位'));
  }
};

// 工号验证
const validatorNo = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if (!value) {
    callback(new Error('请输入工号'));
  } else {
    callback();
  }
};

// 密码验证
const validatorPassword = (_rule: any, value: string, callback: (error?: Error) => void) => {
  if(!value){
    callback(new Error('请输入密码'));
  }else if (value.length >= 6) {
    callback();
  } else {
    callback(new Error('密码长度至少六位'));
  }
};

const rules = {
  username: [
    { trigger: 'blur', validator: validatorUserName },
  ],
  no: [
    { trigger: 'blur', validator: validatorNo },
  ],
  password: [
    { trigger: 'blur', validator: validatorPassword },
  ],
  confirmPassword: [
    { trigger: 'blur', validator: validatePass },
  ]
};

// 注册方法（安全优化 + 异常捕获）
const register = async () => {
  // 表单未通过则不发送请求
  try {
    await registerForms.value.validate();
  } catch (error) {
    ElNotification({
      type: 'warning',
      title: '提示',
      message: '请完善注册信息'
    })
    return;
  }

  loading.value = true;
  try {
    const res = await reqRegister(registerForm);
    if (res.code === 200) {
      ElNotification.success('注册成功！即将跳转到登录页');
      setTimeout(() => {
        $router.push('/login');
      },800)
    } else {
      ElNotification.error(res.error || res.message || '注册失败');
    }
  } catch (error) {
    ElNotification.error('注册请求失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 去登录
const goToLogin = () => {
  $router.push({ path: '/login?redirect=/home' });
};
</script>

<style scoped lang="scss">
.register-container {
  height: 100vh;
  overflow: hidden;
  background-image: url("/注册背景图.png");
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
  background: radial-gradient(circle at 70% 50%, rgba(64, 224, 208, 0.1) 0%, rgba(10, 92, 173, 0.05) 60%, transparent 100%);
  z-index: 0;
  animation: lightMove 18s ease-in-out infinite alternate;
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

/* ====================== 左侧主题区 美化 ====================== */
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

/* ====================== 注册框样式（科技玻璃态） ====================== */
.register-box {
  position: absolute;
  z-index: 2;
  top: 50%;
  right: 10%;
  transform: translateY(-50%);
  width: 460px;
  background-color: rgba(10, 25, 50, 0.65);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-radius: 20px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5), inset 0 0 1px rgba(255, 255, 255, 0.2);
  padding: 50px 40px;
  box-sizing: border-box;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.register-header {
  text-align: center;
  margin-bottom: 40px;
}

.register-title {
  font-size: 28px;
  font-weight: 700;
  color: #40e0d0;
  margin-bottom: 8px;
  text-shadow: 0 0 10px rgba(64, 224, 208, 0.4);
}

.register-subtitle {
  font-size: 14px;
  color: #b8e8e4;
  opacity: 0.8;
}

.register-form {
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

.register-input {
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

.register-btn-item {
  margin-bottom: 15px;
  margin-top: 10px;
}

.register-btn {
  background: linear-gradient(135deg, #0a5cad 0%, #084b8a 100%);
  border: none;
  font-weight: 600;
  height: 52px;
  font-size: 16px;
  border-radius: 10px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(10, 92, 173, 0.3);
}

.register-btn:hover {
  background: linear-gradient(135deg, #084b8a 0%, #063e70 100%);
  box-shadow: 0 6px 20px rgba(10, 92, 173, 0.4);
  transform: translateY(-2px);
}

.register-btn:active {
  transform: translateY(0);
}

.login-tip {
  text-align: center;
  font-size: 14px;
  color: #b8e8e4;
  margin-top: 10px;
}

.login-tip a {
  color: #40e0d0;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: pointer;
}

.login-tip a:hover {
  color: #fff;
  text-shadow: 0 0 5px #40e0d0;
  text-decoration: none;
}

@media (max-width: 1200px) {
  .theme-logo {
    display: none;
  }
  .register-box {
    right: 50%;
    transform: translate(50%, -50%);
  }
}

@media (max-width: 480px) {
  .register-box {
    width: 90%;
    padding: 40px 25px;
    border-radius: 15px;
  }
  .register-title {
    font-size: 24px;
  }
  .form-item {
    margin-bottom: 20px;
  }
}
</style>