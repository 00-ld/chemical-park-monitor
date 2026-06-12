# Migrations 目录

本目录用于存放数据库版本迁移脚本。当前已有迁移脚本位于 `deploy/mysql/migration_add_role.sql`。

新增迁移脚本时请遵循：

- 文件名使用递增编号和简短说明，例如 `002_add_warning_event_table.sql`。
- 每个迁移只做一类结构变更，避免混入大量种子数据。
- 迁移脚本必须可重复审查，危险操作需要在注释中说明影响范围。
- 更新后同步维护 `db/manifest.json` 和接口/部署文档。
