# GasModelTest — 气体扩散 / 溯源模型测试数据集

用于验证 **气体扩散模型(正向)** 与 **气体溯源模型(反演)** 的可复现合成数据集。
纯解析解生成,带已知真值,可直接做精度评估与算法回归测试。

## 快速开始

```bash
python generate_dataset.py     # 依赖 numpy / scipy / pandas
```

所有参数集中在 `config.json`,固定随机种子 (`20260608`),数据完全可复现。
改参数后重跑脚本即可重新生成。

## 单位与坐标约定

| 量 | 单位 | 说明 |
|----|------|------|
| 坐标 x / y / z | m | x=下风向距离, y=横风向, z=垂直高度 |
| 风速 u | m/s | |
| 源强 Q | g/s | 连续源 |
| 瞬时质量 mass | g | 烟团一次性释放总量 |
| 浓度 C | mg/m³ | 1 mg/m³ = 1000 µg/m³ |
| 风向 | 度 | 气象约定:风的**来向**,270=正西来风(吹向东) |

扩散系数 σy、σz 采用 **Briggs 开阔乡村(open-country)Pasquill-Gifford** 公式,
稳定度分 A(强不稳定)→ F(强稳定)六档。

## 目录与文件

```
GasModelTest/
├── config.json                 全局参数
├── generate_dataset.py         生成脚本(可复现)
├── case01_gaussian_plume/      场景1:高斯烟羽稳态浓度场
│   ├── stability_A.csv ~ F.csv 6档稳定度的地面(z=0)浓度场; 行=y, 列=x
│   ├── plume_3d_D.npy          中性D的3D体数据, shape [nx,ny,nz]=[201,101,41]
│   └── meta.json
├── case02_puff_timeseries/     场景2:瞬时烟团时序
│   ├── puff_concentration.npy  浓度演化, shape [nt,ny,nx]=[61,101,201] (地面)
│   ├── receptor_timeseries.csv 4个受体点浓度时间曲线
│   └── meta.json
├── case03_sensor_observations/ 场景3:传感器观测(溯源核心输入)
│   ├── sensors.csv             15个传感器坐标
│   ├── observations.csv        conc_true + conc_observed(含噪)
│   ├── ground_truth.json       真源参数(评估用,禁止作反演输入)
│   └── meta.json
└── case04_multi_source/        场景4:多源 + 时变风场
    ├── wind_field.csv          时变风速/风向
    ├── observations.csv        多源叠加观测 + 各源贡献
    ├── ground_truth.json       3个真源参数
    └── meta.json
```

## 各场景用途

**Case 1 — 高斯烟羽稳态**
连续点源(H=50m, Q=100g/s, u=5m/s)在 6 档稳定度下的解析浓度场。
用途:验证扩散模型实现是否复现解析解;对比不同稳定度的浓度衰减与展宽。
随稳定度 A→F,地面峰值浓度下降、烟羽变窄——符合物理预期。

**Case 2 — 瞬时烟团时序**
单次瞬时释放(mass=5000g),烟团随风平流、σ 随漂移距离增长。
用途:测试动态扩散、烟团到达时间、受体点浓度峰值与时刻。
注:近源极早期受体浓度为极小值(烟团尚未到达),属正常物理现象。

**Case 3 — 传感器观测(溯源标准输入)**
在已知真源基础上,15 个随机布点传感器采样并叠加高斯噪声(SNR=20dB)。
用途:溯源反演的标准输入。**反演只能用 `observations.csv` 的 `conc_observed` 列**;
`conc_true` 与 `ground_truth.json` 仅用于评估反演结果误差,严禁作为反演输入(防数据泄漏)。

**Case 4 — 多源 / 复杂气象**
3 个真源叠加 + 时变风场(风速风向正弦扰动),SNR=18dB。
用途:高难度多源辨识、源强联合估计、可辨识性分析。
`observations.csv` 额外保留每个源的贡献列(`contrib_S1/S2/S3`),便于诊断。

## 溯源评估建议

1. 仅以 `conc_observed` + 传感器坐标 + 气象条件作为反演输入。
2. 反演得到源位置/强度后,与 `ground_truth.json` 对比:
   - 位置误差:估计源与真源的欧氏距离 (m)
   - 源强误差:相对误差 |Q_est − Q_true| / Q_true
3. 正向模型精度建议指标:FAC2、FB(分数偏差)、NMSE(归一化均方误差)。

## 注意事项

- 高斯烟羽假设:平坦地形、定常均匀风场、源下风向 x>0 区域有效。复杂地形/近场建筑绕流不适用,需 CFD。
- 所有数据为**合成解析解**,不含真实大气湍流间歇性,适合算法验证,不能替代实测标定。
- 控制台输出若出现中文乱码,是 Windows GBK 终端显示问题,文件内容均为 UTF-8,不影响数据。
