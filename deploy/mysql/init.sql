-- ========================================
-- 化工园区智能监测系统 - 数据库初始化
-- ========================================

CREATE DATABASE IF NOT EXISTS `chemical` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `chemical`;

SET NAMES utf8mb4;

-- 1. 气体传感器基础信息表
CREATE TABLE IF NOT EXISTS `gas` (
    `id`                  VARCHAR(50)  NOT NULL COMMENT '气体编号 (如 CO, H2S, CH4, O2)',
    `name`                VARCHAR(100) NOT NULL COMMENT '气体名称',
    `detection_range`     VARCHAR(200) DEFAULT NULL COMMENT '检测气体范围',
    `installation_height` DOUBLE       DEFAULT 1.5 COMMENT '安装高度 (m)',
    `effective_range`     DOUBLE       DEFAULT 20 COMMENT '有效监测范围 (m)',
    `install_remark`      VARCHAR(500) DEFAULT NULL COMMENT '布点说明 / 备注',
    `priority`            INT          DEFAULT 3 COMMENT '风险等级 1=重大风险 2=较大风险 3=一般风险 4=低风险',
    `risk`                DOUBLE       DEFAULT 0.3 COMMENT '风险值 0~1',
    `type`                VARCHAR(20)  DEFAULT 'gas' COMMENT '传感器类型',
    `mode`                VARCHAR(10)  DEFAULT 'auto' COMMENT '数据模式 auto/manual',
    `created_at`          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='气体传感器基础信息表';

-- 初始数据：四气传感器
INSERT IGNORE INTO `gas` (`id`, `name`, `detection_range`, `installation_height`, `effective_range`, `install_remark`, `priority`, `risk`) VALUES
('CO', '一氧化碳', '0-1000ppm', 1.5, 15, '高毒气体', 1, 0.90),
('H2S', '硫化氢', '0-100ppm', 0.5, 12, '剧毒气体', 1, 0.95),
('CH4', '甲烷', '0-100%LEL', 2.0, 18, '可燃气体', 2, 0.80),
('O2', '氧气', '0-30%VOL', 1.5, 15, '缺氧监测', 2, 0.30);

-- 2. 传感器布点表
CREATE TABLE IF NOT EXISTS `sensor` (
    `id`                 VARCHAR(50)  NOT NULL COMMENT '传感器工程编号 (如 TK-01)',
    `x`                  DOUBLE       NOT NULL COMMENT '地图 X 坐标',
    `y`                  DOUBLE       NOT NULL COMMENT '地图 Y 坐标',
    `installation_height` DOUBLE      DEFAULT 1.5 COMMENT '安装高度 (m)',
    `effective_range`    DOUBLE       DEFAULT 20 COMMENT '有效监测范围 (m)',
    `detection_range`    VARCHAR(200) DEFAULT 'CO / 可燃气体 / H2S / O2' COMMENT '检测气体范围',
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

-- 3. 传感器布局方案表
CREATE TABLE IF NOT EXISTS `sensor_layout` (
    `id`                 INT          AUTO_INCREMENT COMMENT '布局方案ID',
    `layout_name`        VARCHAR(100) NOT NULL COMMENT '布局方案名称',
    `description`        VARCHAR(500) DEFAULT NULL COMMENT '布局方案描述',
    `sensor_count`       INT          DEFAULT 0 COMMENT '传感器数量',
    `coverage_rate`      DOUBLE       DEFAULT 0 COMMENT '覆盖率 0~1',
    `risk_score`         DOUBLE       DEFAULT 0 COMMENT '风险评分 0~1',
    `status`             VARCHAR(20)  DEFAULT 'draft' COMMENT '状态 draft/active/archived',
    `created_at`         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器布局方案表';

-- 4. 传感器布局详情表
CREATE TABLE IF NOT EXISTS `sensor_layout_detail` (
    `id`                 INT          AUTO_INCREMENT COMMENT '记录ID',
    `layout_id`          INT          NOT NULL COMMENT '所属布局方案ID',
    `sensor_id`          VARCHAR(50)  NOT NULL COMMENT '传感器编号',
    `x`                  DOUBLE       NOT NULL COMMENT '地图 X 坐标',
    `y`                  DOUBLE       NOT NULL COMMENT '地图 Y 坐标',
    `installation_height` DOUBLE      DEFAULT 1.5 COMMENT '安装高度 (m)',
    `effective_range`    DOUBLE       DEFAULT 20 COMMENT '有效监测范围 (m)',
    `detection_range`    VARCHAR(200) DEFAULT NULL COMMENT '检测气体范围',
    `priority`           INT          DEFAULT 3 COMMENT '风险等级 1=重大风险 2=较大风险 3=一般风险 4=低风险',
    `risk`               DOUBLE       DEFAULT 0.3 COMMENT '风险值 0~1',
    `created_at`         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    FOREIGN KEY (`layout_id`) REFERENCES `sensor_layout`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器布局方案详情表';


-- ========================================
-- 传感器布点数据 (179个, 基于GB/T 50493-2019)
-- ========================================

-- 传感器布点数据 - 基于GB/T 50493-2019国标方案
-- 共179个传感器，覆盖14个区域

INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-01L', 170.0, 253.0, 0.5, 8.0, 'CO/可燃气体/H₂S/O2', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-01H', 170.0, 253.0, 2.2, 5.0, 'NH3/CO/可燃气体/O2', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-02L', 110.0, 253.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-02H', 110.0, 253.0, 2.2, 5.0, 'NH3/CO/可燃气体/O2', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-03L', 245.0, 253.0, 0.5, 6.0, 'CO/可燃气体/H2S/O2', 1, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-03H', 245.0, 253.0, 2.2, 5.0, 'NH3/CO/可燃气体/O2', 1, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-04L', 240.0, 253.0, 0.5, 6.0, 'CO/可燃气体/H2S/O2', 1, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-04H', 240.0, 253.0, 2.2, 5.0, 'NH3/CO/可燃气体/O2', 1, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-05L', 260.0, 253.0, 0.5, 6.0, 'CO/可燃气体/H2S/O2', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-05H', 260.0, 253.0, 2.2, 5.0, 'NH3/CO/可燃气体/O2', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-06L', 310.0, 253.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 2, 0.55, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-06H', 310.0, 253.0, 2.2, 5.0, 'NH3/CO/可燃气体/O2', 2, 0.55, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-E01', 170.0, 129.0, 1.5, 15.0, 'CO/可燃气体/H2S/O2', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-E02', 155.0, 191.0, 1.5, 15.0, 'CO/可燃气体/H2S/O2', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-E03', 245.0, 99.0, 1.5, 15.0, '可燃气体/CO/H2S/O2', 1, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('A-E04', 240.0, 186.0, 1.5, 15.0, 'CO/可燃气体/H2S/O2', 1, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-01L', 378.0, 175.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-02L', 378.0, 140.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-03L', 420.0, 157.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-04L', 462.0, 140.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-05L', 462.0, 175.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-06H', 420.0, 133.0, 2.2, 5.0, 'CH4/C2H4/CO/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-07H', 378.0, 65.0, 2.2, 5.0, 'C2H4/C3H6/CO/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-08H', 435.0, 82.0, 2.2, 5.0, 'C2H4/C3H6/CO/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-09H', 492.0, 65.0, 2.2, 5.0, 'C2H4/C3H6/CO/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-10L', 385.0, 117.0, 0.5, 8.0, 'CO/可燃气体/O2', 1, 0.8, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-11L', 498.0, 72.0, 0.5, 8.0, 'CO/可燃气体/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-12L', 498.0, 106.0, 0.5, 8.0, 'CO/可燃气体/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-13H', 517.0, 70.0, 2.2, 5.0, 'CO/可燃气体/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-14L', 547.0, 108.0, 0.5, 8.0, 'CO/可燃气体/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-15L', 567.0, 82.0, 0.5, 8.0, 'CO/可燃气体/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-16L', 587.0, 82.0, 0.5, 8.0, 'CO/可燃气体/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-17L', 610.0, 82.0, 0.5, 8.0, 'CO/可燃气体/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-E01', 517.0, 128.0, 1.5, 15.0, 'CO/可燃气体/H2S/O2', 1, 0.8, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-E02', 517.0, 166.0, 1.5, 15.0, 'CO/可燃气体/H2S/O2', 1, 0.8, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PA-E03', 498.0, 129.0, 1.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-01L', 678.0, 143.0, 0.5, 8.0, 'CH4/CO/可燃气体', 1, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-02L', 737.0, 162.0, 0.5, 8.0, 'CH4/CO/可燃气体', 1, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-03L', 773.0, 143.0, 0.5, 8.0, 'CH4/CO/可燃气体', 1, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-03H', 773.0, 143.0, 2.2, 8.0, 'CH4/CO/可燃气体', 1, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-04L', 678.0, 73.0, 0.5, 8.0, 'CH4/CO/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-05L', 752.0, 95.0, 0.5, 8.0, 'CH4/CO/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-06L', 798.0, 73.0, 0.5, 8.0, 'CH4/CO/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-06H', 752.0, 73.0, 2.2, 8.0, 'CH4/CO/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-07L', 808.0, 78.0, 0.5, 8.0, 'CH4/CO/可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-08L', 840.0, 95.0, 0.5, 8.0, 'CH4/CO/可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-09L', 868.0, 78.0, 0.5, 8.0, 'CH4/CO/可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-10L', 808.0, 138.0, 0.5, 4.0, 'H2S/CO/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-11L', 840.0, 152.0, 0.5, 4.0, 'H2S/CO/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-12L', 868.0, 138.0, 0.5, 4.0, 'H2S/CO/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-13', 840.0, 133.0, 1.5, 8.0, 'CO/可燃气体', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PB-13H', 840.0, 138.0, 2.2, 8.0, 'CH4/CO/可燃气体', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-01H', 740.0, 280.0, 2.0, 10.0, 'CH4', 1, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-02L', 755.0, 290.0, 0.5, 5.0, 'H2S', 1, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-E01H', 699.0, 270.0, 2.2, 10.0, 'CH4', 2, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-E02H', 791.0, 282.0, 2.2, 10.0, 'CH4', 2, 0.65, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-03H', 855.0, 280.0, 2.2, 10.0, 'CH4', 1, 0.55, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-04', 865.0, 290.0, 1.5, 15.0, 'CO', 2, 0.55, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-E03H', 819.0, 270.0, 2.2, 10.0, 'CH4', 2, 0.55, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-E04H', 901.0, 270.0, 2.2, 10.0, 'CH4', 2, 0.55, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-05H', 735.0, 358.0, 2.2, 10.0, 'CH4', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-06', 745.0, 368.0, 1.5, 15.0, 'CO', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-E05H', 699.0, 355.0, 2.2, 10.0, 'CH4', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-07', 855.0, 358.0, 1.5, 15.0, 'CO', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('P2-E06', 819.0, 355.0, 1.5, 15.0, 'CO', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-01L', 80.0, 275.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-02L', 120.0, 325.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.9, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-03L', 170.0, 262.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 2, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-04L', 192.0, 312.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-05L', 266.0, 274.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-06L', 240.0, 334.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 2, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-07L', 122.0, 362.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 2, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-08L', 79.0, 401.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 2, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-09L', 191.0, 364.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 2, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-10L', 170.0, 410.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 2, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-11L', 259.0, 361.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-12L', 240.0, 404.0, 0.5, 8.0, 'CO/可燃气体/H2S/O2', 2, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-13H', 320.0, 310.0, 2.2, 5.0, 'NH3/CO/可燃气体/O2', 1, 0.95, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-14H', 300.0, 287.0, 2.2, 5.0, 'NH3/CO/可燃气体/O2', 1, 0.95, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-15H', 300.0, 332.0, 2.2, 5.0, 'NH3/CO/可燃气体/O2', 1, 0.95, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-16H', 280.0, 310.0, 2.2, 5.0, 'NH3/CO/可燃气体/O2', 1, 0.95, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-17L', 354.0, 375.0, 0.3, 6.0, 'H2S/可燃气体/CO/O2', 1, 0.95, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-18L', 300.0, 352.0, 0.3, 5.0, 'H2S/CO/可燃气体/O2', 1, 0.95, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TK-19L', 300.0, 408.0, 0.3, 5.0, 'H2S/CO/可燃气体/O2', 1, 0.95, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-01L', 448.0, 268.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-02L', 482.0, 292.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-03H', 470.0, 278.0, 3.2, 10.0, 'CH4/CO/可燃气体', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-04L', 509.0, 301.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-05L', 531.0, 279.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-06H', 520.0, 288.0, 3.3, 10.0, 'CH4/CO/可燃气体', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-07L', 559.0, 291.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 1, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-08H', 570.0, 278.0, 3.1, 10.0, 'CH4/CO/可燃气体', 1, 0.7, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-09L', 448.0, 383.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 1, 0.8, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-10L', 483.0, 357.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 1, 0.8, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-11', 486.0, 370.0, 1.5, 10.0, 'CH4/CO/H2S/可燃气体', 1, 0.8, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-12H', 470.0, 368.0, 3.5, 10.0, 'CH4/CO/可燃气体', 1, 0.8, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-13L', 520.0, 365.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-14L', 540.0, 385.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-15', 542.0, 375.0, 1.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-16H', 530.0, 373.0, 3.4, 10.0, 'CH4/CO/可燃气体', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-17L', 569.0, 354.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-18H', 580.0, 363.0, 3.2, 10.0, 'CH4/CO/可燃气体', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-19L', 630.0, 290.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.55, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-20H', 640.0, 278.0, 3.0, 10.0, 'CH4/CO/可燃气体', 2, 0.55, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-21L', 631.0, 361.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-22H', 640.0, 368.0, 2.8, 10.0, 'CH4/CO/可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-23', 440.0, 400.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('TW-24', 660.0, 255.0, 0.5, 10.0, 'CH4/CO/H2S/可燃气体', 2, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-01H', 440.0, 465.0, 2.2, 8.0, 'CH4', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-02H', 465.0, 470.0, 2.2, 8.0, 'CH4', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-03H', 485.0, 470.0, 2.2, 8.0, 'CH4', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-04H', 465.0, 455.0, 2.2, 8.0, 'CH4', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-05L', 445.0, 525.0, 0.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-06L', 465.0, 525.0, 0.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-07L', 445.0, 515.0, 0.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-08', 520.0, 520.0, 1.5, 8.0, 'O2', 2, 0.45, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-09', 540.0, 525.0, 1.5, 8.0, 'O2', 2, 0.45, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-10L', 588.0, 520.0, 0.5, 10.0, 'CH4/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-11L', 600.0, 520.0, 0.5, 10.0, 'CH4/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-12L', 600.0, 525.0, 0.5, 10.0, 'CH4/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-13L', 600.0, 542.0, 0.5, 10.0, 'CH4/可燃气体', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-14L', 535.0, 470.0, 0.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-15L', 555.0, 470.0, 0.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-16L', 600.0, 458.0, 0.5, 8.0, 'H2S', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('UT-17L', 630.0, 475.0, 0.5, 8.0, 'H2S', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-01H', 715.0, 455.0, 2.2, 10.0, 'CH4', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-02H', 715.0, 495.0, 2.2, 10.0, 'CH4', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-03H', 800.0, 455.0, 2.2, 10.0, 'CH4', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-04H', 800.0, 495.0, 2.2, 10.0, 'CH4', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-05H', 757.0, 455.0, 2.5, 10.0, 'CH4', 1, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-06', 815.0, 523.0, 1.5, 4.0, 'CO', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-07', 815.0, 553.0, 1.5, 4.0, 'CO', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-08', 865.0, 523.0, 1.5, 4.0, 'CO', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-09', 865.0, 553.0, 1.5, 4.0, 'CO', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-10', 815.0, 538.0, 1.5, 4.0, 'CO', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-11', 715.0, 513.0, 1.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-12', 780.0, 548.0, 1.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-13', 815.0, 455.0, 1.5, 8.0, '可燃气体', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-14', 890.0, 500.0, 1.5, 8.0, '可燃气体', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-15', 895.0, 475.0, 1.5, 8.0, '可燃气体', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WH-16', 920.0, 520.0, 1.5, 8.0, '可燃气体', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-01L', 78.0, 508.0, 0.5, 8.0, 'H2S', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-02L', 120.0, 508.0, 0.5, 8.0, 'H2S', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-03L', 162.0, 508.0, 0.5, 8.0, 'H2S', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-04L', 162.0, 547.0, 0.5, 8.0, 'H2S', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-05L', 78.0, 547.0, 0.5, 8.0, 'H2S', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-06L', 178.0, 503.0, 0.5, 8.0, 'H2S', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-07L', 225.0, 503.0, 0.5, 8.0, 'H2S', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-08L', 272.0, 503.0, 0.5, 8.0, 'H2S', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-09L', 272.0, 547.0, 0.5, 8.0, 'H2S', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-10L', 178.0, 547.0, 0.5, 8.0, 'H2S', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-11L', 178.0, 525.0, 0.5, 8.0, 'H2S', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-12L', 185.0, 570.0, 0.5, 5.0, 'H2S', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-13L', 207.0, 580.0, 0.5, 5.0, 'H2S', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-14L', 215.0, 575.0, 0.5, 5.0, 'H2S', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-15L', 230.0, 590.0, 0.5, 5.0, 'H2S', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-12H', 185.0, 570.0, 2.2, 5.0, 'CH4/NH3', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-15H', 230.0, 590.0, 2.2, 5.0, 'CH4/NH3', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-16L', 78.0, 585.0, 0.5, 8.0, 'H2S', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-17L', 115.0, 585.0, 0.5, 8.0, 'H2S', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('WT-18L', 152.0, 585.0, 0.5, 8.0, 'H2S', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('MN-01', 305.0, 578.0, 1.5, 15.0, 'CO/可燃气体/H2S/NH3', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('MN-02', 485.0, 578.0, 1.5, 15.0, 'CO/可燃气体/H2S/NH3', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('MN-03', 665.0, 578.0, 1.5, 15.0, 'CO/可燃气体/H2S/NH3', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('MN-04', 748.0, 573.0, 1.5, 15.0, 'CO/可燃气体/H2S/NH3', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('MN-05', 785.0, 585.0, 1.5, 15.0, 'CO/可燃气体/H2S/NH3', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('MN-06', 822.0, 573.0, 1.5, 15.0, 'CO/可燃气体/H2S/NH3', 2, 0.3, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('MT-01L', 738.0, 207.0, 0.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('MT-02', 777.0, 188.0, 1.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('MT-03L', 817.0, 207.0, 0.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('FS-01L', 354.0, 465.0, 0.5, 8.0, '可燃气体', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('FS-02L', 380.0, 493.0, 0.5, 8.0, '可燃气体', 1, 0.5, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('FS-03', 412.0, 465.0, 1.5, 8.0, '可燃气体', 2, 0.4, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('FD-01L', 354.0, 342.0, 0.5, 15.0, 'CO/可燃气体/H2S/O2', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('FD-02L', 55.0, 340.0, 0.5, 15.0, 'CO/可燃气体/H2S/O2', 2, 0.6, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PL-01L', 100.0, 330.0, 0.5, 8.0, 'CO/可燃气体/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PL-02L', 170.0, 316.0, 0.5, 8.0, 'CO/可燃气体/O2', 1, 0.85, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PL-03L', 270.0, 300.0, 0.5, 8.0, 'CO/可燃气体/O2', 1, 0.8, 'gas', 'auto');
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, priority, risk, type, mode) VALUES ('PL-04L', 240.0, 382.0, 0.5, 8.0, 'CO/可燃气体/O2', 2, 0.7, 'gas', 'auto');