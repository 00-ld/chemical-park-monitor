-- 传感器表
-- 存储用户手动布设的传感器信息
CREATE TABLE IF NOT EXISTS `sensor` (
    `id`                 VARCHAR(50)  NOT NULL COMMENT '传感器工程编号 (如 TK-01)',
    `x`                  DOUBLE       NOT NULL COMMENT '地图 X 坐标',
    `y`                  DOUBLE       NOT NULL COMMENT '地图 Y 坐标',
    `installation_height` DOUBLE      DEFAULT 1.5 COMMENT '安装高度 (m)',
    `effective_range`    DOUBLE       DEFAULT 20 COMMENT '有效监测范围 (m)',
    `detection_range`    VARCHAR(200) DEFAULT 'CO / CH4 / NH3 / O2' COMMENT '检测气体范围（预留）',
    `install_remark`     VARCHAR(500) DEFAULT '' COMMENT '布点说明 / 备注',
    `priority`           INT          DEFAULT 3 COMMENT '风险等级 1=重大风险 2=较大风险 3=一般风险 4=低风险',
    `risk`               DOUBLE       DEFAULT 0.3 COMMENT '风险值 0~1',
    `type`               VARCHAR(20)  DEFAULT 'gas' COMMENT '传感器类型',
    `mode`               VARCHAR(10)  DEFAULT 'auto' COMMENT '数据模式 auto/manual',
    `last_sample_time`   BIGINT       DEFAULT NULL COMMENT '最后采样时间戳',
    `created_at`         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器布点表';

-- 传感器布局方案表
-- 存储传感器布局方案，用于保存和切换不同布局
CREATE TABLE IF NOT EXISTS `sensor_layout` (
    `id`                 INT          AUTO_INCREMENT COMMENT '布局方案ID',
    `layout_name`        VARCHAR(100) NOT NULL COMMENT '布局方案名称',
    `description`        VARCHAR(500) DEFAULT '' COMMENT '布局方案描述',
    `sensor_count`       INT          DEFAULT 0 COMMENT '传感器数量',
    `coverage_rate`      DOUBLE       DEFAULT 0 COMMENT '覆盖率 0~1',
    `risk_score`         DOUBLE       DEFAULT 0 COMMENT '风险评分 0~1',
    `status`             VARCHAR(20)  DEFAULT 'draft' COMMENT '状态 draft/active/archived',
    `created_at`         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器布局方案表';

-- 传感器布局详情表
-- 存储布局方案中的传感器配置
CREATE TABLE IF NOT EXISTS `sensor_layout_detail` (
    `id`                 INT          AUTO_INCREMENT COMMENT '记录ID',
    `layout_id`          INT          NOT NULL COMMENT '所属布局方案ID',
    `sensor_id`          VARCHAR(50)  NOT NULL COMMENT '传感器编号',
    `x`                  DOUBLE       NOT NULL COMMENT '地图 X 坐标',
    `y`                  DOUBLE       NOT NULL COMMENT '地图 Y 坐标',
    `installation_height` DOUBLE      DEFAULT 1.5 COMMENT '安装高度 (m)',
    `effective_range`    DOUBLE       DEFAULT 20 COMMENT '有效监测范围 (m)',
    `detection_range`    VARCHAR(200) DEFAULT 'CO / CH4 / NH3 / O2' COMMENT '检测气体范围',
    `priority`           INT          DEFAULT 3 COMMENT '风险等级 1=重大风险 2=较大风险 3=一般风险 4=低风险',
    `risk`               DOUBLE       DEFAULT 0.3 COMMENT '风险值 0~1',
    `created_at`         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    FOREIGN KEY (`layout_id`) REFERENCES `sensor_layout`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器布局方案详情表';
