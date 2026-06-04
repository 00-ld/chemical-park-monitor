package com.at.controller;

import com.at.pojo.Result;
import com.at.pojo.Sensor;
import com.at.service.SensorService;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/sensor")
public class SensorController {

    @Resource
    private SensorService sensorService;

    @GetMapping("/list")
    public ResponseEntity<Result> getAllSensors() {
        try {
            List<Sensor> list = sensorService.getAllSensors();
            log.info("查询所有传感器, 数量: {}", list.size());
            return ResponseEntity.ok(Result.success(list));
        } catch (Exception e) {
            log.error("查询传感器失败", e);
            return ResponseEntity.internalServerError().body(Result.error("查询失败：" + e.getMessage()));
        }
    }

    @PostMapping("/add")
    public ResponseEntity<Result> addSensor(@RequestBody Sensor sensor) {
        try {
            if (sensor.getId() == null || sensor.getId().isEmpty()) {
                return ResponseEntity.badRequest().body(Result.error("传感器ID不能为空"));
            }
            boolean success = sensorService.addSensor(sensor);
            if (success) {
                log.info("新增传感器成功: id={}", sensor.getId());
                return ResponseEntity.ok(Result.success("传感器已保存"));
            } else {
                return ResponseEntity.internalServerError().body(Result.error("保存失败"));
            }
        } catch (Exception e) {
            log.error("新增传感器异常", e);
            return ResponseEntity.internalServerError().body(Result.error("系统异常：" + e.getMessage()));
        }
    }

    @PostMapping("/update")
    public ResponseEntity<Result> updateSensor(@RequestBody Sensor sensor) {
        try {
            if (sensor.getId() == null || sensor.getId().isEmpty()) {
                return ResponseEntity.badRequest().body(Result.error("传感器ID不能为空"));
            }
            boolean success = sensorService.updateSensor(sensor);
            if (success) {
                log.info("更新传感器成功: id={}", sensor.getId());
                return ResponseEntity.ok(Result.success("传感器已更新"));
            } else {
                return ResponseEntity.internalServerError().body(Result.error("更新失败"));
            }
        } catch (Exception e) {
            log.error("更新传感器异常", e);
            return ResponseEntity.internalServerError().body(Result.error("系统异常：" + e.getMessage()));
        }
    }

    @PostMapping("/delete")
    public ResponseEntity<Result> deleteSensor(@RequestBody Map<String, String> param) {
        try {
            String id = param.get("id");
            if (id == null || id.isEmpty()) {
                return ResponseEntity.badRequest().body(Result.error("传感器ID不能为空"));
            }
            boolean success = sensorService.deleteSensor(id);
            if (success) {
                log.info("删除传感器成功: id={}", id);
                return ResponseEntity.ok(Result.success("传感器已删除"));
            } else {
                return ResponseEntity.internalServerError().body(Result.error("删除失败，未找到该传感器"));
            }
        } catch (Exception e) {
            log.error("删除传感器异常", e);
            return ResponseEntity.internalServerError().body(Result.error("系统异常：" + e.getMessage()));
        }
    }
}
