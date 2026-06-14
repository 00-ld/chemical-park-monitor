-- 化工园区监测系统数据库初始化脚本。
-- 默认开发账号：admin / 123456

CREATE DATABASE IF NOT EXISTS `chemical` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `chemical`;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `user` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `username` VARCHAR(64) NOT NULL,
    `password` VARCHAR(100) NOT NULL,
    `role` VARCHAR(16) NOT NULL DEFAULT 'user',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

SET @add_user_role_column = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE `user` ADD COLUMN `role` VARCHAR(16) NOT NULL DEFAULT ''user'' COMMENT ''角色：admin 可写，user 只读''',
        'SELECT 1'
    )
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'user'
      AND COLUMN_NAME = 'role'
);
PREPARE add_user_role_column_stmt FROM @add_user_role_column;
EXECUTE add_user_role_column_stmt;
DEALLOCATE PREPARE add_user_role_column_stmt;

INSERT INTO `user` (`username`, `password`, `role`, `create_time`)
SELECT 'admin', '$2a$10$AaE3RNDY/XTzY13C5ArD5OvS0KXTIjv4vxOBrY.s5XjYs/lWQAPl.', 'admin', NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM `user` WHERE `username` = 'admin'
);

UPDATE `user`
SET `password` = '$2a$10$AaE3RNDY/XTzY13C5ArD5OvS0KXTIjv4vxOBrY.s5XjYs/lWQAPl.',
    `role` = 'admin'
WHERE `username` = 'admin';

DELETE duplicate_user
FROM `user` duplicate_user
JOIN `user` keep_user
  ON duplicate_user.`username` = keep_user.`username`
 AND duplicate_user.`id` > keep_user.`id`;

SET @add_user_username_unique = (
    SELECT IF(
        COUNT(*) = 0,
        'ALTER TABLE `user` ADD UNIQUE KEY `uk_user_username` (`username`)',
        'SELECT 1'
    )
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'user'
      AND INDEX_NAME = 'uk_user_username'
);
PREPARE add_user_username_unique_stmt FROM @add_user_username_unique;
EXECUTE add_user_username_unique_stmt;
DEALLOCATE PREPARE add_user_username_unique_stmt;

CREATE TABLE IF NOT EXISTS `gas` (
    `id` VARCHAR(50) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `detection_range` VARCHAR(200) DEFAULT NULL,
    `installation_height` DOUBLE DEFAULT 1.5,
    `effective_range` DOUBLE DEFAULT 20,
    `install_remark` VARCHAR(500) DEFAULT NULL,
    `priority` INT DEFAULT 3,
    `risk` DOUBLE DEFAULT 0.3,
    `type` VARCHAR(20) DEFAULT 'gas',
    `mode` VARCHAR(10) DEFAULT 'auto',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='气体类型配置表';

INSERT INTO `gas` (`id`, `name`, `detection_range`, `installation_height`, `effective_range`, `install_remark`, `priority`, `risk`, `type`, `mode`) VALUES
('CO', '一氧化碳', '0-1000ppm', 1.5, 15, '有毒气体监测', 1, 0.90, 'gas', 'auto'),
('NH3', '氨气', '0-100ppm', 1.5, 20, '有毒气体监测', 1, 0.90, 'gas', 'auto'),
('CH4', '甲烷', '0-100%LEL', 2.0, 18, '可燃气体监测', 2, 0.80, 'gas', 'auto'),
('O2', '氧气', '0-30%VOL', 1.5, 15, '氧气浓度监测', 2, 0.30, 'gas', 'auto')
ON DUPLICATE KEY UPDATE
    `name` = VALUES(`name`),
    `detection_range` = VALUES(`detection_range`),
    `installation_height` = VALUES(`installation_height`),
    `effective_range` = VALUES(`effective_range`),
    `install_remark` = VALUES(`install_remark`),
    `priority` = VALUES(`priority`),
    `risk` = VALUES(`risk`),
    `type` = VALUES(`type`),
    `mode` = VALUES(`mode`);

CREATE TABLE IF NOT EXISTS `leida` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `car_id` INT NOT NULL,
    `warning` TINYINT NOT NULL DEFAULT 0,
    `x` INT NOT NULL,
    `y` INT NOT NULL,
    `gas_type` VARCHAR(20) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_leida_car_id` (`car_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='巡检小车实时位置与气体类型表';

-- 小车坐标基于真实 DOM 二维地图米制坐标，限制在 1587.2m x 947.2m 数据边界内。
-- 1: 西南储罐泵区；2: 中南反应装置区；3: 中东塔器/公用工程区；4: 东南应急装卸区。
INSERT INTO `leida` (`car_id`, `warning`, `x`, `y`, `gas_type`) VALUES
(1, 0, 450, 565, 'CH4'),
(2, 0, 690, 500, 'NH3'),
(3, 0, 925, 430, 'CO'),
(4, 0, 1125, 610, 'O2')
ON DUPLICATE KEY UPDATE
    `x` = VALUES(`x`),
    `y` = VALUES(`y`),
    `gas_type` = VALUES(`gas_type`);

CREATE TABLE IF NOT EXISTS `sensor` (
    `id` VARCHAR(50) NOT NULL,
    `x` DOUBLE NOT NULL,
    `y` DOUBLE NOT NULL,
    `installation_height` DOUBLE DEFAULT 1.5,
    `effective_range` DOUBLE DEFAULT 20,
    `detection_range` VARCHAR(200) DEFAULT 'CO / CH4 / NH3 / O2',
    `install_remark` VARCHAR(500) DEFAULT '',
    `priority` INT DEFAULT 3,
    `risk` DOUBLE DEFAULT 0.3,
    `type` VARCHAR(20) DEFAULT 'gas',
    `mode` VARCHAR(10) DEFAULT 'auto',
    `last_sample_time` BIGINT DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器布点表';

CREATE TABLE IF NOT EXISTS `sensor_layout` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `layout_name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(500) DEFAULT NULL,
    `sensor_count` INT DEFAULT 0,
    `coverage_rate` DOUBLE DEFAULT 0,
    `risk_score` DOUBLE DEFAULT 0,
    `status` VARCHAR(20) DEFAULT 'draft',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器布点方案表';

CREATE TABLE IF NOT EXISTS `sensor_layout_detail` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `layout_id` INT NOT NULL,
    `sensor_id` VARCHAR(50) NOT NULL,
    `x` DOUBLE NOT NULL,
    `y` DOUBLE NOT NULL,
    `installation_height` DOUBLE DEFAULT 1.5,
    `effective_range` DOUBLE DEFAULT 20,
    `detection_range` VARCHAR(200) DEFAULT NULL,
    `priority` INT DEFAULT 3,
    `risk` DOUBLE DEFAULT 0.3,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_sensor_layout_detail_layout` (`layout_id`),
    CONSTRAINT `fk_sensor_layout_detail_layout`
        FOREIGN KEY (`layout_id`) REFERENCES `sensor_layout`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Sensor layout plan detail';

-- 真实 DOM 二维地图传感器布点种子数据。
-- 源地图：D:/BaiduNetdiskDownload/三维模型/ResultDOM_2.tiff
-- 源分辨率：0.05 m/pixel；前端资源：frontend/public/maps/real-park-dom.jpg。
-- 坐标为真实地图米制坐标，严格限制在 1587.2m x 947.2m 数据边界内。
-- 布点依据：GB/T 50493-2019。CO/CH4/NH3/O2 混合点按有毒气体 4m 水平覆盖半径控制；
-- 仓储区和应急边界点使用 8m 覆盖半径。


-- 重建真实 DOM 点位集，避免旧版 canvas 假点位继续混入数据库。
DELETE FROM sensor;

INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-01L', 272.0, 286.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(272.0m,286.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.86, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-01H', 272.0, 286.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：生产装置区；点位坐标(272.0m,286.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 1, 0.86, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-02L', 336.0, 332.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(336.0m,332.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.84, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-03L', 420.0, 354.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(420.0m,354.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.82, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-03H', 420.0, 354.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：生产装置区；点位坐标(420.0m,354.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 1, 0.82, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-04L', 510.0, 304.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(510.0m,304.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.80, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-05L', 548.0, 398.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(548.0m,398.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.78, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-05H', 548.0, 398.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：生产装置区；点位坐标(548.0m,398.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 1, 0.78, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TK-01L', 276.0, 456.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：储罐与泵区；点位坐标(276.0m,456.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.90, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TK-02L', 346.0, 500.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：储罐与泵区；点位坐标(346.0m,500.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.90, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TK-02H', 346.0, 500.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：储罐与泵区；点位坐标(346.0m,500.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 1, 0.88, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TK-03L', 430.0, 470.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：储罐与泵区；点位坐标(430.0m,470.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.86, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TK-04L', 520.0, 510.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：储罐与泵区；点位坐标(520.0m,510.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.84, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TK-05L', 292.0, 598.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：储罐与泵区；点位坐标(292.0m,598.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.82, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TK-06L', 372.0, 636.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：储罐与泵区；点位坐标(372.0m,636.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.82, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TK-07L', 470.0, 604.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：储罐与泵区；点位坐标(470.0m,604.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.80, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TK-08L', 558.0, 648.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：储罐与泵区；点位坐标(558.0m,648.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.80, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TK-08H', 558.0, 648.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：储罐与泵区；点位坐标(558.0m,648.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 1, 0.78, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-06L', 612.0, 292.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(612.0m,292.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.70, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-07L', 674.0, 288.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(674.0m,288.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.70, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-08L', 730.0, 366.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(730.0m,366.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.68, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-08H', 730.0, 366.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：生产装置区；点位坐标(730.0m,366.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 2, 0.68, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-09L', 620.0, 456.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(620.0m,456.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.74, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-10L', 704.0, 504.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(704.0m,504.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.74, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-11L', 642.0, 590.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(642.0m,590.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.76, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PA-12L', 736.0, 650.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：生产装置区；点位坐标(736.0m,650.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.68, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('UT-01L', 782.0, 300.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.4.4；真实DOM识别区域：公用工程与管廊区；点位坐标(782.0m,300.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.52, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('UT-01H', 782.0, 300.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：公用工程与管廊区；点位坐标(782.0m,300.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 2, 0.52, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('UT-02L', 826.0, 426.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.4.4；真实DOM识别区域：公用工程与管廊区；点位坐标(826.0m,426.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.50, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('UT-03L', 800.0, 520.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.4.4；真实DOM识别区域：公用工程与管廊区；点位坐标(800.0m,520.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.48, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('UT-04L', 832.0, 628.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.4.4；真实DOM识别区域：公用工程与管廊区；点位坐标(832.0m,628.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.48, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TW-01L', 872.0, 286.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：塔器与罐组区；点位坐标(872.0m,286.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.82, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TW-01H', 872.0, 286.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：塔器与罐组区；点位坐标(872.0m,286.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 1, 0.82, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TW-02L', 920.0, 326.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：塔器与罐组区；点位坐标(920.0m,326.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.82, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TW-03L', 892.0, 410.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：塔器与罐组区；点位坐标(892.0m,410.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.80, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TW-04L', 922.0, 500.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：塔器与罐组区；点位坐标(922.0m,500.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.78, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TW-04H', 922.0, 500.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：塔器与罐组区；点位坐标(922.0m,500.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 1, 0.78, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TW-05L', 880.0, 610.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：塔器与罐组区；点位坐标(880.0m,610.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.76, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('TW-06L', 938.0, 650.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：塔器与罐组区；点位坐标(938.0m,650.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.68, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PB-01L', 982.0, 284.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：东北罐组与管汇区；点位坐标(982.0m,284.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.80, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PB-01H', 982.0, 284.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：东北罐组与管汇区；点位坐标(982.0m,284.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 1, 0.80, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PB-02L', 1030.0, 294.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：东北罐组与管汇区；点位坐标(1030.0m,294.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.82, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PB-03L', 1082.0, 304.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：东北罐组与管汇区；点位坐标(1082.0m,304.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.82, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PB-03H', 1082.0, 304.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：东北罐组与管汇区；点位坐标(1082.0m,304.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 1, 0.82, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PB-04L', 1132.0, 314.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：东北罐组与管汇区；点位坐标(1132.0m,314.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.80, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PB-05L', 1180.0, 344.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：东北罐组与管汇区；点位坐标(1180.0m,344.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 1, 0.78, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PB-06L', 1000.0, 386.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：东北罐组与管汇区；点位坐标(1000.0m,386.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.70, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('PB-07L', 1100.0, 394.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.1；真实DOM识别区域：东北罐组与管汇区；点位坐标(1100.0m,394.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.70, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('P2-01L', 984.0, 456.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：东中生产与污水装置区；点位坐标(984.0m,456.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.64, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('P2-02L', 1060.0, 470.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：东中生产与污水装置区；点位坐标(1060.0m,470.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.62, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('P2-03L', 1150.0, 470.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.2.1；真实DOM识别区域：东中生产与污水装置区；点位坐标(1150.0m,470.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.62, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('P2-03H', 1150.0, 470.0, 2.2, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 6.1.2；真实DOM识别区域：东中生产与污水装置区；点位坐标(1150.0m,470.0m)，安装高度2.2m，覆盖半径4.0m；高位配对点，覆盖轻气上浮或顶部积聚风险', 2, 0.62, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('P2-04L', 990.0, 520.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.4.4；真实DOM识别区域：东中生产与污水装置区；点位坐标(990.0m,520.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.58, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('P2-05L', 1130.0, 520.0, 0.5, 4.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.4.4；真实DOM识别区域：东中生产与污水装置区；点位坐标(1130.0m,520.0m)，安装高度0.5m，覆盖半径4.0m；低位近源点，覆盖有毒/重气贴地扩散风险', 2, 0.58, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('WH-01', 1100.0, 560.0, 1.5, 8.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.4；真实DOM识别区域：仓储物流区；点位坐标(1100.0m,560.0m)，安装高度1.5m，覆盖半径8.0m；边界/装卸通道巡检点，覆盖仓储与应急通道风险', 2, 0.48, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('WH-02', 1160.0, 560.0, 1.5, 8.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.4；真实DOM识别区域：仓储物流区；点位坐标(1160.0m,560.0m)，安装高度1.5m，覆盖半径8.0m；边界/装卸通道巡检点，覆盖仓储与应急通道风险', 2, 0.48, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('WH-03', 1200.0, 592.0, 1.5, 8.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.4；真实DOM识别区域：仓储物流区；点位坐标(1200.0m,592.0m)，安装高度1.5m，覆盖半径8.0m；边界/装卸通道巡检点，覆盖仓储与应急通道风险', 2, 0.46, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('WH-04', 1120.0, 630.0, 1.5, 8.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.4；真实DOM识别区域：仓储物流区；点位坐标(1120.0m,630.0m)，安装高度1.5m，覆盖半径8.0m；边界/装卸通道巡检点，覆盖仓储与应急通道风险', 2, 0.46, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('WH-05', 1180.0, 650.0, 1.5, 8.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.3.4；真实DOM识别区域：仓储物流区；点位坐标(1180.0m,650.0m)，安装高度1.5m，覆盖半径8.0m；边界/装卸通道巡检点，覆盖仓储与应急通道风险', 2, 0.46, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('FS-01', 1000.0, 560.0, 1.5, 8.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.4.3；真实DOM识别区域：东侧应急与装卸边界区；点位坐标(1000.0m,560.0m)，安装高度1.5m，覆盖半径8.0m；边界/装卸通道巡检点，覆盖仓储与应急通道风险', 2, 0.40, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
INSERT INTO sensor (id, x, y, installation_height, effective_range, detection_range, install_remark, priority, risk, type, mode) VALUES ('FS-02', 1040.0, 620.0, 1.5, 8.0, 'CO/CH4/NH3/O2', '依据 GB/T 50493-2019 4.4.3；真实DOM识别区域：东侧应急与装卸边界区；点位坐标(1040.0m,620.0m)，安装高度1.5m，覆盖半径8.0m；边界/装卸通道巡检点，覆盖仓储与应急通道风险', 2, 0.40, 'gas', 'auto') ON DUPLICATE KEY UPDATE x = VALUES(x), y = VALUES(y), installation_height = VALUES(installation_height), effective_range = VALUES(effective_range), detection_range = VALUES(detection_range), install_remark = VALUES(install_remark), priority = VALUES(priority), risk = VALUES(risk), type = VALUES(type), mode = VALUES(mode);
