-- ========================================
-- 迁移脚本: 为 user 表增加角色字段 (H-1 授权层)
-- 角色: admin=管理员(可执行增删改写操作), user=普通用户(仅只读 GET)
-- ========================================
USE `chemical`;

-- 为 user 表增加角色字段，默认普通用户
ALTER TABLE `user`
    ADD COLUMN `role` VARCHAR(16) NOT NULL DEFAULT 'user'
    COMMENT '角色: admin=管理员可写, user=普通用户只读';

-- 首次迁移：将已有账号提升为管理员（按需调整；新注册账号一律强制为 user）
-- 谨慎执行：确认现有 user 表中均为可信管理账号后再放开下一行
-- UPDATE `user` SET `role` = 'admin';
