# 数据集来源台账

本文档用于记录气体扩散、溯源、路径规划和传感器校验相关数据来源。所有真实数据集接入前必须记录下载时间、版本、许可证、预处理步骤、字段说明和适用边界；未完成下载或未完成授权确认的数据不得在报告中写成“已使用真实数据验证”。

## 当前仓库数据状态

| 数据目录 | 状态 | 数据性质 | 说明 |
| --- | --- | --- | --- |
| `GasModelTest/` | 已提交 | 合成解析数据 | 用高斯烟羽/烟团解析公式和固定随机种子生成，用于算法回归测试，不是现场实测数据。 |
| `python/diffusion/test_*` | 已提交 | 单元/回归验证 | 用物理不变量、公式基准和数值收敛检查验证扩散实现。 |
| `.npy` 体数据 | 不提交 | 本地生成产物 | 由 `GasModelTest/generate_dataset.py` 生成，因体积和可复现性原因不进 GitHub。 |

## 候选权威来源

| 来源 | 用途 | 接入状态 | 备注 |
| --- | --- | --- | --- |
| NIST Chemistry WebBook, SRD 69 | CO、O2、NH3、CH4 等气体分子量、热物性、化学物性参数 | 候选 | 用于校验气体参数表，注意 NIST WebBook 的版权和使用说明。 |
| NOAA NCEI Integrated Surface Database (ISD) | 风速、风向、温度、露点、气压、能见度等气象实况 | 候选 | 可用于构造真实气象边界条件；需要按站点、时间范围下载并保留元数据。 |
| HARMO classic dispersion datasets | Prairie Grass、Kincaid、Round Hill 等经典扩散模型评估数据 | 候选 | 适合模型评估，但需要确认具体数据包、字段和引用方式。 |
| Jack Rabbit Program / Jack Rabbit II | 氯气、氨气等危险气体大规模释放实验参考 | 候选 | 更偏危险气体事故级场景；数据敏感性和公开可用范围需要单独确认。 |

## 来源链接

- NIST Chemistry WebBook, SRD 69: https://webbook.nist.gov/chemistry/
- NIST CO 示例页: https://webbook.nist.gov/cgi/cbook.cgi?ID=630-08-0
- NOAA NCEI ISD: https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
- NOAA ISD HTTPS 数据入口: https://www.ncei.noaa.gov/data/global-hourly/
- HARMO classic datasets: https://www.harmo.org/classic.php
- Jack Rabbit Program: https://www.uvu.edu/es/jack-rabbit/

## 接入流程

1. 明确验证目标：扩散模型、溯源模型、路径规划、气体物性或气象边界。
2. 下载原始数据到未提交目录，例如 `datasets/raw/`，并记录来源 URL、下载日期、版本和许可证。
3. 编写预处理脚本，将清洗结果输出到 `datasets/processed/`，保留字段映射和单位换算说明。
4. 建立测试用例，记录输入参数、评价指标、误差、失败场景和适用边界。
5. 只提交小体积、脱敏、授权明确的数据样例；大体积原始数据用外部存储或下载脚本复现。

## 禁止事项

- 不得把合成数据写成真实实测数据。
- 不得提交未授权、未脱敏、来源不清的数据。
- 不得提交真实事故敏感数据、生产数据库导出或人员隐私数据。
- 不得只写“来自权威网站”，必须记录具体 URL、下载时间和处理脚本。
- 不得用大模型生成的数据冒充真实实验数据。
