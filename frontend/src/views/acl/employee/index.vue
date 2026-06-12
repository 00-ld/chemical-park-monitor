<template>
  <div class="employee-container">
    <!-- 背景图片 -->
    <div class="background-image"></div>
    <!-- 统计卡片 -->
    <div class="stats-container">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <div class="stat-value">{{ allEmployeeList.length }}</div>
          <div class="stat-label">总员工数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ allEmployeeList.filter(item => item.status === '在岗').length }}</div>
          <div class="stat-label">在岗员工</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🏖️</div>
        <div class="stat-content">
          <div class="stat-value">{{ allEmployeeList.filter(item => item.status === '休假').length }}</div>
          <div class="stat-label">休假员工</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-content">
          <div class="stat-value">{{ allEmployeeList.filter(item => item.status === '离职').length }}</div>
          <div class="stat-label">离职员工</div>
        </div>
      </div>
    </div>

    <!-- 搜索表单 -->
    <el-card>
      <el-form :model="searchForm" inline class="search-form">
        <el-form-item label="在岗状态">
          <el-select v-model="searchForm.status" placeholder="请选择在岗状态" clearable style="width: 150px;">
            <el-option label="全部" value="" />
            <el-option label="在岗" value="在岗" />
            <el-option label="休假" value="休假" />
            <el-option label="离职" value="离职" />
          </el-select>
        </el-form-item>
        <el-form-item label="员工姓名">
          <el-input v-model="searchForm.name" placeholder="请输入员工姓名" clearable />
        </el-form-item>
        <el-form-item label="工号">
          <el-input v-model.number="searchForm.employeeId" placeholder="请输入工号" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card style="margin: 10px 0;">
      <el-button type="primary" size="default" icon="Plus" @click="handleAdd">添加员工</el-button>
      <el-table :data="displayEmployeeList" border stripe style="margin: 10px 0;">
        <el-table-column type="index" label="id" width="60" align="center" />
        <el-table-column prop="name" label="员工姓名" align="center" />
        <el-table-column prop="age" label="年龄" align="center" />
        <el-table-column prop="gender" label="性别" align="center">
          <template #default="scope">
            {{ scope.row.gender === 1 ? '男' : '女' }}
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="联系电话" align="center" />
        <el-table-column prop="department" label="所属部门" align="center" />
        <el-table-column prop="employeeId" label="工号" align="center" />
        <el-table-column prop="status" label="在岗状态" align="center" />
        <el-table-column prop="jobDesc" label="岗位职责" align="center" show-overflow-tooltip />
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

      <!-- 分页 -->
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="page"
        :page-sizes="[5, 10, 20, 50]"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, jumper, ->, sizes, total"
        background
        class="pagination"
      />
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editMode ? '编辑员工信息' : '添加员工信息'" width="30%">
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="员工姓名" prop="name">
          <el-input v-model="formData.name" placeholder="请输入员工姓名" />
        </el-form-item>
        <el-form-item label="年龄" prop="age">
          <el-input-number v-model="formData.age" :min="18" :max="60" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="formData.gender">
            <el-radio :label="1">男</el-radio>
            <el-radio :label="0">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="所属部门" prop="department">
          <el-input v-model="formData.department" placeholder="请输入所属部门" />
        </el-form-item>
        <el-form-item label="工号" prop="employeeId">
          <el-input-number v-model="formData.employeeId" :min="1000" />
        </el-form-item>
        <el-form-item label="在岗状态" prop="status">
          <el-select v-model="formData.status" placeholder="请选择在岗状态">
            <el-option label="在岗" value="在岗" />
            <el-option label="休假" value="休假" />
            <el-option label="离职" value="离职" />
          </el-select>
        </el-form-item>
        <el-form-item label="岗位职责" prop="jobDesc">
          <el-input v-model="formData.jobDesc" placeholder="请输入岗位职责" type="textarea" />
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
import { ref, onMounted, reactive, nextTick, computed } from 'vue'
import { ElMessage, ElForm } from 'element-plus'

// 定义员工数据类型（适配化工园区场景）
interface EmployeeItem {
  id: number
  name: string
  age: number
  gender: 0 | 1
  phone: string
  department: string
  employeeId: number
  status: '在岗' | '休假' | '离职'
  jobDesc: string
}

// 搜索表单
const searchForm = ref({
  status: '' as '在岗' | '休假' | '离职' | '',
  name: '',
  employeeId: undefined as number | undefined,
})

// 原始完整数据（15条化工园区员工固定数据）
const allEmployeeList = ref<EmployeeItem[]>([
  { id: 1, name: '李伟', age: 45, gender: 1, phone: '13800138001', department: '生产部', employeeId: 1001, status: '在岗', jobDesc: '负责化工生产线日常巡检，设备维护保养，确保生产安全运行' },
  { id: 2, name: '张丽', age: 38, gender: 0, phone: '13800138002', department: '安全部', employeeId: 1002, status: '在岗', jobDesc: '制定安全管理制度，开展安全培训，排查园区安全隐患' },
  { id: 3, name: '王强', age: 50, gender: 1, phone: '13800138003', department: '技术部', employeeId: 1003, status: '休假', jobDesc: '研发化工工艺优化方案，解决生产技术难题，指导现场操作' },
  { id: 4, name: '刘芳', age: 35, gender: 0, phone: '13800138004', department: '质检部', employeeId: 1004, status: '在岗', jobDesc: '检测化工产品质量，记录检测数据，出具质量检验报告' },
  { id: 5, name: '赵刚', age: 42, gender: 1, phone: '13800138005', department: '设备部', employeeId: 1005, status: '在岗', jobDesc: '管理生产设备台账，定期检修设备，保障设备正常运转' },
  { id: 6, name: '孙梅', age: 39, gender: 0, phone: '13800138006', department: '行政部', employeeId: 1006, status: '离职', jobDesc: '负责园区行政事务，员工考勤管理，办公用品采购' },
  { id: 7, name: '周军', age: 48, gender: 1, phone: '13800138007', department: '环保部', employeeId: 1007, status: '在岗', jobDesc: '监测园区排污情况，落实环保政策，处理环保投诉' },
  { id: 8, name: '吴燕', age: 33, gender: 0, phone: '13800138008', department: '财务部', employeeId: 1008, status: '在岗', jobDesc: '核算生产成本，处理财务报销，编制财务报表' },
  { id: 9, name: '郑涛', age: 46, gender: 1, phone: '13800138009', department: '仓储部', employeeId: 1009, status: '休假', jobDesc: '管理化工原料仓储，把控物料进出库，盘点库存数量' },
  { id: 10, name: '钱丽', age: 37, gender: 0, phone: '13800138010', department: '采购部', employeeId: 1010, status: '在岗', jobDesc: '采购化工原料，洽谈供应商合作，控制采购成本' },
  { id: 11, name: '冯伟', age: 44, gender: 1, phone: '13800138011', department: '销售部', employeeId: 1011, status: '在岗', jobDesc: '拓展化工产品市场，维护客户关系，完成销售指标' },
  { id: 12, name: '陈静', age: 36, gender: 0, phone: '13800138012', department: '人事部', employeeId: 1012, status: '离职', jobDesc: '负责员工招聘，办理入职离职，组织员工培训' },
  { id: 13, name: '褚亮', age: 41, gender: 1, phone: '13800138013', department: '工程部', employeeId: 1013, status: '在岗', jobDesc: '负责园区基建工程，维护园区基础设施，处理工程维修' },
  { id: 14, name: '卫华', age: 49, gender: 1, phone: '13800138014', department: '应急部', employeeId: 1014, status: '在岗', jobDesc: '制定应急救援预案，组织应急演练，处理突发安全事件' },
  { id: 15, name: '蒋欣', age: 34, gender: 0, phone: '13800138015', department: '研发部', employeeId: 1015, status: '休假', jobDesc: '开展新型化工产品研发，撰写研发报告，申请技术专利' }
])

// 分页相关
const page = ref(1)
const pageSize = ref(10)
const total = ref(allEmployeeList.value.length)

// 筛选后的数据（计算属性）
const filteredEmployeeList = computed<EmployeeItem[]>(() => {
  let result = [...allEmployeeList.value]
  
  // 状态筛选
  if (searchForm.value.status) {
    result = result.filter(item => item.status === searchForm.value.status)
  }
  
  // 姓名筛选（模糊匹配）
  if (searchForm.value.name) {
    const keyword = searchForm.value.name.trim()
    result = result.filter(item => item.name.includes(keyword))
  }
  
  // 工号筛选
  if (searchForm.value.employeeId !== undefined) {
    result = result.filter(item => item.employeeId === searchForm.value.employeeId)
  }
  
  return result
})

// 分页后展示的数据（计算属性）
const displayEmployeeList = computed<EmployeeItem[]>(() => {
  const start = (page.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredEmployeeList.value.slice(start, end)
})

// 监听筛选结果变化，更新总条数
onMounted(() => {
  total.value = filteredEmployeeList.value.length
})

// 对话框相关
const dialogVisible = ref(false)
const editMode = ref(false)
const formRef = ref<InstanceType<typeof ElForm>>()
const submitLoading = ref(false)

// 表单数据
const formData = reactive<EmployeeItem>({
  id: 0,
  name: '',
  age: 0,
  gender: 1,
  phone: '',
  department: '',
  employeeId: 0,
  status: '在岗',
  jobDesc: ''
})

// 表单验证规则
const rules = {
  name: [{ required: true, message: '请输入员工姓名', trigger: 'blur' }],
  age: [{ required: true, message: '请输入年龄', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }],
  department: [{ required: true, message: '请输入所属部门', trigger: 'blur' }],
  employeeId: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  status: [{ required: true, message: '请选择在岗状态', trigger: 'change' }],
  jobDesc: [{ required: true, message: '请输入岗位职责', trigger: 'blur' }]
}

// 搜索按钮
const handleSearch = () => {
  page.value = 1 // 搜索后重置页码
  total.value = filteredEmployeeList.value.length
}

// 重置按钮
const handleReset = () => {
  searchForm.value = {
    status: '',
    name: '',
    employeeId: undefined
  }
  page.value = 1
  total.value = filteredEmployeeList.value.length
}

// 分页事件
const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  page.value = 1 // 切换页大小时重置页码
}

const handleCurrentChange = (newPage: number) => {
  page.value = newPage
}

// 添加员工
const handleAdd = () => {
  editMode.value = false
  // 重置表单数据
  Object.assign(formData, {
    id: 0,
    name: '',
    age: 0,
    gender: 1,
    phone: '',
    department: '',
    employeeId: 0,
    status: '在岗',
    jobDesc: ''
  })
  
  dialogVisible.value = true
  // 清除表单验证结果
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

// 编辑员工
const handleEdit = (row: EmployeeItem) => {
  editMode.value = true
  Object.assign(formData, { ...row })
  dialogVisible.value = true
  // 清除表单验证结果
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

// 删除员工
const handleDelete = (id: number) => {
  // 从原始数据中删除对应项
  allEmployeeList.value = allEmployeeList.value.filter(item => item.id !== id)
  // 更新总条数
  total.value = filteredEmployeeList.value.length
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
      const index = allEmployeeList.value.findIndex(item => item.id === formData.id)
      if (index !== -1) {
        allEmployeeList.value[index] = { ...formData }
        ElMessage.success('编辑成功')
      }
    } else {
      // 新增模式：添加新数据（生成新ID）
      const newId = Math.max(...allEmployeeList.value.map(item => item.id)) + 1
      const newEmployee = { ...formData, id: newId }
      allEmployeeList.value.push(newEmployee)
      ElMessage.success('添加成功')
    }
    
    dialogVisible.value = false
    // 更新总条数
    total.value = filteredEmployeeList.value.length
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error(editMode.value ? '编辑失败' : '添加失败')
  } finally {
    submitLoading.value = false
  }
}
</script>

<style scoped>
.employee-container {
  min-height: 100vh;
  padding: 32px;
  position: relative;
  overflow: hidden;
  background: transparent;
}

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

.employee-container > * {
  position: relative;
  z-index: 1;
}

.employee-container > * {
  margin-bottom: 24px;
}

.employee-container > *:last-child {
  margin-bottom: 0;
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
  color: #fff !important;
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

.el-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(64, 224, 208, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 224, 208, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
  z-index: 0;
}

.el-card::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, rgba(64, 224, 208, 0.15) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 0.8; }
}

.el-card > * {
  position: relative;
  z-index: 1;
}

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
