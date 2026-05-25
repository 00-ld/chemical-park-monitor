-- 传感器表
-- 存储用户手动布设的传感器信息
CREATE TABLE IF NOT EXISTS `sensor` (
    `id`                 VARCHAR(50)  NOT NULL COMMENT '传感器工程编号 (如 TK-01)',
    `x`                  DOUBLE       NOT NULL COMMENT '地图 X 坐标',
    `y`                  DOUBLE       NOT NULL COMMENT '地图 Y 坐标',
    `installation_height` DOUBLE      DEFAULT 1.5 COMMENT '安装高度 (m)',
    `effective_range`    DOUBLE       DEFAULT 30 COMMENT '有效监测范围 (m)',
    `detection_range`    VARCHAR(200) DEFAULT 'CO / 可燃气体 / H2S / O2' COMMENT '检测气体范围（预留）',
    `install_remark`     VARCHAR(500) DEFAULT '' COMMENT '布点说明 / 备注',
    `priority`           INT          DEFAULT 2 COMMENT '优先级 1=高危 2=常规 3=辅助',
    `risk`               DOUBLE       DEFAULT 0.3 COMMENT '风险值 0~1',
    `type`               VARCHAR(20)  DEFAULT 'gas' COMMENT '传感器类型',
    `mode`               VARCHAR(10)  DEFAULT 'auto' COMMENT '数据模式 auto/manual',
    `last_sample_time`   BIGINT       DEFAULT NULL COMMENT '最后采样时间戳',
    `created_at`         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器布点表';
