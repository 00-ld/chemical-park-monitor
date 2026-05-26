<template>
  <div class="layout_container">
    <!-- 顶部导航栏 -->
    <header class="header_nav">
      <div class="header_wrap">
        <!-- Logo -->
        <Logo style="margin: auto"></Logo>
        <!-- 导航菜单 -->
        <nav class="header_menu">
          <el-menu
            mode="horizontal"
            :default-active="$route.path"
            @select="handleMenuSelect"
            background-color="#000"
            text-color="#fff"
            active-text-color="#40a9ff"
            class="top_menu"
            :ellipsis="false"
          >
            <!-- 首页（无下拉） -->
            <el-menu-item index="/home">首页</el-menu-item>

            <!-- 数字园区（无下拉） -->
            <el-menu-item index="/screen">数字园区</el-menu-item>

            <!-- 智慧地图（无下拉） -->
            <el-menu-item index="/map_test">智慧地图</el-menu-item>

            <!-- 预警与智巡（有子菜单） -->
            <el-sub-menu index="/warning-patrol">
              <template #title>预警与智巡</template>
              <el-menu-item index="/thing/monitor_history">实时监控</el-menu-item>
              <el-menu-item index="/car/home">智巡监测</el-menu-item>
            </el-sub-menu>

            <!-- 厂区实时监测（无下拉） -->
            <el-menu-item index="/yolo">厂区实时监测</el-menu-item>

            <!-- 人员信息管理（有子菜单） -->
            <el-sub-menu index="/personnel-manage">
              <template #title>人员信息管理</template>
              <el-menu-item index="/acl/role">管理员管理</el-menu-item>
              <el-menu-item index="/acl/employee">员工信息管理</el-menu-item>
            </el-sub-menu>

            <!-- 退出登录（无下拉） -->
            <el-menu-item index="logout" class="logout-item">
              退出登录
            </el-menu-item>
          </el-menu>
        </nav>

        <!-- 右侧个人头像区域 -->
        <div class="user_info">
          <div class="avatar_box">
            <el-avatar size="48" :src="avatar" class="user_avatar">
              <span class="avatar_text">管理员</span>
            </el-avatar>
          </div>
        </div>
      </div>
    </header>

    <!-- 顶部tabbar（移出header_nav，单独布局） -->
    <div class="layout_tabbar" :class="{ fold: LayOutSettingStore?.fold }">
      <Tabbar></Tabbar>
    </div>

    <!-- 内容区域 -->
    <main class="layout_main">
      <Main />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElAvatar } from 'element-plus'
// 引入子组件
import Main from './main/index.vue'
import Logo from './logo/index.vue'
import Tabbar from './tabbar/index.vue'

defineOptions({
  name: 'Layout',
})

// 获取路由实例
const $router = useRouter()
const $route = useRoute()

// 模拟布局仓库（如果项目中有真实的Pinia/Vuex仓库，替换此处）
const LayOutSettingStore = {
  fold: false, // 默认不折叠
}

const avatar = ref(
  'https://wpimg.wallstcn.com/f778738c-e4f8-4870-b634-56703b4acafe.gif?imageView2/1/w/80/h/80',
)
// 菜单选中事件
const handleMenuSelect = (index: string) => {
  if (index === $route.path) return

  if (index === 'logout') {
    localStorage.removeItem('token')
    $router
      .push('/login')
      .catch((err) => console.warn('退出登录跳转失败:', err))
    return
  }

  $router.push(index).catch((err) => console.warn('菜单跳转失败:', err))
}
</script>

<style scoped lang="scss">
// 全局变量定义（解决未定义变量问题）
$base-menu-width: 200px; // 菜单展开宽度
$base-menu-min-width: 64px; // 菜单折叠宽度
$base-tabbar-height: 48px; // tabbar高度
$header-height: 80px; // 顶部导航高度

.layout_container {
  width: 100%;
  min-height: 100vh;
}
// 顶部导航栏（独立布局）
.header_nav {
  width: 100%;
  height: $header-height;
  background-color: #0a192f; /* 科技深蓝色 */
  color: #fff;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 999; // 高于tabbar，避免遮挡
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5); /* 增加阴影增强层次感 */

  .header_wrap {
    max-width: 1920px;
    width: 100%; // 占满宽度
    height: 100%;
    margin: 0 auto;
    display: flex;
    align-items: stretch;
    justify-content: flex-start; // 整体左对齐，最大化菜单空间
    padding: 0 24px;
    box-sizing: border-box; // 防止padding撑大容器
  }

  // 导航菜单
  .header_menu {
    flex: 1;
    display: flex;
    justify-content: flex-start;
    margin-left: 10px;
    /* 移除右侧margin，彻底释放菜单宽度 */
    // margin-right: 80px;

    .top_menu {
      border-bottom: none;
      background-color: transparent !important;
      width: 100%;
      display: flex;
      flex-wrap: nowrap; // 禁止菜单项换行

      :deep(.el-menu-item),
      :deep(.el-sub-menu__title) {
        color: #e0e6ed;
        font-size: 16px;
        padding: 0 10px;
        height: $header-height;
        line-height: $header-height;
        transition: all 0.3s;
        // 禁止文字换行
        white-space: nowrap;
        box-sizing: border-box;
        padding-right: 35px;

        &:hover,
        &.is-active {
          color: #40e0d0; /* 科技青色 */
          border-bottom: 5px solid #40e0d0;
          background-color: rgba(64, 224, 208, 0.1) !important;
        }
      }

      // 退出登录样式突出
      :deep(.logout-item) {
        color: #ff4d4f;
        &:hover {
          color: #ff7875;
          border-bottom-color: #ff4d4f;
        }
      }

      :deep(.el-sub-menu__icon-arrow) {
        color: #fff;
        margin-left: 5px;
        //display: none;
      }

      // 下拉子菜单样式
      :deep(.el-sub-menu .el-menu) {
        background-color: #0a192f !important;

        :deep(.el-menu-item) {
          height: 48px;
          line-height: 48px;
          padding-left: 30px !important;
          border-bottom: none !important;

          &:hover {
            background-color: rgba(64, 224, 208, 0.1) !important;
            color: #40e0d0;
          }
        }
      }
    }
  }

  // 右侧个人头像
  .user_info {
    display: flex;
    align-items: center;
    margin-left: 20px;
    margin-right: 15px;
    flex-shrink: 0; // 防止头像被压缩

    .avatar_box {
      .user_avatar {
        cursor: pointer;
        border: 2px solid #40a9ff;
        transition: all 0.3s;

        &:hover {
          transform: scale(1.05);
          border-color: #69b1ff;
        }

        .avatar_text {
          font-size: 12px;
          color: #fff;
        }
      }
    }
  }
}

// 顶部tabbar（独立布局，避免和header嵌套）
.layout_tabbar {
  position: fixed;
  top: $header-height;
  left: 0;
  width: 100%;
  height: $base-tabbar-height;
  background-color: #112240; /* 匹配科技感深色 */
  z-index: 998;
  transition: all 0.3s;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);

  &.fold {
    left: $base-menu-min-width;
    width: calc(100% - #{$base-menu-min-width});
  }
}

// 内容区域（适配header+tabbar高度）
.layout_main {
  margin-top: calc($header-height + $base-tabbar-height);
  padding: 24px 40px;
  min-height: calc(100vh - $header-height - $base-tabbar-height);
  max-width: 1920px;
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;
  position: relative; /* 必须加 */
  overflow: hidden; /* 必须加，防止模糊溢出 */
  background-color: #f5f5f5;

  /* 背景图 */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url('@/assets/images/background2.jpg');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    z-index: 0;
    /* 0=不模糊，3=轻微，5=适中，8=很模糊，10=非常模糊 */
    filter: blur(8px);
  }

  /* 让内容在模糊层上面 */
  & > * {
    position: relative;
    z-index: 1;
  }
}
// 小屏幕适配
@media (max-width: 1440px) {
  .header_menu :deep(.el-menu-item),
  .header_menu :deep(.el-sub-menu__title) {
    font-size: 14px;
    padding: 0 8px;
  }
}
</style>
