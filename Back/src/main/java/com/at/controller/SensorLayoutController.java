package com.at.controller;

import com.at.pojo.Result;
import com.at.pojo.SensorLayout;
import com.at.pojo.SensorLayoutDetail;
import com.at.service.SensorLayoutService;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/sensor-layout")
@CrossOrigin
public class SensorLayoutController {

    @Resource
    private SensorLayoutService sensorLayoutService;

    @GetMapping("/list")
    public ResponseEntity<Result> getAllLayouts() {
        try {
            List<SensorLayout> list = sensorLayoutService.getAllLayouts();
            log.info("查询所有布局方案, 数量: {}", list.size());
            return ResponseEntity.ok(Result.success(list));
        } catch (Exception e) {
            log.error("查询布局方案失败", e);
            return ResponseEntity.internalServerError().body(Result.error("查询失败：" + e.getMessage()));
        }
    }

    @GetMapping("/{id}")
    public ResponseEntity<Result> getLayoutById(@PathVariable Integer id) {
        try {
            SensorLayout layout = sensorLayoutService.getLayoutById(id);
            if (layout == null) {
                return ResponseEntity.badRequest().body(Result.error("布局方案不存在"));
            }
            List<SensorLayoutDetail> details = sensorLayoutService.getLayoutDetails(id);
            Map<String, Object> result = Map.of("layout", layout, "details", details);
            return ResponseEntity.ok(Result.success(result));
        } catch (Exception e) {
            log.error("查询布局方案失败", e);
            return ResponseEntity.internalServerError().body(Result.error("查询失败：" + e.getMessage()));
        }
    }

    @PostMapping("/save")
    public ResponseEntity<Result> saveLayout(@RequestBody Map<String, Object> param) {
        try {
            SensorLayout layout = new SensorLayout();
            layout.setLayoutName((String) param.get("layoutName"));
            layout.setDescription((String) param.getOrDefault("description", ""));
            layout.setCoverageRate((Double) param.getOrDefault("coverageRate", 0.0));
            layout.setRiskScore((Double) param.getOrDefault("riskScore", 0.0));

            @SuppressWarnings("unchecked")
            List<Map<String, Object>> detailMaps = (List<Map<String, Object>>) param.get("details");
            List<SensorLayoutDetail> details = detailMaps.stream().map(m -> {
                SensorLayoutDetail d = new SensorLayoutDetail();
                d.setSensorId((String) m.get("sensorId"));
                d.setX((Double) m.get("x"));
                d.setY((Double) m.get("y"));
                d.setInstallationHeight((Double) m.getOrDefault("installationHeight", 1.5));
                d.setEffectiveRange((Double) m.getOrDefault("effectiveRange", 20.0));
                d.setDetectionRange((String) m.getOrDefault("detectionRange", "CO / 可燃气体 / H2S / O2"));
                d.setPriority((Integer) m.getOrDefault("priority", 2));
                d.setRisk((Double) m.getOrDefault("risk", 0.3));
                return d;
            }).toList();

            Integer layoutId = sensorLayoutService.saveLayout(layout, details);
            log.info("保存布局方案成功: id={}", layoutId);
            return ResponseEntity.ok(Result.success(Map.of("id", layoutId)));
        } catch (Exception e) {
            log.error("保存布局方案异常", e);
            return ResponseEntity.internalServerError().body(Result.error("保存失败：" + e.getMessage()));
        }
    }

    @PostMapping("/delete/{id}")
    public ResponseEntity<Result> deleteLayout(@PathVariable Integer id) {
        try {
            sensorLayoutService.deleteLayout(id);
            log.info("删除布局方案成功: id={}", id);
            return ResponseEntity.ok(Result.success("布局方案已删除"));
        } catch (Exception e) {
            log.error("删除布局方案异常", e);
            return ResponseEntity.internalServerError().body(Result.error("删除失败：" + e.getMessage()));
        }
    }
}
