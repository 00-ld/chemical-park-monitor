# 数据库目录说明

`db/` 是项目数据库资产的统一入口，用于说明 MySQL 初始化、迁移、种子数据、测试数据、ER 说明和备份规则。

当前运行中的 SQL 脚本仍保留在原有位置，避免破坏 Docker 部署和 Spring Boot 本地启动路径。`db/manifest.json` 记录这些脚本的职责和维护状态，后续新增数据库文件应优先放入本目录对应子文件夹。

## 目录结构

```text
db/
  README.md
  manifest.json
  schema/       # 建表脚本说明
  migrations/   # 版本迁移脚本说明
  seed/         # 种子数据说明
  test_data/    # 数据库测试数据说明
  er/           # ER 图、表关系和字段说明
  backups/      # 本地备份占位目录，真实备份禁止提交
```

## 当前脚本索引

| 类型 | 当前文件 | 用途 |
| --- | --- | --- |
| 初始化 | `deploy/mysql/init.sql` | Docker MySQL 容器启动时执行的主初始化脚本。 |
| 迁移 | `deploy/mysql/migration_add_role.sql` | 为用户表增加角色字段的迁移脚本。 |
| 种子数据 | `deploy/mysql/sensor_data.sql` | 传感器点位种子数据。 |
| 后端本地资源 | `Back/src/main/resources/schema-gas.sql` | 气体类型表局部建表脚本。 |
| 后端本地资源 | `Back/src/main/resources/schema-sensor.sql` | 传感器与布局表局部建表脚本。 |
| 后端本地资源 | `Back/src/main/resources/init-sensor-db.sql` | 传感器相关初始化脚本。 |

## 强制要求

- 数据库使用 MySQL，字符集统一使用 `utf8mb4`。
- SQL 文件不得写入生产数据库密码、真实用户密码、API Key、token 密钥或其他敏感配置。
- 表结构变更必须新增迁移脚本，并同步更新 `db/manifest.json` 与相关接口文档。
- 种子数据必须是可公开、可复现、可脱敏的数据，不得包含真实生产用户数据或真实事故敏感数据。
- 真实数据库备份、导出文件和本地调试数据禁止提交到 GitHub。
- SQL 注释和 Markdown 文档必须保持 UTF-8，可读、可检索、可维护。

## 后续整理方向

1. 将 `deploy/mysql/init.sql` 拆分为 `db/schema/001_init.sql`、`db/seed/001_seed_sensor.sql` 等小文件。
2. 保留 `deploy/mysql/init.sql` 作为部署聚合脚本，由脚本或文档明确生成来源。
3. 为核心业务表补充 ER 图或字段字典，至少覆盖用户、传感器、小车、气体数据、告警、扩散任务、溯源任务和路径规划任务。
