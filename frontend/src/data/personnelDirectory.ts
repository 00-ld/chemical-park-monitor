// Local anonymized seed data for personnel pages before backend integration.
// These records are not real people and must not be used as production data.
export type EmployeeStatus = '在岗' | '休假' | '离职'

export interface EmployeeItem {
  id: number
  name: string
  age: number
  gender: 0 | 1
  phone: string
  department: string
  employeeId: number
  status: EmployeeStatus
  jobDesc: string
}

export type AdministratorJob = 1 | 2 | 3 | 4 | 5
export type AdministratorStatus = '1' | '2'

export interface AdministratorInfo {
  id: number | undefined
  name: string
  age: number
  gender: 1 | 2
  phone: string
  job: AdministratorJob
  status: AdministratorStatus
}

export const ADMINISTRATOR_JOB_LABELS: Record<AdministratorJob, string> = {
  1: '安全管理员',
  2: '设备管理员',
  3: '工艺管理员',
  4: '环保管理员',
  5: '质检管理员',
}

export const ADMINISTRATOR_STATUS_LABELS: Record<AdministratorStatus, string> = {
  '1': '工作中',
  '2': '空闲中',
}

export const initialEmployeeDirectory: EmployeeItem[] = [
  { id: 1, name: '员工-1001', age: 45, gender: 1, phone: '园区内线 6101', department: '生产部', employeeId: 1001, status: '在岗', jobDesc: '负责化工生产线日常巡检、设备维护保养和安全运行记录' },
  { id: 2, name: '员工-1002', age: 38, gender: 0, phone: '园区内线 6102', department: '安全部', employeeId: 1002, status: '在岗', jobDesc: '制定安全管理制度、开展安全培训并排查园区安全隐患' },
  { id: 3, name: '员工-1003', age: 50, gender: 1, phone: '园区内线 6103', department: '技术部', employeeId: 1003, status: '休假', jobDesc: '研发化工工艺优化方案、解决生产技术问题并指导现场操作' },
  { id: 4, name: '员工-1004', age: 35, gender: 0, phone: '园区内线 6104', department: '质检部', employeeId: 1004, status: '在岗', jobDesc: '检测化工产品质量、记录检测数据并出具质量检验报告' },
  { id: 5, name: '员工-1005', age: 42, gender: 1, phone: '园区内线 6105', department: '设备部', employeeId: 1005, status: '在岗', jobDesc: '管理生产设备台账、定期检修设备并保障设备正常运转' },
  { id: 6, name: '员工-1006', age: 39, gender: 0, phone: '园区内线 6106', department: '行政部', employeeId: 1006, status: '离职', jobDesc: '负责园区行政事务、员工考勤管理和办公用品采购' },
  { id: 7, name: '员工-1007', age: 48, gender: 1, phone: '园区内线 6107', department: '环保部', employeeId: 1007, status: '在岗', jobDesc: '监测园区排污情况、落实环保政策并处理环保投诉' },
  { id: 8, name: '员工-1008', age: 33, gender: 0, phone: '园区内线 6108', department: '财务部', employeeId: 1008, status: '在岗', jobDesc: '核算生产成本、处理财务报销并编制财务报表' },
  { id: 9, name: '员工-1009', age: 46, gender: 1, phone: '园区内线 6109', department: '仓储部', employeeId: 1009, status: '休假', jobDesc: '管理化工原料仓储、把控物料进出库并盘点库存数量' },
  { id: 10, name: '员工-1010', age: 37, gender: 0, phone: '园区内线 6110', department: '采购部', employeeId: 1010, status: '在岗', jobDesc: '采购化工原料、维护供应商合作并控制采购成本' },
  { id: 11, name: '员工-1011', age: 44, gender: 1, phone: '园区内线 6111', department: '销售部', employeeId: 1011, status: '在岗', jobDesc: '拓展化工产品市场、维护客户关系并完成销售指标' },
  { id: 12, name: '员工-1012', age: 36, gender: 0, phone: '园区内线 6112', department: '人事部', employeeId: 1012, status: '离职', jobDesc: '负责员工招聘、办理入职离职并组织员工培训' },
  { id: 13, name: '员工-1013', age: 41, gender: 1, phone: '园区内线 6113', department: '工程部', employeeId: 1013, status: '在岗', jobDesc: '负责园区基建工程、维护基础设施并处理工程维修' },
  { id: 14, name: '员工-1014', age: 49, gender: 1, phone: '园区内线 6114', department: '应急部', employeeId: 1014, status: '在岗', jobDesc: '制定应急救援预案、组织应急演练并处理突发安全事件' },
  { id: 15, name: '员工-1015', age: 34, gender: 0, phone: '园区内线 6115', department: '研发部', employeeId: 1015, status: '休假', jobDesc: '开展新型化工产品研发、撰写研发报告并申请技术专利' },
]

export const initialAdministratorDirectory: AdministratorInfo[] = [
  { id: 1, name: '管理员-安全-01', age: 45, gender: 1, phone: '园区内线 6201', job: 1, status: '1' },
  { id: 2, name: '管理员-设备-01', age: 38, gender: 2, phone: '园区内线 6202', job: 2, status: '1' },
  { id: 3, name: '管理员-工艺-01', age: 42, gender: 1, phone: '园区内线 6203', job: 3, status: '2' },
  { id: 4, name: '管理员-环保-01', age: 36, gender: 2, phone: '园区内线 6204', job: 4, status: '1' },
  { id: 5, name: '管理员-质检-01', age: 48, gender: 1, phone: '园区内线 6205', job: 5, status: '1' },
  { id: 6, name: '管理员-安全-02', age: 39, gender: 2, phone: '园区内线 6206', job: 1, status: '2' },
  { id: 7, name: '管理员-设备-02', age: 41, gender: 1, phone: '园区内线 6207', job: 2, status: '1' },
  { id: 8, name: '管理员-工艺-02', age: 37, gender: 2, phone: '园区内线 6208', job: 3, status: '1' },
  { id: 9, name: '管理员-环保-02', age: 44, gender: 1, phone: '园区内线 6209', job: 4, status: '2' },
  { id: 10, name: '管理员-质检-02', age: 35, gender: 2, phone: '园区内线 6210', job: 5, status: '1' },
  { id: 11, name: '管理员-安全-03', age: 46, gender: 1, phone: '园区内线 6211', job: 1, status: '1' },
  { id: 12, name: '管理员-设备-03', age: 40, gender: 2, phone: '园区内线 6212', job: 2, status: '2' },
  { id: 13, name: '管理员-工艺-03', age: 43, gender: 1, phone: '园区内线 6213', job: 3, status: '1' },
  { id: 14, name: '管理员-环保-03', age: 34, gender: 2, phone: '园区内线 6214', job: 4, status: '1' },
  { id: 15, name: '管理员-质检-03', age: 47, gender: 1, phone: '园区内线 6215', job: 5, status: '2' },
]
