<template>
  <div class="worker-container">
    <!-- 背景图片 -->
    <div class="background-image"></div>
    
    <!-- 统计卡片 -->
    <div class="stats-container">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <div class="stat-value">{{ allWorkerList.length }}</div>
          <div class="stat-label">总管理员数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ allWorkerList.filter(item => item.status === '1').length }}</div>
          <div class="stat-label">工作中</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🏖️</div>
        <div class="stat-content">
          <div class="stat-value">{{ allWorkerList.filter(item => item.status === '2').length }}</div>
          <div class="stat-label">空闲中</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-content">
          <div class="stat-value">{{ new Set(allWorkerList.map(item => item.job)).size }}</div>
          <div class="stat-label">职位类型</div>
        </div>
      </div>
    </div>

    <!-- 搜索表单 -->
    <el-card>
      <el-form :inline="true" class="search-form">
        <el-form-item label="姓名搜索">
          <el-input placeholder="请输入工作人员姓名" v-model="searchForm.name" clearable></el-input>
        </el-form-item>
        <el-form-item label="职位">
          <el-select v-model="searchForm.job" placeholder="请选择职位" clearable style="width: 150px;">
            <el-option label="全部" value=""></el-option>
            <el-option label="安全管理员" :value="1"></el-option>
            <el-option label="设备管理员" :value="2"></el-option>
            <el-option label="工艺管理员" :value="3"></el-option>
            <el-option label="环保管理员" :value="4"></el-option>
            <el-option label="质检管理员" :value="5"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable style="width: 150px;">
            <el-option label="全部" value=""></el-option>
            <el-option label="工作中" value="1"></el-option>
            <el-option label="空闲中" value="2"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="default" @click="handleSearch">搜索</el-button>
          <el-button size="default" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 工作人员列表 -->
    <el-card style="margin: 10px 0;">
      <el-button type="primary" size="default" icon="Plus" @click="handleAdd">添加管理员</el-button>
      <el-table :data="displayWorkerList" border stripe style="margin: 10px 0;">
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="name" label="姓名" align="center" />
        <el-table-column prop="age" label="年龄" align="center" />
        <el-table-column prop="gender" label="性别" align="center">
          <template #default="scope">
            {{ scope.row.gender === 1 ? '男' : '女' }}
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="电话" align="center" />
        <el-table-column prop="job" label="职位" align="center">
          <template #default="scope">
            {{ getJobLabel(scope.row.job) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" align="center">
          <template #default="scope">
            {{ getStatusLabel(scope.row.status) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="scope">
            <el-button type="primary" size="small" icon="Edit" @click="handleEdit(scope.row)">编辑</el-button>
            <el-popconfirm :title="`你确定要删除${scope.row.name}?`" width="260px" @confirm="handleDelete(scope.row.id)">
              <template #reference>
                <el-button type="danger" size="small" icon="Delete">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页：修复 v-model 参数问题 -->
      <el-pagination
        :current-page="pageInfo.page"
        :page-size="pageInfo.pageSize"
        :page-sizes="[5, 10, 20, 50]"
        :total="total"
        layout="prev, pager, next, jumper, ->, sizes, total"
        background
        @current-change="handleCurrentChange"
        @size-change="handleSizeChange"
        class="pagination"
      />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editMode ? '编辑管理员' : '添加管理员'" width="30%">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="formData.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="年龄" prop="age">
          <el-input-number v-model="formData.age" :min="18" :max="60" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="formData.gender">
            <el-radio :label="1">男</el-radio>
            <el-radio :label="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入电话号码" />
        </el-form-item>
        <el-form-item label="职位" prop="job">
          <el-select v-model="formData.job" placeholder="请选择职位">
            <el-option label="安全管理员" :value="1"></el-option>
            <el-option label="设备管理员" :value="2"></el-option>
            <el-option label="工艺管理员" :value="3"></el-option>
            <el-option label="环保管理员" :value="4"></el-option>
            <el-option label="质检管理员" :value="5"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio label="1">工作中</el-radio>
            <el-radio label="2">空闲中</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import {
  ADMINISTRATOR_JOB_LABELS,
  ADMINISTRATOR_STATUS_LABELS,
  initialAdministratorDirectory,
  type AdministratorInfo,
  type AdministratorJob,
  type AdministratorStatus,
} from '@/data/personnelDirectory'

// 搜索表单
const searchForm = reactive({
  name: '',
  job: '',
  status: ''
})

// 分页信息
const pageInfo = reactive({
  page: 1,
  pageSize: 10
})

const allWorkerList = ref<AdministratorInfo[]>(initialAdministratorDirectory.map(item => ({ ...item })))

// 筛选后的数据（计算属性）
const filteredWorkerList = computed<AdministratorInfo[]>(() => {
  let result = [...allWorkerList.value]
  
  // 姓名筛选（模糊匹配）
  if (searchForm.name) {
    const keyword = searchForm.name.trim()
    result = result.filter(item => item.name.includes(keyword))
  }
  
  // 职位筛选
  if (searchForm.job) {
    result = result.filter(item => item.job === Number(searchForm.job))
  }
  
  // 状态筛选
  if (searchForm.status) {
    result = result.filter(item => item.status === searchForm.status)
  }
  
  return result
})

// 分页后展示的数据（计算属性）
const displayWorkerList = computed<AdministratorInfo[]>(() => {
  const start = (pageInfo.page - 1) * pageInfo.pageSize
  const end = start + pageInfo.pageSize
  return filteredWorkerList.value.slice(start, end)
})

// 总条数
const total = computed(() => filteredWorkerList.value.length)

// 对话框相关
const dialogVisible = ref(false)
const editMode = ref(false)
const formRef = ref<InstanceType<typeof ElForm>>()
const submitLoading = ref(false)

// 表单数据
const formData = reactive<AdministratorInfo>({
  id: undefined,
  name: '',
  age: 0,
  gender: 1,
  phone: '',
  job: 1,
  status: '1'
})

// 表单验证规则
const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  age: [{ required: true, message: '请输入年龄', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  phone: [{ required: true, message: '请输入电话号码', trigger: 'blur' }],
  job: [{ required: true, message: '请选择职位', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

// 职位标签映射（适配化工厂场景）
const getJobLabel = (job: number) => {
  return ADMINISTRATOR_JOB_LABELS[job as AdministratorJob] || '未知'
}

// 状态标签映射
const getStatusLabel = (status: string) => {
  return ADMINISTRATOR_STATUS_LABELS[status as AdministratorStatus] || '未知'
}

// 初始化加载
onMounted(() => {})

// 搜索按钮
const handleSearch = () => {
  pageInfo.page = 1 // 搜索后重置页码
}

// 重置按钮
const handleReset = () => {
  searchForm.name = ''
  searchForm.job = ''
  searchForm.status = ''
  pageInfo.page = 1
}

// 分页事件：手动更新分页数据
const handleSizeChange = (newSize: number) => {
  pageInfo.pageSize = newSize
  pageInfo.page = 1 // 切换页大小时重置页码
}

const handleCurrentChange = (newPage: number) => {
  pageInfo.page = newPage
}

// 添加管理员
const handleAdd = () => {
  editMode.value = false
  // 重置表单数据
  Object.assign(formData, {
    id: undefined,
    name: '',
    age: 0,
    gender: 1,
    phone: '',
    job: 1,
    status: '1'
  })
  
  dialogVisible.value = true
  // 清除表单验证结果
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

// 编辑管理员
const handleEdit = (row: AdministratorInfo) => {
  editMode.value = true
  Object.assign(formData, { ...row })
  dialogVisible.value = true
  // 清除表单验证结果
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

// 删除管理员
const handleDelete = (id: number) => {
  // 从原始数据中删除对应项
  allWorkerList.value = allWorkerList.value.filter(item => item.id !== id)
  ElMessage.success('删除成功')
}

// 提交表单
const handleSubmit = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return
  
  try {
    submitLoading.value = true
    
    if (editMode.value) {
      // 编辑模式：更新数据
      const index = allWorkerList.value.findIndex(item => item.id === formData.id)
      if (index !== -1) {
        allWorkerList.value[index] = { ...formData }
        ElMessage.success('编辑成功')
      }
    } else {
      // 新增模式：添加新数据（生成新ID）
      const newId = Math.max(...allWorkerList.value.map(item => item.id || 0)) + 1
      const newWorker = { ...formData, id: newId }
      allWorkerList.value.push(newWorker)
      ElMessage.success('添加成功')
    }
    
    dialogVisible.value = false
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error(editMode.value ? '编辑失败' : '添加失败')
  } finally {
    submitLoading.value = false
  }
}
</script>

<style scoped>
.worker-container {
  min-height: 100vh;
  padding: 32px;
  position: relative;
  overflow: hidden;
  background: transparent;
}

.worker-container > * {
  margin-bottom: 24px;
  position: relative;
  z-index: 1;
}

.worker-container > *:last-child {
  margin-bottom: 0;
}

/* 背景图片 */
.background-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: url('@/assets/images/background2.jpg') center/cover no-repeat;
  filter: blur(8px) brightness(0.4);
  z-index: 0;
  opacity: 0.8;
  pointer-events: none;
}

/* 统计卡片容器 */
.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

/* 统计卡片 */
.stat-card {
  background: rgba(10, 25, 50, 0.6) !important;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5), inset 0 0 1px rgba(64, 224, 208, 0.3);
  border: 1px solid rgba(64, 224, 208, 0.2) !important;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, #40e0d0, #0a5cad, #40e0d0);
  animation: gradientFlow 3s ease-in-out infinite;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(64, 224, 208, 0.2);
}

.stat-icon {
  font-size: 32px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(64, 224, 208, 0.1);
  border: 1px solid rgba(64, 224, 208, 0.3);
  border-radius: 12px;
  color: #40e0d0;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
  text-shadow: 0 0 10px rgba(64, 224, 208, 0.5);
}

.stat-label {
  font-size: 14px;
  color: #b8e8e4;
  font-weight: 500;
}

@keyframes gradientFlow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* 搜索表单 */
.search-form {
  margin-bottom: 0;
  padding: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
}

.search-form .el-form-item {
  margin-bottom: 0;
}

.search-form .el-select,
.search-form .el-input {
  width: 180px;
}

/* 卡片样式 */
.el-card {
  background: rgba(10, 25, 50, 0.6) !important;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(64, 224, 208, 0.2) !important;
  position: relative;
  overflow: hidden;
  color: #e0e6ed;
  margin-bottom: 24px;
}

:deep(.el-form-item__label) {
  color: #b8e8e4 !important;
}

:deep(.el-input__wrapper), :deep(.el-textarea__inner) {
  background-color: rgba(0, 0, 0, 0.2) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

:deep(.el-input__wrapper:focus-within), :deep(.el-textarea__inner:focus) {
  border-color: #40e0d0;
  box-shadow: 0 0 0 1px #40e0d0 !important;
}

:deep(.el-input__inner) {
  color: #fff !important;
}

:deep(.el-radio__label) {
  color: #e0e6ed !important;
}

:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  background: rgba(0, 0, 0, 0.3) !important;
  color: #40e0d0 !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
}

/* 表格内边框和鼠标悬停 */
:deep(.el-table--border .el-table__inner-wrapper::after),
:deep(.el-table--border::after),
:deep(.el-table--border::before),
:deep(.el-table__inner-wrapper::before) {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-table--border .el-table__cell) {
  border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-table__empty-block) {
  background-color: transparent !important;
}

:deep(.el-table__empty-text) {
  color: #b8e8e4 !important;
}
.el-table {
  border-radius: 12px;
  overflow: hidden;
  background-color: transparent !important;
  color: #e0e6ed;
}

:deep(.el-table) {
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: transparent !important;
  --el-table-row-hover-bg-color: rgba(64, 224, 208, 0.1) !important;
  --el-table-border-color: rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-table-fixed-column--right), :deep(.el-table-fixed-column--left) {
  background-color: rgba(10, 25, 50, 0.8) !important;
}

:deep(.el-table th.el-table__cell) {
  background: rgba(0, 0, 0, 0.3) !important;
  color: #40e0d0 !important;
  border-bottom: 1px solid rgba(64, 224, 208, 0.3) !important;
  font-weight: 600;
  padding: 16px;
  font-size: 14px;
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
  padding: 14px;
  font-size: 14px;
  color: #e0e6ed !important;
  background-color: transparent !important;
}

.el-table tr {
  transition: all 0.3s ease;
}

.el-table tr:nth-child(even) {
  background: rgba(64, 224, 208, 0.02) !important;
}

/* 添加悬浮行固定列背景透明适配 */
:deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: rgba(64, 224, 208, 0.1) !important;
}

.el-table .cell {
  white-space: normal;
  word-break: break-word;
}

.el-table .el-button {
  margin-right: 8px;
}

.el-table .el-button:last-child {
  margin-right: 0;
}

/* 分页样式 */
.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  padding: 16px;
  background: rgba(10, 25, 50, 0.6) !important;
  border-radius: 12px;
  border: 1px solid rgba(64, 224, 208, 0.2);
}

.el-pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-pagination.is-background .el-pager li) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  color: #e0e6ed !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

:deep(.el-pagination.is-background .el-pager li.is-active) {
  background-color: #40e0d0 !important;
  color: #0a192f !important;
  border-color: #40e0d0;
}

:deep(.el-pagination.is-background .btn-next),
:deep(.el-pagination.is-background .btn-prev) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  color: #e0e6ed !important;
}

/* 对话框样式 */
:deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  background: rgba(10, 25, 50, 0.95) !important;
  border: 1px solid rgba(64, 224, 208, 0.2);
}

:deep(.el-dialog__header) {
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(64, 224, 208, 0.2);
  margin-right: 0 !important;
  padding: 20px;
}

:deep(.el-dialog__title) {
  color: #40e0d0;
  font-weight: 600;
}

:deep(.el-dialog__body) {
  color: #e0e6ed;
  padding: 20px;
}

:deep(.el-dialog__footer) {
  border-top: 1px solid rgba(64, 224, 208, 0.2);
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.3);
}

/* 按钮样式 */
.el-button {
  border-radius: 8px;
  transition: all 0.3s ease;
  font-weight: 500;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e0e6ed;
}

.el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 224, 208, 0.3);
  border-color: #40e0d0;
  color: #40e0d0;
}

.el-button--primary {
  background: linear-gradient(90deg, #40e0d0, #0a5cad);
  border: none;
  color: #fff;
}

.el-button--primary:hover {
  background: linear-gradient(90deg, #40e0d0, #40e0d0);
  box-shadow: 0 4px 12px rgba(64, 224, 208, 0.4);
}



.el-button--danger {
  background: linear-gradient(90deg, #ff4d4f, #ff7875);
  border: none;
  color: #fff;
  box-shadow: 0 2px 8px rgba(255, 77, 79, 0.4);
}

.el-button--danger:hover {
  background: linear-gradient(90deg, #ff7875, #ff4d4f);
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.6);
  color: #fff;
}
</style>
